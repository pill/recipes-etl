# Reindex Elasticsearch with Embeddings

This guide shows how to reindex your Elasticsearch index to include vector embeddings.

## Prerequisites

1. **Install dependencies** (if not already installed):
   ```bash
   source venv/bin/activate
   pip install sentence-transformers
   ```

   Note: If you encounter dependency conflicts with Python 3.13, you may need to:
   - Use Python 3.11 or 3.12 instead, or
   - Install with: `pip install sentence-transformers --no-deps` and then install dependencies manually

2. **Ensure Elasticsearch is running**:
   ```bash
   docker-compose up -d elasticsearch
   ```

## Reindex with Embeddings

### Option 1: Using CLI Command (Recommended)

```bash
source activate.sh
python -m recipes.cli sync-search --recreate-index
```

This will:
1. ✅ Delete the existing Elasticsearch index
2. ✅ Create a new index with the embedding field mapping
3. ✅ Sync all recipes from the database
4. ✅ Generate embeddings for each recipe (or use existing ones from database)
5. ✅ Index recipes with embeddings included

### Option 2: Using Python Script

```python
import asyncio
from recipes.services.elasticsearch_service import ElasticsearchService

async def reindex():
    es_service = ElasticsearchService()
    
    try:
        # Health check
        if not await es_service.health_check():
            print("❌ Elasticsearch is not healthy!")
            return
        
        # Delete existing index
        print("🗑️  Deleting existing index...")
        await es_service.delete_index()
        
        # Create new index with embedding field
        print("📝 Creating index with embeddings...")
        await es_service.create_index()
        
        # Sync all recipes (embeddings will be included)
        print("🔄 Syncing recipes with embeddings...")
        result = await es_service.sync_all_from_database(batch_size=1000)
        
        print(f"✅ Successfully indexed: {result['success']} recipes")
        print(f"⏭️  Skipped: {result['skipped']} recipes")
        print(f"❌ Failed: {result['failed']} recipes")
        
    finally:
        await es_service.close()

# Run it
asyncio.run(reindex())
```

## What Happens During Reindexing

1. **Index Recreation**: The old index is deleted and a new one is created with:
   - All existing fields (title, description, ingredients, etc.)
   - New `embedding` field as `dense_vector` (384 dimensions)

2. **Embedding Generation**: For each recipe:
   - First checks if embedding exists in PostgreSQL database
   - If found, uses the existing embedding
   - If not found, generates a new embedding from title + ingredients
   - Stores generated embeddings in database for future use

3. **Bulk Indexing**: Recipes are indexed in batches (default: 1000) for efficiency

## Verify Embeddings

After reindexing, verify that embeddings are included:

```bash
# Check a sample document
curl -X GET "localhost:9200/recipes/_search?pretty&size=1" | grep -A 5 embedding
```

Or in Python:

```python
from recipes.services.elasticsearch_service import ElasticsearchService

async def check_embeddings():
    es_service = ElasticsearchService()
    
    # Get a sample document
    response = await es_service.client.search(
        index=es_service.index_name,
        body={"size": 1}
    )
    
    if response["hits"]["hits"]:
        doc = response["hits"]["hits"][0]["_source"]
        if "embedding" in doc:
            print(f"✅ Embedding found! Length: {len(doc['embedding'])}")
        else:
            print("❌ No embedding in document")
    
    await es_service.close()

import asyncio
asyncio.run(check_embeddings())
```

## Troubleshooting

### Dependency Issues

If you get errors installing `sentence-transformers`:

1. **Try with Python 3.11 or 3.12**:
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Or install without torch** (sentence-transformers will use CPU):
   ```bash
   pip install sentence-transformers --no-deps
   pip install transformers numpy scikit-learn
   ```

### Elasticsearch Not Running

```bash
# Start Elasticsearch
docker-compose up -d elasticsearch

# Check health
curl http://localhost:9200/_cluster/health
```

### Slow Reindexing

If reindexing is slow:
- Reduce batch size: `--batch-size 100`
- Generate embeddings in smaller batches
- Ensure embeddings are pre-generated in database first

## Next Steps

After reindexing, you can:
- Use semantic search with kNN queries
- Combine text and semantic search (hybrid search)
- Find similar recipes using embeddings

See `docs/EMBEDDINGS_GUIDE.md` for search examples.

