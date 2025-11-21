"""Tests for search API endpoint."""

import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Add src to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from fastapi.testclient import TestClient
from recipes.api.search_api import app, SearchRequest


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_search_request_model():
    """Test SearchRequest model validation."""
    # Test with all fields
    request = SearchRequest(
        query_text="test query",
        search_mode="semantic",
        from_=0,
        size=10
    )
    assert request.query_text == "test query"
    assert request.search_mode == "semantic"
    assert request.from_ == 0
    assert request.size == 10
    
    # Test with 'from' alias
    request2 = SearchRequest(
        query_text="test",
        from_=5
    )
    assert request2.from_ == 5


@patch('recipes.api.search_api.ElasticsearchService')
@patch('recipes.api.search_api.get_embedding_service')
def test_semantic_search_endpoint(mock_get_embedding, mock_es_service_class):
    """Test semantic search endpoint."""
    # Mock embedding service
    mock_embedding_service = MagicMock()
    mock_embedding_service.generate_embedding.return_value = [0.1] * 384
    mock_get_embedding.return_value = mock_embedding_service
    
    # Mock Elasticsearch service
    mock_es_service = AsyncMock()
    mock_es_service.index_name = "recipes"
    mock_es_service.client.search = AsyncMock(return_value={
        "hits": {
            "hits": [
                {
                    "_source": {
                        "id": 1,
                        "title": "Test Recipe",
                        "ingredients": []
                    }
                }
            ],
            "total": {"value": 1}
        }
    })
    mock_es_service_class.return_value = mock_es_service
    
    client = TestClient(app)
    
    response = client.post(
        "/api/recipes/_search",
        json={
            "query_text": "comfort food",
            "search_mode": "semantic",
            "from": 0,
            "size": 10
        }
    )
    
    assert response.status_code == 200
    assert "hits" in response.json()
    mock_embedding_service.generate_embedding.assert_called_once_with("comfort food")
    mock_es_service.client.search.assert_called_once()


@patch('recipes.api.search_api.ElasticsearchService')
@patch('recipes.api.search_api.get_embedding_service')
def test_hybrid_search_endpoint(mock_get_embedding, mock_es_service_class):
    """Test hybrid search endpoint."""
    # Mock embedding service
    mock_embedding_service = MagicMock()
    mock_embedding_service.generate_embedding.return_value = [0.1] * 384
    mock_get_embedding.return_value = mock_embedding_service
    
    # Mock Elasticsearch service
    mock_es_service = AsyncMock()
    mock_es_service.index_name = "recipes"
    mock_es_service.client.search = AsyncMock(return_value={
        "hits": {
            "hits": [],
            "total": {"value": 0}
        }
    })
    mock_es_service_class.return_value = mock_es_service
    
    client = TestClient(app)
    
    response = client.post(
        "/api/recipes/_search",
        json={
            "query_text": "pasta",
            "search_mode": "hybrid",
            "from": 0,
            "size": 10
        }
    )
    
    assert response.status_code == 200
    # Verify both query and knn were included
    call_args = mock_es_service.client.search.call_args
    search_body = call_args.kwargs['body']
    assert "query" in search_body
    assert "knn" in search_body


@patch('recipes.api.search_api.ElasticsearchService')
def test_text_search_endpoint(mock_es_service_class):
    """Test traditional text search endpoint."""
    # Mock Elasticsearch service
    mock_es_service = AsyncMock()
    mock_es_service.index_name = "recipes"
    mock_es_service.client.search = AsyncMock(return_value={
        "hits": {
            "hits": [
                {
                    "_source": {
                        "id": 1,
                        "title": "Test Recipe"
                    }
                }
            ],
            "total": {"value": 1}
        }
    })
    mock_es_service_class.return_value = mock_es_service
    
    client = TestClient(app)
    
    response = client.post(
        "/api/recipes/_search",
        json={
            "query": {
                "multi_match": {
                    "query": "chicken",
                    "fields": ["title"]
                }
            },
            "from": 0,
            "size": 10
        }
    )
    
    assert response.status_code == 200
    assert "hits" in response.json()


@patch('recipes.api.search_api.get_embedding_service')
def test_semantic_search_missing_dependency(mock_get_embedding):
    """Test semantic search when sentence-transformers is not installed."""
    mock_get_embedding.side_effect = ImportError("No module named 'sentence_transformers'")
    
    client = TestClient(app)
    
    response = client.post(
        "/api/recipes/_search",
        json={
            "query_text": "test",
            "search_mode": "semantic"
        }
    )
    
    assert response.status_code == 503
    assert "sentence-transformers not installed" in response.json()["detail"]


def test_search_endpoint_missing_params():
    """Test search endpoint with missing required parameters."""
    client = TestClient(app)
    
    response = client.post(
        "/api/recipes/_search",
        json={}
    )
    
    assert response.status_code == 400
    assert "must be provided" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

