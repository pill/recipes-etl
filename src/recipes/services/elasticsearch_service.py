"""Elasticsearch service for recipe search indexing."""

import asyncio
import json
from typing import List, Optional, Dict, Any
from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk
from ..config import elasticsearch_config
from ..database import get_pool
from ..models.recipe import Recipe
from ..services.recipe_service import RecipeService


class ElasticsearchService:
    """Service for Elasticsearch operations."""
    
    def __init__(self):
        """Initialize Elasticsearch client."""
        self.client = AsyncElasticsearch(
            [elasticsearch_config.url],
            basic_auth=(elasticsearch_config.username, elasticsearch_config.password) if elasticsearch_config.username else None,
            verify_certs=False
        )
        self.index_name = "recipes"
    
    async def close(self):
        """Close Elasticsearch client."""
        await self.client.close()
    
    async def create_index(self):
        """Create the recipes index with mapping."""
        # Check if index exists
        if await self.client.indices.exists(index=self.index_name):
            print(f"Index '{self.index_name}' already exists")
            return
        
        # Create index with mapping
        mapping = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "recipe_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "stop", "snowball"]
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "id": {"type": "integer"},
                    "uuid": {"type": "keyword"},
                    "title": {
                        "type": "text",
                        "analyzer": "recipe_analyzer",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "description": {
                        "type": "text",
                        "analyzer": "recipe_analyzer"
                    },
                    "instructions": {
                        "type": "text",
                        "analyzer": "recipe_analyzer"
                    },
                    "ingredients": {
                        "type": "nested",
                        "properties": {
                            "name": {
                                "type": "text",
                                "analyzer": "recipe_analyzer",
                                "fields": {
                                    "keyword": {"type": "keyword"}
                                }
                            },
                            "quantity": {"type": "float"},
                            "unit": {"type": "keyword"},
                            "notes": {"type": "text"}
                        }
                    },
                    "prep_time_minutes": {"type": "integer"},
                    "cook_time_minutes": {"type": "integer"},
                    "total_time_minutes": {"type": "integer"},
                    "servings": {"type": "float"},
                    "difficulty": {"type": "keyword"},
                    "cuisine_type": {"type": "keyword"},
                    "meal_type": {"type": "keyword"},
                    "dietary_tags": {"type": "keyword"},
                    "source_url": {"type": "keyword"},
                    "reddit_score": {"type": "integer"},
                    "reddit_author": {"type": "keyword"},
                    "reddit_post_id": {"type": "keyword"},
                    "created_at": {"type": "date"},
                    "embedding": {
                        "type": "dense_vector",
                        "dims": 384,
                        "index": True,
                        "similarity": "cosine"
                    }
                }
            }
        }
        
        await self.client.indices.create(index=self.index_name, body=mapping)
        print(f"✅ Created index '{self.index_name}'")
    
    async def delete_index(self):
        """Delete the recipes index."""
        if await self.client.indices.exists(index=self.index_name):
            await self.client.indices.delete(index=self.index_name)
            print(f"🗑️  Deleted index '{self.index_name}'")
    
    def _is_malformed_recipe(self, recipe: Recipe) -> bool:
        """Check if recipe has malformed data (entire recipe text in one ingredient)."""
        # Check for placeholder instructions
        if recipe.instructions:
            inst_text = " ".join(recipe.instructions) if isinstance(recipe.instructions, list) else str(recipe.instructions)
            if "See full recipe text for instructions" in inst_text:
                return True
        
        # Check for single ingredient with very long name (>100 chars)
        if recipe.ingredients and len(recipe.ingredients) == 1:
            ing = recipe.ingredients[0]
            if ing.ingredient and ing.ingredient.name and len(ing.ingredient.name) > 100:
                return True
        
        # Check for no ingredients at all
        if not recipe.ingredients or len(recipe.ingredients) == 0:
            return True
        
        return False
    
    async def _get_recipe_embedding(self, recipe: Recipe, use_database_cache: bool = True) -> Optional[List[float]]:
        """
        Get embedding for a recipe from database or generate it if missing.
        
        Args:
            recipe: Recipe object
            use_database_cache: If True, try to fetch from database first. If False, always generate.
            
        Returns:
            List of floats representing the embedding vector, or None if generation fails
        """
        try:
            from ..services.embedding_service import get_embedding_service
            embedding_service = get_embedding_service()
        except ImportError:
            print("Warning: sentence-transformers not installed. Skipping embedding generation.")
            return None
        
        # If not using database cache, just generate
        if not use_database_cache:
            try:
                return embedding_service.generate_recipe_embedding(recipe)
            except Exception as e:
                print(f"Warning: Failed to generate embedding for recipe {recipe.id}: {str(e)}")
                return None
        
        # Try to fetch from database first
        pool = await get_pool()
        
        try:
            async with pool.acquire() as conn:
                # Try to fetch embedding from database
                try:
                    query = "SELECT embedding FROM recipes WHERE id = $1"
                    row = await conn.fetchrow(query, recipe.id)
                    
                    if row and row['embedding']:
                        # Parse the vector string from PostgreSQL
                        # pgvector returns as a string like '[0.1,0.2,...]'
                        embedding_str = str(row['embedding'])
                        # Remove brackets and split by comma
                        embedding_str = embedding_str.strip('[]')
                        embedding = [float(x.strip()) for x in embedding_str.split(',') if x.strip()]
                        if len(embedding) == 384:
                            return embedding
                except Exception as db_error:
                    # Database column might not exist, continue to generate
                    pass
                
                # If no embedding in database, generate it
                embedding = embedding_service.generate_recipe_embedding(recipe)
                
                # Try to store it in the database for future use (optional)
                try:
                    embedding_str = '[' + ','.join(str(x) for x in embedding) + ']'
                    await conn.execute(
                        'UPDATE recipes SET embedding = $1::vector WHERE id = $2',
                        embedding_str,
                        recipe.id
                    )
                except Exception as store_error:
                    # If storing fails (e.g., column doesn't exist), that's okay
                    # Just continue without storing
                    pass
                
                return embedding
        except Exception as e:
            print(f"Warning: Failed to get/generate embedding for recipe {recipe.id}: {str(e)}")
            # Fallback: try to generate embedding without storing
            try:
                return embedding_service.generate_recipe_embedding(recipe)
            except Exception as gen_error:
                print(f"Warning: Failed to generate embedding for recipe {recipe.id}: {str(gen_error)}")
                return None
    
    def _recipe_to_document(self, recipe: Recipe, embedding: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        Convert a Recipe model to Elasticsearch document.
        
        Args:
            recipe: Recipe object
            embedding: Optional pre-computed embedding (if None, will be fetched/generated)
        """
        # Skip malformed recipes
        if self._is_malformed_recipe(recipe):
            raise ValueError(f"Malformed recipe data - skipping")
        
        # Extract ingredient data
        ingredients = []
        if recipe.ingredients:
            for ing in recipe.ingredients:
                # Skip if no ingredient name
                if not ing.ingredient or not ing.ingredient.name:
                    continue
                
                # Skip if ingredient name is suspiciously long (>100 chars = likely malformed)
                if len(ing.ingredient.name) > 100:
                    continue
                    
                ingredient_doc = {
                    "name": ing.ingredient.name,
                    "quantity": float(ing.amount) if ing.amount else None,
                    "unit": ing.measurement.name if ing.measurement else None,
                    "notes": ing.notes
                }
                ingredients.append(ingredient_doc)
        
        # Convert instructions to array of strings - handle various formats
        instructions_array = []
        if recipe.instructions:
            if isinstance(recipe.instructions, list):
                # Convert list items to strings
                for inst in recipe.instructions:
                    if isinstance(inst, str):
                        instructions_array.append(inst)
                    elif isinstance(inst, dict):
                        # Handle instruction objects with description
                        instructions_array.append(inst.get('description', str(inst)))
                    else:
                        instructions_array.append(str(inst))
            else:
                # If it's a string, try to parse as JSON first
                try:
                    parsed = json.loads(str(recipe.instructions))
                    if isinstance(parsed, list):
                        instructions_array = [str(x) for x in parsed]
                    else:
                        instructions_array = [str(recipe.instructions)]
                except:
                    instructions_array = [str(recipe.instructions)]
        
        # Build document
        doc = {
            "_id": str(recipe.id),
            "_index": self.index_name,
            "_source": {
                "id": recipe.id,
                "uuid": recipe.uuid,
                "title": recipe.title,
                "description": recipe.description,
                "instructions": instructions_array,
                "ingredients": ingredients,
                "prep_time_minutes": recipe.prep_time_minutes,
                "cook_time_minutes": recipe.cook_time_minutes,
                "total_time_minutes": recipe.total_time_minutes,
                "servings": recipe.servings,
                "difficulty": recipe.difficulty,
                "cuisine_type": recipe.cuisine_type,
                "meal_type": recipe.meal_type,
                "dietary_tags": recipe.dietary_tags,
                "source_url": recipe.source_url,
                "reddit_score": recipe.reddit_score,
                "reddit_author": recipe.reddit_author,
                "reddit_post_id": recipe.reddit_post_id,
                "created_at": recipe.created_at.isoformat() if recipe.created_at else None
            }
        }
        
        # Add embedding if provided
        if embedding:
            doc["_source"]["embedding"] = embedding
        
        return doc
    
    async def index_recipe(self, recipe: Recipe) -> bool:
        """Index a single recipe."""
        try:
            # Get or generate embedding
            embedding = await self._get_recipe_embedding(recipe)
            
            doc = self._recipe_to_document(recipe, embedding=embedding)
            await self.client.index(
                index=self.index_name,
                id=str(recipe.id),
                document=doc["_source"]
            )
            return True
        except Exception as e:
            print(f"Error indexing recipe {recipe.id}: {str(e)}")
            return False
    
    async def bulk_index_recipes(self, recipes: List[Recipe]) -> Dict[str, int]:
        """Bulk index multiple recipes."""
        if not recipes:
            return {"success": 0, "failed": 0, "skipped": 0}
        
        # Prepare documents for bulk indexing
        actions = []
        skipped_count = 0
        
        # Fetch or generate embeddings in batch for efficiency
        try:
            from ..services.embedding_service import get_embedding_service
            embedding_service = get_embedding_service()
            has_embedding_service = True
        except ImportError:
            print("Warning: sentence-transformers not installed. Indexing without embeddings.")
            has_embedding_service = False
            recipe_embeddings = {}
        
        if not has_embedding_service:
            # No embedding service available - index without embeddings
            for recipe in recipes:
                try:
                    doc = self._recipe_to_document(recipe, embedding=None)
                    actions.append(doc)
                except ValueError:
                    skipped_count += 1
                except Exception as e:
                    print(f"Warning: Failed to prepare recipe {recipe.id}: {str(e)}")
            
            # Bulk index without embeddings
            success_count = 0
            failed_count = 0
            if actions:
                try:
                    success, failed = await async_bulk(
                        self.client,
                        actions,
                        raise_on_error=False,
                        raise_on_exception=False
                    )
                    success_count = success
                    failed_count = len(actions) - success
                except Exception as e:
                    print(f"Error during bulk indexing: {str(e)}")
                    failed_count = len(actions)
            
            return {
                "success": success_count,
                "failed": failed_count,
                "skipped": skipped_count
            }
        
        # Has embedding service - fetch or generate embeddings
        recipe_embeddings = {}
        
        # Try to fetch from database first (if column exists)
        try:
            pool = await get_pool()
            async with pool.acquire() as conn:
                recipe_ids = [r.id for r in recipes]
                
                # Fetch existing embeddings from database
                query = "SELECT id, embedding FROM recipes WHERE id = ANY($1)"
                rows = await conn.fetch(query, recipe_ids)
                
                for row in rows:
                    if row['embedding']:
                        try:
                            # Parse the vector string from PostgreSQL
                            embedding_str = str(row['embedding'])
                            embedding_str = embedding_str.strip('[]')
                            embedding = [float(x.strip()) for x in embedding_str.split(',') if x.strip()]
                            if len(embedding) == 384:
                                recipe_embeddings[row['id']] = embedding
                        except Exception as e:
                            # If parsing fails, will generate below
                            pass
        except Exception as e:
            # Database column might not exist, that's okay - we'll generate all
            pass
        
        # Generate embeddings for recipes that don't have them
        recipes_to_embed = [r for r in recipes if r.id not in recipe_embeddings]
        if recipes_to_embed:
            # Generate embeddings in batch
            texts = [embedding_service.build_embedding_text(r) for r in recipes_to_embed]
            generated_embeddings = embedding_service.generate_batch_embeddings(texts, batch_size=32)
            
            # Add to map
            for recipe, embedding in zip(recipes_to_embed, generated_embeddings):
                recipe_embeddings[recipe.id] = embedding
            
            # Optionally store in database (if column exists)
            try:
                pool = await get_pool()
                async with pool.acquire() as conn:
                    for recipe, embedding in zip(recipes_to_embed, generated_embeddings):
                        try:
                            embedding_str = '[' + ','.join(str(x) for x in embedding) + ']'
                            await conn.execute(
                                'UPDATE recipes SET embedding = $1::vector WHERE id = $2',
                                embedding_str,
                                recipe.id
                            )
                        except Exception as e:
                            # Continue even if storing fails (column might not exist)
                            pass
            except Exception as e:
                # Database column might not exist, that's okay
                pass
        
        # Build documents with embeddings
        for recipe in recipes:
            try:
                embedding = recipe_embeddings.get(recipe.id)
                doc = self._recipe_to_document(recipe, embedding=embedding)
                actions.append(doc)
            except ValueError as e:
                # Malformed recipe - skip it
                skipped_count += 1
            except Exception as e:
                print(f"Warning: Failed to prepare recipe {recipe.id} '{recipe.title[:50] if recipe.title else 'No title'}': {str(e)}")
        
        # Bulk index
        success_count = 0
        failed_count = 0
        
        if actions:
            try:
                success, failed = await async_bulk(
                    self.client,
                    actions,
                    raise_on_error=False,
                    raise_on_exception=False
                )
                success_count = success
                failed_count = len(actions) - success
            except Exception as e:
                print(f"Error during bulk indexing: {str(e)}")
                failed_count = len(actions)
        
        return {
            "success": success_count,
            "failed": failed_count,
            "skipped": skipped_count
        }
    
    async def sync_all_from_database(self, batch_size: int = 1000) -> Dict[str, int]:
        """Sync all recipes from database to Elasticsearch."""
        print("🔄 Starting sync from database to Elasticsearch...")
        
        # Get total count
        stats = await RecipeService.get_stats()
        total_recipes = stats.get('total_recipes', 0)
        
        if total_recipes == 0:
            print("📭 No recipes found in database")
            return {"total": 0, "success": 0, "failed": 0}
        
        print(f"📊 Found {total_recipes} recipes to sync")
        
        total_success = 0
        total_failed = 0
        total_skipped = 0
        offset = 0
        show_sample = True  # Show first recipe as sample
        
        while offset < total_recipes:
            print(f"📦 Processing batch {offset // batch_size + 1} (recipes {offset + 1}-{min(offset + batch_size, total_recipes)})")
            
            # Fetch batch of recipes
            recipes = await RecipeService.get_all(limit=batch_size, offset=offset)
            
            if not recipes:
                break
            
            # Show sample of first recipe
            if show_sample and recipes:
                sample_doc = self._recipe_to_document(recipes[0])
                print(f"\n📋 Sample recipe (ID {recipes[0].id}):")
                print(f"   Title: {sample_doc['_source']['title'][:80]}")
                print(f"   Ingredients: {len(sample_doc['_source']['ingredients'])} items")
                if sample_doc['_source']['ingredients']:
                    print(f"   First ingredient: {sample_doc['_source']['ingredients'][0]}")
                print(f"   Instructions length: {len(sample_doc['_source']['instructions'])} chars")
                print(f"   Instructions preview: {sample_doc['_source']['instructions'][:100]}...")
                print()
                show_sample = False
            
            # Bulk index this batch
            result = await self.bulk_index_recipes(recipes)
            total_success += result['success']
            total_failed += result['failed']
            total_skipped += result['skipped']
            
            print(f"  ✅ Indexed: {result['success']}, ⏭️  Skipped: {result['skipped']}, ❌ Failed: {result['failed']}")
            
            offset += batch_size
            
            # Brief pause between batches
            await asyncio.sleep(0.5)
        
        print()
        print("=" * 60)
        print("📈 SYNC COMPLETE!")
        print("=" * 60)
        print(f"✅ Successfully indexed: {total_success} recipes")
        print(f"⏭️  Skipped (malformed): {total_skipped} recipes")
        print(f"❌ Failed:              {total_failed} recipes")
        print(f"📊 Total processed:     {total_success + total_skipped + total_failed} recipes")
        print("=" * 60)
        
        if total_skipped > 0:
            print(f"\n💡 Note: {total_skipped} malformed recipes were skipped (placeholder instructions or single long ingredient)")
        
        return {
            "total": total_recipes,
            "success": total_success,
            "failed": total_failed,
            "skipped": total_skipped
        }
    
    async def search_recipes(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search recipes in Elasticsearch."""
        # Build search query
        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["title^3", "description^2", "ingredients.name^2", "instructions"],
                                "type": "best_fields",
                                "fuzziness": "AUTO"
                            }
                        }
                    ]
                }
            },
            "size": limit
        }
        
        # Add filters if provided
        if filters:
            filter_clauses = []
            
            if filters.get('cuisine_type'):
                filter_clauses.append({"term": {"cuisine_type": filters['cuisine_type']}})
            
            if filters.get('meal_type'):
                filter_clauses.append({"term": {"meal_type": filters['meal_type']}})
            
            if filters.get('max_prep_time'):
                filter_clauses.append({"range": {"prep_time_minutes": {"lte": filters['max_prep_time']}}})
            
            if filter_clauses:
                search_body["query"]["bool"]["filter"] = filter_clauses
        
        # Execute search
        try:
            response = await self.client.search(index=self.index_name, body=search_body)
            return [hit["_source"] for hit in response["hits"]["hits"]]
        except Exception as e:
            print(f"Error searching recipes: {str(e)}")
            return []
    
    async def health_check(self) -> bool:
        """Check if Elasticsearch is healthy."""
        try:
            health = await self.client.cluster.health()
            return health['status'] in ['yellow', 'green']
        except Exception as e:
            print(f"Elasticsearch health check failed: {str(e)}")
            return False


async def get_elasticsearch_service() -> ElasticsearchService:
    """Get Elasticsearch service instance."""
    return ElasticsearchService()

