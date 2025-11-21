# Semantic Search in React Client

This guide explains how to use semantic search from the React client.

## Overview

The React client now supports three search modes:
1. **Text Search** - Traditional keyword-based search
2. **Semantic Search** - Finds recipes by meaning using vector embeddings
3. **Hybrid Search** - Combines text and semantic search for best results

## Setup

### 1. Install API Dependencies

The search API requires FastAPI and Uvicorn:

```bash
source venv/bin/activate
pip install fastapi uvicorn
```

### 2. Start the API Server

Run the search API server:

```bash
cd /Users/pavery/dev/recipes-etl
source activate.sh
python -m recipes.api
```

**If port 8000 is already in use:**

Option 1: Kill the existing process
```bash
# Find the process
lsof -i :8000

# Kill it (replace PID with the actual process ID)
kill <PID>
```

Option 2: Use a different port
```bash
python -m recipes.api 8001
```

Then update `client/vite.config.ts` to use the new port:
```typescript
'/api/recipes/_search': {
  target: 'http://localhost:8001',  // Change port here
  changeOrigin: true,
}
```

**Important:** Always use `source activate.sh` first to set the PYTHONPATH correctly!

The API will be available at `http://localhost:8000`

### 3. Configure Vite Proxy

Update `client/vite.config.ts` to proxy API requests:

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

### 4. Start the React Client

```bash
cd client
npm run dev
```

## Using Semantic Search

The `SearchRecipes` component now has three search modes:

### Text Search (Default)
- Traditional keyword matching
- Fast and reliable
- Good for exact ingredient names or recipe titles

### Semantic Search
- Finds recipes by meaning
- Great for conceptual queries like:
  - "comfort food"
  - "healthy breakfast"
  - "quick weeknight dinner"
  - "party appetizers"

### Hybrid Search
- Combines text and semantic search
- Best of both worlds
- Text search for exact matches, semantic for meaning

## How It Works

1. **User enters query** in the React component
2. **Query sent to API** at `/api/recipes/_search`
3. **Backend generates embedding** for the query text
4. **kNN search** in Elasticsearch finds similar recipes
5. **Results returned** to React client

## API Endpoint

The API endpoint accepts:

```json
{
  "query_text": "comfort food",
  "search_mode": "semantic",  // or "text" or "hybrid"
  "from": 0,
  "size": 10
}
```

For semantic/hybrid search:
- `query_text`: The search query (required)
- `search_mode`: "semantic" or "hybrid"
- `from`: Pagination offset
- `size`: Number of results

For text search:
- `query`: Elasticsearch query object (traditional)

## Example Queries

**Semantic Search Examples:**
- "comfort food" → Finds hearty, warming dishes
- "healthy breakfast" → Finds nutritious morning meals
- "quick weeknight dinner" → Finds fast, simple recipes
- "party appetizers" → Finds finger foods and snacks

**Text Search Examples:**
- "chicken pasta" → Exact keyword matches
- "chocolate chip cookies" → Specific recipe names

**Hybrid Search:**
- Best for general queries where you want both exact matches and semantic similarity

## Troubleshooting

### "Semantic search not available"

This means `sentence-transformers` isn't installed. Install it:

```bash
pip install sentence-transformers
```

### API server not running

Make sure the API server is running on port 8000:

```bash
python -m recipes.api.search_api
```

### CORS errors

The API includes CORS middleware, but if you see errors, check:
- API server is running
- React dev server proxy is configured
- Ports match (8000 for API, 5173 for Vite)

## Next Steps

- Add filters (cuisine, meal type, etc.) to semantic search
- Add similarity scores to results
- Cache query embeddings for performance
- Add "find similar recipes" feature

