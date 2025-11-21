"""Script to generate embeddings for existing recipes in the database."""

import asyncio
import sys
from pathlib import Path

# Add src to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from recipes.database import get_pool, close_pool
from recipes.services.recipe_service import RecipeService
from recipes.services.embedding_service import get_embedding_service


async def generate_embeddings_for_all_recipes(batch_size: int = 100, limit: int = None):
    """
    Generate embeddings for all recipes in the database that don't have embeddings.
    
    Args:
        batch_size: Number of recipes to process in each batch
        limit: Maximum number of recipes to process (None for all)
    """
    pool = await get_pool()
    embedding_service = get_embedding_service()
    
    try:
        async with pool.acquire() as conn:
            # Get all recipe IDs that don't have embeddings
            query = """
                SELECT id, title 
                FROM recipes 
                WHERE embedding IS NULL
                ORDER BY id
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            rows = await conn.fetch(query)
            
            if not rows:
                print("✅ All recipes already have embeddings!")
                return
            
            total = len(rows)
            print(f"📊 Found {total} recipes without embeddings")
            print(f"🔄 Processing in batches of {batch_size}...")
            print()
            
            processed = 0
            errors = 0
            
            for i in range(0, total, batch_size):
                batch = rows[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (total + batch_size - 1) // batch_size
                
                print(f"📦 Processing batch {batch_num}/{total_batches} ({len(batch)} recipes)...")
                
                for row in batch:
                    recipe_id = row['id']
                    title = row['title']
                    
                    try:
                        # Fetch the complete recipe with ingredients
                        recipe = await RecipeService.get_by_id(recipe_id)
                        
                        if not recipe:
                            print(f"  ⚠️  Recipe {recipe_id} not found, skipping")
                            errors += 1
                            continue
                        
                        # Generate embedding
                        embedding = embedding_service.generate_recipe_embedding(recipe)
                        
                        # Format embedding as string for pgvector
                        embedding_str = '[' + ','.join(str(x) for x in embedding) + ']'
                        
                        # Store embedding in database
                        await conn.execute(
                            'UPDATE recipes SET embedding = $1::vector WHERE id = $2',
                            embedding_str,
                            recipe_id
                        )
                        
                        processed += 1
                        
                        if processed % 10 == 0:
                            print(f"  ✅ Processed {processed}/{total} recipes...")
                    
                    except Exception as e:
                        print(f"  ❌ Error processing recipe {recipe_id} ('{title[:50]}'): {str(e)}")
                        errors += 1
                        continue
                
                print(f"  ✅ Batch {batch_num} complete ({processed}/{total} processed, {errors} errors)")
                print()
            
            print(f"🎉 Complete! Processed {processed} recipes, {errors} errors")
    
    finally:
        await close_pool()


async def generate_embeddings_for_recipe(recipe_id: int):
    """Generate embedding for a specific recipe."""
    pool = await get_pool()
    embedding_service = get_embedding_service()
    
    try:
        async with pool.acquire() as conn:
            # Fetch the recipe
            recipe = await RecipeService.get_by_id(recipe_id)
            
            if not recipe:
                print(f"❌ Recipe {recipe_id} not found")
                return False
            
            print(f"📝 Generating embedding for recipe: {recipe.title}")
            
            # Generate embedding
            embedding = embedding_service.generate_recipe_embedding(recipe)
            
            # Format embedding as string for pgvector
            embedding_str = '[' + ','.join(str(x) for x in embedding) + ']'
            
            # Store embedding in database
            await conn.execute(
                'UPDATE recipes SET embedding = $1::vector WHERE id = $2',
                embedding_str,
                recipe_id
            )
            
            print(f"✅ Embedding generated and stored for recipe {recipe_id}")
            return True
    
    finally:
        await close_pool()


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate embeddings for recipes')
    parser.add_argument(
        '--recipe-id',
        type=int,
        help='Generate embedding for a specific recipe ID'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for processing (default: 100)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Maximum number of recipes to process (default: all)'
    )
    
    args = parser.parse_args()
    
    if args.recipe_id:
        await generate_embeddings_for_recipe(args.recipe_id)
    else:
        await generate_embeddings_for_all_recipes(
            batch_size=args.batch_size,
            limit=args.limit
        )


if __name__ == '__main__':
    asyncio.run(main())

