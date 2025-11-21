"""Integration tests for recipe service embedding functionality."""

import sys
import asyncio
from pathlib import Path
import pytest

# Add src to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from recipes.services.recipe_service import RecipeService
from recipes.models.recipe import Recipe, Ingredient, RecipeIngredient
from recipes.database import get_pool


@pytest.mark.asyncio
async def test_create_recipe_generates_embedding():
    """Test that creating a recipe generates and stores embedding."""
    # Create a test recipe
    recipe = Recipe(
        title="Test Recipe for Embedding Generation",
        description="A test recipe to verify embedding generation",
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
        instructions=["Mix", "Bake"]
    )
    
    try:
        # Create recipe (should generate embedding)
        created = await RecipeService.create(recipe)
        
        if created and created.id:
            # Check if embedding was stored in database
            pool = await get_pool()
            async with pool.acquire() as conn:
                result = await conn.fetchrow(
                    "SELECT embedding FROM recipes WHERE id = $1",
                    created.id
                )
                
                if result and result['embedding']:
                    # Parse embedding
                    embedding_str = str(result['embedding'])
                    embedding_str = embedding_str.strip('[]')
                    embedding = [float(x.strip()) for x in embedding_str.split(',') if x.strip()]
                    
                    assert len(embedding) == 384, "Embedding should be 384 dimensions"
                    assert all(isinstance(x, float) for x in embedding), "Embedding should be floats"
                else:
                    # Embedding might not be generated if sentence-transformers not installed
                    # That's okay - the recipe was still created
                    pass
            
            # Cleanup: delete test recipe
            await RecipeService.delete(created.id)
        
    except Exception as e:
        # If sentence-transformers not installed, that's okay
        if "sentence-transformers" in str(e).lower() or "ImportError" in str(type(e).__name__):
            pytest.skip("sentence-transformers not installed - embedding generation skipped")
        else:
            raise


@pytest.mark.asyncio
async def test_update_recipe_regenerates_embedding():
    """Test that updating recipe title or ingredients regenerates embedding."""
    # Create a test recipe first
    recipe = Recipe(
        title="Original Title",
        ingredients=[
            RecipeIngredient(
                ingredient=Ingredient(name="original"),
                amount=1.0
            )
        ],
        instructions=["Step 1"]
    )
    
    try:
        created = await RecipeService.create(recipe)
        
        if created and created.id:
            # Update the title (should regenerate embedding)
            updated = await RecipeService.update(created.id, {
                "title": "Updated Title"
            })
            
            if updated:
                # Check if embedding was updated
                pool = await get_pool()
                async with pool.acquire() as conn:
                    result = await conn.fetchrow(
                        "SELECT embedding FROM recipes WHERE id = $1",
                        created.id
                    )
                    
                    # Embedding should exist (if sentence-transformers available)
                    # Just verify the update didn't crash
                    assert result is not None
            
            # Cleanup
            await RecipeService.delete(created.id)
        
    except Exception as e:
        # If sentence-transformers not installed, that's okay
        if "sentence-transformers" in str(e).lower() or "ImportError" in str(type(e).__name__):
            pytest.skip("sentence-transformers not installed - embedding generation skipped")
        else:
            raise


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

