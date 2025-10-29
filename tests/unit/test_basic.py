"""Basic tests for the recipes Python package."""

import sys
from pathlib import Path
import pytest

# Add src to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from recipes.models.recipe import Recipe, Ingredient, Measurement, RecipeIngredient
from recipes.models.schemas import RecipeSchema, RecipeIngredientSchema, RecipeInstructionSchema


def test_recipe_model():
    """Test Recipe model creation."""
    recipe = Recipe(
        title="Test Recipe",
        description="A test recipe",
        ingredients=[],
        instructions=["Step 1", "Step 2"]
    )
    
    assert recipe.title == "Test Recipe"
    assert recipe.description == "A test recipe"
    assert len(recipe.ingredients) == 0
    assert len(recipe.instructions) == 2


def test_ingredient_model():
    """Test Ingredient model creation."""
    ingredient = Ingredient(
        name="Flour",
        category="Baking",
        description="All-purpose flour"
    )
    
    assert ingredient.name == "Flour"
    assert ingredient.category == "Baking"
    assert ingredient.description == "All-purpose flour"


def test_measurement_model():
    """Test Measurement model creation."""
    measurement = Measurement(
        name="Cup",
        abbreviation="C",
        unit_type="volume"
    )
    
    assert measurement.name == "Cup"
    assert measurement.abbreviation == "C"
    assert measurement.unit_type == "volume"


def test_recipe_ingredient_model():
    """Test RecipeIngredient model creation."""
    ingredient = Ingredient(name="Flour")
    measurement = Measurement(name="Cup")
    
    recipe_ingredient = RecipeIngredient(
        ingredient_id=1,
        measurement_id=1,
        amount=2.0,
        notes="Sifted"
    )
    
    assert recipe_ingredient.ingredient_id == 1
    assert recipe_ingredient.measurement_id == 1
    assert recipe_ingredient.amount == 2.0
    assert recipe_ingredient.notes == "Sifted"


def test_recipe_schema():
    """Test RecipeSchema model creation."""
    ingredient = RecipeIngredientSchema(
        item="Flour",
        amount="2 cups"
    )
    
    instruction = RecipeInstructionSchema(
        step=1,
        title="Mix ingredients",
        description="Mix all ingredients in a bowl"
    )
    
    recipe = RecipeSchema(
        title="Test Recipe",
        description="A test recipe",
        ingredients=[ingredient],
        instructions=[instruction]
    )
    
    assert recipe.title == "Test Recipe"
    assert recipe.description == "A test recipe"
    assert len(recipe.ingredients) == 1
    assert len(recipe.instructions) == 1
    assert recipe.ingredients[0].item == "Flour"
    assert recipe.ingredients[0].amount == "2 cups"
    assert recipe.instructions[0].step == 1
    assert recipe.instructions[0].title == "Mix ingredients"


if __name__ == "__main__":
    pytest.main([__file__])
