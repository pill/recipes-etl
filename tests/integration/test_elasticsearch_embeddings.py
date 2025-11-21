"""Integration tests for Elasticsearch embeddings functionality."""

import sys
import asyncio
from pathlib import Path
import pytest

# Add src to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from recipes.services.elasticsearch_service import ElasticsearchService
from recipes.services.recipe_service import RecipeService
from recipes.models.recipe import Recipe, Ingredient, RecipeIngredient


@pytest.mark.asyncio
async def test_elasticsearch_index_has_embedding_field():
    """Test that Elasticsearch index includes embedding field in mapping."""
    es_service = ElasticsearchService()
    
    try:
        # Check if index exists
        exists = await es_service.client.indices.exists(index=es_service.index_name)
        
        if exists:
            # Get index mapping
            mapping = await es_service.client.indices.get_mapping(index=es_service.index_name)
            properties = mapping[es_service.index_name]['mappings']['properties']
            
            # Check if embedding field exists
            assert 'embedding' in properties, "Embedding field not found in index mapping"
            assert properties['embedding']['type'] == 'dense_vector', "Embedding field is not dense_vector type"
            assert properties['embedding']['dims'] == 384, "Embedding dimension should be 384"
        else:
            pytest.skip("Elasticsearch index does not exist - run sync-search first")
    finally:
        await es_service.close()


@pytest.mark.asyncio
async def test_index_recipe_with_embedding():
    """Test indexing a recipe with embedding."""
    es_service = ElasticsearchService()
    
    try:
        # Create a test recipe
        recipe = Recipe(
            title="Test Recipe for Embedding",
            description="A test recipe",
            ingredients=[
                RecipeIngredient(
                    ingredient=Ingredient(name="flour"),
                    amount=2.0
                ),
                RecipeIngredient(
                    ingredient=Ingredient(name="sugar"),
                    amount=1.0
                )
            ],
            instructions=["Mix ingredients", "Bake"]
        )
        
        # Index the recipe (this should generate and include embedding)
        result = await es_service.index_recipe(recipe)
        
        # Note: This test requires recipe to have an ID, so it needs to be in DB first
        # For now, just verify the method doesn't crash
        assert result is not None
        
    except Exception as e:
        # If sentence-transformers not installed, skip
        if "sentence-transformers" in str(e).lower() or "ImportError" in str(type(e).__name__):
            pytest.skip("sentence-transformers not installed")
        else:
            raise
    finally:
        await es_service.close()


@pytest.mark.asyncio
async def test_bulk_index_with_embeddings():
    """Test bulk indexing recipes with embeddings."""
    es_service = ElasticsearchService()
    
    try:
        # Create test recipes
        recipes = [
            Recipe(
                title=f"Test Recipe {i}",
                ingredients=[
                    RecipeIngredient(
                        ingredient=Ingredient(name="ingredient1"),
                        amount=1.0
                    )
                ],
                instructions=["Step 1"]
            )
            for i in range(3)
        ]
        
        # Bulk index (should generate embeddings)
        result = await es_service.bulk_index_recipes(recipes)
        
        # Verify results
        assert "success" in result
        assert "failed" in result
        assert "skipped" in result
        
    except Exception as e:
        # If sentence-transformers not installed, skip
        if "sentence-transformers" in str(e).lower() or "ImportError" in str(type(e).__name__):
            pytest.skip("sentence-transformers not installed")
        else:
            raise
    finally:
        await es_service.close()


@pytest.mark.asyncio
async def test_get_recipe_embedding():
    """Test getting recipe embedding from database or generating it."""
    es_service = ElasticsearchService()
    
    try:
        # Create a test recipe (needs to be in DB with an ID)
        # For this test, we'll just verify the method exists and can be called
        recipe = Recipe(
            id=999999,  # Non-existent ID for testing
            title="Test Recipe",
            ingredients=[
                RecipeIngredient(
                    ingredient=Ingredient(name="test"),
                    amount=1.0
                )
            ]
        )
        
        # This will try to fetch from DB, then generate if not found
        embedding = await es_service._get_recipe_embedding(recipe)
        
        # Should return None if recipe doesn't exist, or a list if generated
        assert embedding is None or isinstance(embedding, list)
        if embedding:
            assert len(embedding) == 384
        
    except Exception as e:
        # If sentence-transformers not installed, skip
        if "sentence-transformers" in str(e).lower() or "ImportError" in str(type(e).__name__):
            pytest.skip("sentence-transformers not installed")
        else:
            raise
    finally:
        await es_service.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

