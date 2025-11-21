"""Tests for embedding service."""

import sys
from pathlib import Path
import pytest

# Add src to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from recipes.models.recipe import Recipe, Ingredient, RecipeIngredient
from recipes.services.embedding_service import EmbeddingService


def test_build_embedding_text():
    """Test building embedding text from recipe title and ingredients."""
    service = EmbeddingService()
    
    # Create a recipe with title and ingredients
    recipe = Recipe(
        title="Chocolate Chip Cookies",
        ingredients=[
            RecipeIngredient(
                ingredient=Ingredient(name="flour"),
                amount=2.0
            ),
            RecipeIngredient(
                ingredient=Ingredient(name="chocolate chips"),
                amount=1.0
            ),
            RecipeIngredient(
                ingredient=Ingredient(name="sugar"),
                amount=0.5
            )
        ]
    )
    
    text = service.build_embedding_text(recipe)
    
    assert "Chocolate Chip Cookies" in text
    assert "flour" in text
    assert "chocolate chips" in text
    assert "sugar" in text


def test_build_embedding_text_no_ingredients():
    """Test building embedding text with no ingredients."""
    service = EmbeddingService()
    
    recipe = Recipe(
        title="Simple Recipe",
        ingredients=[]
    )
    
    text = service.build_embedding_text(recipe)
    
    assert text == "Simple Recipe"


def test_generate_embedding():
    """Test generating an embedding from text."""
    service = EmbeddingService()
    
    text = "Chocolate Chip Cookies with flour, chocolate chips, sugar"
    embedding = service.generate_embedding(text)
    
    # Should return a list of floats
    assert isinstance(embedding, list)
    assert len(embedding) == 384  # all-MiniLM-L6-v2 produces 384-dimensional embeddings
    assert all(isinstance(x, float) for x in embedding)


def test_generate_recipe_embedding():
    """Test generating embedding for a complete recipe."""
    service = EmbeddingService()
    
    recipe = Recipe(
        title="Pasta Carbonara",
        ingredients=[
            RecipeIngredient(
                ingredient=Ingredient(name="pasta"),
                amount=500.0
            ),
            RecipeIngredient(
                ingredient=Ingredient(name="eggs"),
                amount=4.0
            ),
            RecipeIngredient(
                ingredient=Ingredient(name="bacon"),
                amount=200.0
            )
        ]
    )
    
    embedding = service.generate_recipe_embedding(recipe)
    
    # Should return a list of floats
    assert isinstance(embedding, list)
    assert len(embedding) == 384
    assert all(isinstance(x, float) for x in embedding)


def test_generate_batch_embeddings():
    """Test generating embeddings for multiple texts in batch."""
    service = EmbeddingService()
    
    texts = [
        "Chocolate Chip Cookies",
        "Pasta Carbonara",
        "Beef Stew"
    ]
    
    embeddings = service.generate_batch_embeddings(texts)
    
    assert len(embeddings) == 3
    assert all(len(emb) == 384 for emb in embeddings)
    assert all(isinstance(x, float) for emb in embeddings for x in emb)


def test_embedding_similarity():
    """Test that similar recipes produce similar embeddings."""
    service = EmbeddingService()
    
    # Two similar recipes
    recipe1 = Recipe(
        title="Chocolate Chip Cookies",
        ingredients=[
            RecipeIngredient(ingredient=Ingredient(name="flour")),
            RecipeIngredient(ingredient=Ingredient(name="chocolate chips")),
            RecipeIngredient(ingredient=Ingredient(name="sugar"))
        ]
    )
    
    recipe2 = Recipe(
        title="Double Chocolate Cookies",
        ingredients=[
            RecipeIngredient(ingredient=Ingredient(name="flour")),
            RecipeIngredient(ingredient=Ingredient(name="chocolate chips")),
            RecipeIngredient(ingredient=Ingredient(name="cocoa powder"))
        ]
    )
    
    # Very different recipe
    recipe3 = Recipe(
        title="Beef Stew",
        ingredients=[
            RecipeIngredient(ingredient=Ingredient(name="beef")),
            RecipeIngredient(ingredient=Ingredient(name="potatoes")),
            RecipeIngredient(ingredient=Ingredient(name="carrots"))
        ]
    )
    
    emb1 = service.generate_recipe_embedding(recipe1)
    emb2 = service.generate_recipe_embedding(recipe2)
    emb3 = service.generate_recipe_embedding(recipe3)
    
    # Calculate cosine similarity
    def cosine_similarity(a, b):
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(y * y for y in b) ** 0.5
        return dot_product / (norm_a * norm_b)
    
    sim_1_2 = cosine_similarity(emb1, emb2)
    sim_1_3 = cosine_similarity(emb1, emb3)
    
    # Similar recipes should have higher similarity than different ones
    assert sim_1_2 > sim_1_3


if __name__ == "__main__":
    pytest.main([__file__])

