# Recipe Vector Embeddings Guide

This guide explains how vector embeddings are generated and used for recipe semantic search.

## Overview

Each recipe document has a vector embedding generated from its **title** and **ingredients**. These embeddings enable semantic search, allowing you to find recipes based on meaning rather than exact keyword matches.

## Architecture

### Components

1. **Embedding Service** (`src/recipes/services/embedding_service.py`)
   - Generates vector embeddings using sentence-transformers
   - Uses the `all-MiniLM-L6-v2` model (384 dimensions)
   - Combines recipe title and ingredients into a single text representation

2. **Database Schema**
   - `recipes.embedding` column (vector(384))
   - Indexed using HNSW for fast approximate nearest neighbor search

3. **Elasticsearch Integration**
   - Embeddings are included in Elasticsearch documents as `dense_vector` fields
   - Enables semantic search in Elasticsearch using kNN queries
   - Automatically fetched from database or generated when indexing

4. **Recipe Service Integration**
   - Automatically generates embeddings when recipes are created
   - Regenerates embeddings when title or ingredients are updated

## Setup

### 1. Install Dependencies

```bash
pip install sentence-transformers torch
```

Or install from requirements.txt:
```bash
pip install -r requirements.txt
```

### 2. Run Database Migration

Apply the migration to add the embedding column:

```bash
psql -U postgres -d recipes -f db/migrations/002_add_recipe_embeddings.sql
```

Or using connection string:
```bash
psql postgresql://postgres:postgres@localhost:5432/recipes -f db/migrations/002_add_recipe_embeddings.sql
```

### 3. Recreate Elasticsearch Index

If you have an existing Elasticsearch index, you'll need to recreate it to include the embedding field:

```python
from recipes.services.elasticsearch_service import ElasticsearchService

async def recreate_index():
    es_service = ElasticsearchService()
    
    # Delete existing index
    await es_service.delete_index()
    
    # Create new index with embedding field
    await es_service.create_index()
    
    # Re-sync all recipes (embeddings will be included)
    await es_service.sync_all_from_database()
    
    await es_service.close()

# Run it
import asyncio
asyncio.run(recreate_index())
```

Or using the CLI if available:
```bash
python -m recipes.cli sync-search --recreate-index
```

### 4. Generate Embeddings for Existing Recipes

If you have existing recipes without embeddings, use the backfill script:

```bash
# Generate embeddings for all recipes without embeddings
python scripts/processing/generate_embeddings.py

# Generate embedding for a specific recipe
python scripts/processing/generate_embeddings.py --recipe-id 123

# Process in smaller batches with a limit
python scripts/processing/generate_embeddings.py --batch-size 50 --limit 1000
```

## How It Works

### Embedding Generation

The embedding service combines the recipe title and ingredient names into a single text:

```
"Chocolate Chip Cookies. flour, chocolate chips, sugar, butter, eggs"
```

This text is then passed through the sentence transformer model to generate a 384-dimensional vector.

### Automatic Generation

Embeddings are automatically generated:
- When a new recipe is created via `RecipeService.create()`
- When a recipe's title or ingredients are updated via `RecipeService.update()`
- When indexing recipes to Elasticsearch (if not already in database)

### Elasticsearch Integration

When recipes are indexed to Elasticsearch:
1. The service first checks if an embedding exists in the database
2. If found, it uses the existing embedding
3. If not found, it generates a new embedding and stores it in the database
4. The embedding is included in the Elasticsearch document as a `dense_vector` field

This ensures embeddings are always available in Elasticsearch for semantic search, while also being stored in PostgreSQL for consistency.

### Manual Generation

You can also generate embeddings manually:

```python
from recipes.services.embedding_service import get_embedding_service
from recipes.services.recipe_service import RecipeService

# Get a recipe
recipe = await RecipeService.get_by_id(recipe_id)

# Generate embedding
embedding_service = get_embedding_service()
embedding = embedding_service.generate_recipe_embedding(recipe)

# Embedding is a list of 384 floats
print(f"Embedding dimension: {len(embedding)}")
```

## Semantic Search

### Using Elasticsearch for Semantic Search

Embeddings are automatically included in Elasticsearch documents, enabling semantic search using kNN (k-nearest neighbors) queries:

```python
from recipes.services.elasticsearch_service import ElasticsearchService
from recipes.services.embedding_service import get_embedding_service

async def semantic_search(query_text: str, limit: int = 10):
    """Perform semantic search using embeddings."""
    es_service = ElasticsearchService()
    embedding_service = get_embedding_service()
    
    # Generate embedding for the query
    query_embedding = embedding_service.generate_embedding(query_text)
    
    # Search using kNN
    search_body = {
        "knn": {
            "field": "embedding",
            "query_vector": query_embedding,
            "k": limit,
            "num_candidates": 100
        },
        "_source": ["id", "title", "description", "ingredients"]
    }
    
    response = await es_service.client.search(
        index=es_service.index_name,
        body=search_body
    )
    
    return [hit["_source"] for hit in response["hits"]["hits"]]

# Usage
results = await semantic_search("chocolate cookies with nuts", limit=5)
for recipe in results:
    print(f"{recipe['title']}: {recipe.get('description', '')[:100]}")
```

