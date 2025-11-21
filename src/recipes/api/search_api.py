"""API endpoint for semantic search in Elasticsearch."""

from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict

from ..services.elasticsearch_service import ElasticsearchService
from ..services.embedding_service import get_embedding_service


app = FastAPI(title="Recipes Search API")

# Enable CORS for React client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    """Search request model."""
    model_config = ConfigDict(populate_by_name=True)
    
    query_text: Optional[str] = None
    search_mode: Optional[str] = "text"  # text, semantic, or hybrid
    from_: int = Field(default=0, alias="from")  # Support Elasticsearch 'from' field
    size: int = 10
    knn: Optional[Dict[str, Any]] = None
    query: Optional[Dict[str, Any]] = None


@app.post("/api/recipes/_search")
async def search_recipes(request: SearchRequest) -> Dict[str, Any]:
    """
    Search recipes in Elasticsearch.
    
    Supports:
    - Text search (traditional)
    - Semantic search (using embeddings)
    - Hybrid search (combines both)
    """
    es_service = ElasticsearchService()
    
    try:
        # Handle semantic or hybrid search
        if request.search_mode in ['semantic', 'hybrid'] and request.query_text:
            # Generate embedding for the query
            try:
                embedding_service = get_embedding_service()
                query_embedding = embedding_service.generate_embedding(request.query_text)
            except ImportError:
                raise HTTPException(
                    status_code=503,
                    detail="Semantic search not available: sentence-transformers not installed"
                )
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to generate embedding: {str(e)}"
                )
            
            # Build search body
            search_body: Dict[str, Any] = {
                "from": request.from_,
                "size": request.size,
            }
            
            if request.search_mode == 'semantic':
                # Pure semantic search
                search_body["knn"] = {
                    "field": "embedding",
                    "query_vector": query_embedding,
                    "k": request.size,
                    "num_candidates": 100,
                }
            else:  # hybrid
                # Combine text and semantic search
                search_body["query"] = request.query or {
                    "multi_match": {
                        "query": request.query_text,
                        "fields": ["title^2", "description", "instructions"],
                    }
                }
                search_body["knn"] = {
                    "field": "embedding",
                    "query_vector": query_embedding,
                    "k": request.size,
                    "num_candidates": 100,
                    "boost": 0.5,
                }
            
            # Execute search
            try:
                response = await es_service.client.search(
                    index=es_service.index_name,
                    body=search_body
                )
                # Convert response to dict if needed
                if hasattr(response, 'body'):
                    return response.body
                elif hasattr(response, 'dict'):
                    return response.dict()
                else:
                    return dict(response) if isinstance(response, dict) else response
            except Exception as search_error:
                import traceback
                print(f"Elasticsearch search error: {str(search_error)}")
                print(f"Traceback: {traceback.format_exc()}")
                print(f"Search body: {search_body}")
                raise
        
        # Traditional text search
        elif request.query:
            search_body = {
                "from": request.from_,
                "size": request.size,
                "query": request.query,
            }
            
            # Execute search
            try:
                response = await es_service.client.search(
                    index=es_service.index_name,
                    body=search_body
                )
                # Convert response to dict if needed
                if hasattr(response, 'body'):
                    return response.body
                elif hasattr(response, 'dict'):
                    return response.dict()
                else:
                    return dict(response) if isinstance(response, dict) else response
            except Exception as search_error:
                import traceback
                print(f"Elasticsearch search error: {str(search_error)}")
                print(f"Traceback: {traceback.format_exc()}")
                raise
        
        else:
            raise HTTPException(
                status_code=400,
                detail="Either query_text (for semantic) or query (for text) must be provided"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Search failed: {str(e)}\n{traceback.format_exc()}"
        print(f"API Error: {error_detail}")  # Log full error for debugging
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )
    finally:
        await es_service.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

