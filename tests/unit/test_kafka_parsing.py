"""Test parsing of Kafka recipe JSON files."""

import pytest
import asyncio
from recipes.utils.local_parser import LocalRecipeParser


@pytest.mark.asyncio
async def test_matcha_mousse_parsing():
    """Test parsing of Matcha mousse recipe with embedded newlines."""
    
    # This is the actual problematic text from the JSON
    text = """(Serves 2)

・1/2 tbsp. matcha

・2 tsp. water

・3/4 cup milk

・2 1/2 oz marshmallows

・2 tbsp. heavy cream

・whipped cream, as needed (optional)

・matcha (optional)

Instructions"""
    
    parser = LocalRecipeParser()
    recipe = await parser.extract_recipe_data(text)
    
    # Should extract individual ingredients, not one blob
    assert len(recipe.ingredients) > 3, f'Should extract multiple ingredients, got {len(recipe.ingredients)}'
    
    # Should filter out "(Serves 2)"
    ingredient_items = [ing.item.lower() for ing in recipe.ingredients]
    assert not any('serves' in item for item in ingredient_items), 'Should filter out serving size'
    
    # Should filter out "Instructions"
    assert not any('instructions' in item for item in ingredient_items), 'Should filter out section headers'
    
    # Should keep actual ingredients
    assert any('matcha' in item for item in ingredient_items), 'Should keep matcha'
    assert any('milk' in item for item in ingredient_items), 'Should keep milk'
    assert any('marshmallow' in item for item in ingredient_items), 'Should keep marshmallows'


@pytest.mark.asyncio
async def test_chicken_nanban_parsing():
    """Test that instructions aren't parsed as ingredients."""
    
    # Simulated problematic input (real Kafka recipe with bad data)
    text = """Ingredients:
Coat the chicken pieces evenly with potato starch and let rest for 5 minutes.
In a separate pan, combine C ingredients (sugar, vinegar, soy sauce, and mirin)

Instructions:
Make the tartar sauce."""
    
    parser = LocalRecipeParser()
    recipe = await parser.extract_recipe_data(text)
    
    # When all ingredients are filtered out (all were instructions), 
    # should get a placeholder ingredient
    assert len(recipe.ingredients) >= 1, 'Should have at least placeholder ingredient'
    
    # Should NOT include instruction-like text as ingredients
    ingredient_items = [ing.item for ing in recipe.ingredients]
    
    # Either we get a placeholder, or valid ingredients (but not instructions)
    for ing_item in ingredient_items:
        item_lower = ing_item.lower()
        
        # If it's the placeholder, that's fine
        if 'ingredients listed in recipe text' in item_lower:
            continue
        
        # Otherwise, should not start with imperative verbs
        first_word = ing_item.split()[0].lower() if ing_item.split() else ''
        assert first_word not in ['coat', 'combine', 'in'], f'Instruction verb found: {ing_item}'


@pytest.mark.asyncio
async def test_section_header_filtering():
    """Test that section headers are filtered out."""
    
    text = """Ingredients:
For the Cookies
1 cup flour
2 eggs
For the Filling
1 cup cream

Instructions:
Mix ingredients."""
    
    parser = LocalRecipeParser()
    recipe = await parser.extract_recipe_data(text)
    
    ingredient_items = [ing.item.lower() for ing in recipe.ingredients]
    
    # Should filter out section headers
    assert not any('for the cookies' in item for item in ingredient_items), 'Should filter "For the Cookies"'
    assert not any('for the filling' in item for item in ingredient_items), 'Should filter "For the Filling"'
    
    # Should keep actual ingredients
    assert any('flour' in item for item in ingredient_items), 'Should keep flour'
    assert any('egg' in item for item in ingredient_items), 'Should keep eggs'


@pytest.mark.asyncio
async def test_japanese_bullet_points():
    """Test handling of Japanese bullet points (・)."""
    
    text = """Ingredients:
・1/2 tbsp. matcha
・2 tsp. water
・3/4 cup milk

Instructions:
Mix all ingredients."""
    
    parser = LocalRecipeParser()
    recipe = await parser.extract_recipe_data(text)
    
    # Should extract individual ingredients
    assert len(recipe.ingredients) >= 3, f'Should extract at least 3 ingredients, got {len(recipe.ingredients)}'
    
    ingredient_items = [ing.item.lower() for ing in recipe.ingredients]
    assert any('matcha' in item for item in ingredient_items), 'Should extract matcha'
    assert any('water' in item for item in ingredient_items), 'Should extract water'
    assert any('milk' in item for item in ingredient_items), 'Should extract milk'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