### Hybrid Search (Text + Semantic)

You can combine traditional text search with semantic search for better results:

```python
async def hybrid_search(query_text: str, limit: int = 10):
    """Combine text search and semantic search."""
    es_service = ElasticsearchService()
    embedding_service = get_embedding_service()
    
    # Generate embedding for the query
    query_embedding = embedding_service.generate_embedding(query_text)
    
    search_body = {
        "query": {
            "bool": {
                "should": [
                    # Text search
                    {
                        "multi_match": {
                            "query": query_text,
                            "fields": ["title^3", "description^2", "ingredients.name^2"],
                            "type": "best_fields",
                            "fuzziness": "AUTO"
                        }
                    }
                ]
            }
        },
        "knn": {
            "field": "embedding",
            "query_vector": query_embedding,
            "k": limit,
            "num_candidates": 100,
            "boost": 0.5  # Weight semantic search
        },
        "size": limit
    }
    
    response = await es_service.client.search(
        index=es_service.index_name,
        body=search_body
    )
    
    return [hit["_source"] for hit in response["hits"]["hits"]]
```

### Using pgvector for Similarity Search

You can also perform semantic similarity searches using PostgreSQL's pgvector extension:

```sql
-- Find recipes similar to a given recipe (by ID)
SELECT 
    r.id,
    r.title,
    1 - (r.embedding <=> (SELECT embedding FROM recipes WHERE id = 123)) as similarity
FROM recipes r
WHERE r.id != 123
ORDER BY r.embedding <=> (SELECT embedding FROM recipes WHERE id = 123)
LIMIT 10;

-- Find recipes similar to a query embedding
-- (You would need to generate the query embedding first)
SELECT 
    r.id,
    r.title,
    1 - (r.embedding <=> '[0.1, 0.2, ...]'::vector) as similarity
FROM recipes r
ORDER BY r.embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 10;
```

### Python Example

```python
from recipes.services.embedding_service import get_embedding_service
from recipes.database import get_pool

async def find_similar_recipes(recipe_id: int, limit: int = 10):
    """Find recipes similar to a given recipe."""
    pool = await get_pool()
    
    async with pool.acquire() as conn:
        query = """
            SELECT 
                r.id,
                r.title,
                1 - (r.embedding <=> (SELECT embedding FROM recipes WHERE id = $1)) as similarity
            FROM recipes r
            WHERE r.id != $1 AND r.embedding IS NOT NULL
            ORDER BY r.embedding <=> (SELECT embedding FROM recipes WHERE id = $1)
            LIMIT $2
        """
        
        rows = await conn.fetch(query, recipe_id, limit)
        return [dict(row) for row in rows]

# Usage
similar = await find_similar_recipes(recipe_id=123, limit=5)
for recipe in similar:
    print(f"{recipe['title']}: {recipe['similarity']:.3f}")
```

## Model Details

- **Model**: `all-MiniLM-L6-v2`
- **Dimensions**: 384
- **Speed**: Fast inference, suitable for real-time use
- **Quality**: Good balance between speed and quality for semantic search

### Alternative Models

You can use different models by initializing the embedding service with a different model name:

```python
from recipes.services.embedding_service import EmbeddingService

# Use a larger, more accurate model
service = EmbeddingService(model_name='all-mpnet-base-v2')  # 768 dimensions

# Note: You'll need to update the database schema to match the new dimension size
```

## Performance Considerations

1. **First Load**: The sentence transformer model is loaded lazily on first use. This may take a few seconds.

2. **Batch Processing**: When generating embeddings for many recipes, use the batch script which processes them in batches to avoid memory issues.

3. **Index Performance**: The HNSW index provides fast approximate nearest neighbor search, suitable for large datasets.

4. **Storage**: Each embedding takes ~1.5KB (384 floats × 4 bytes), so 10,000 recipes would use ~15MB for embeddings.

## Troubleshooting

### Missing Embeddings

If recipes don't have embeddings:
1. Check that the migration was applied: `SELECT COUNT(*) FROM recipes WHERE embedding IS NOT NULL;`
2. Run the backfill script: `python scripts/processing/generate_embeddings.py`

### Model Loading Issues

If you encounter issues loading the model:
1. Ensure sentence-transformers is installed: `pip install sentence-transformers`
2. The model will be downloaded automatically on first use
3. Check your internet connection for the initial download

### Database Errors

If you see errors about the vector type:
1. Ensure pgvector extension is installed: `CREATE EXTENSION IF NOT EXISTS vector;`
2. Verify the migration was applied correctly

## Future Enhancements

Potential improvements:
- Add semantic search API endpoint
- Support for query embeddings (search by natural language)
- Integration with Elasticsearch for hybrid search
- Support for multiple embedding models
- Embedding-based recipe recommendations

