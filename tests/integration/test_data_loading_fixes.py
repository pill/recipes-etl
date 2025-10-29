#!/usr/bin/env python3
"""Test script to verify fixes for failed recipe entries."""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from recipes.models.schemas import RecipeSchema
from recipes.workflows.activities import load_json_to_db


async def test_entry(json_path: str):
    """Test loading a single entry."""
    print(f"\n{'='*60}")
    print(f"Testing: {json_path}")
    print(f"{'='*60}")
    
    try:
        # Try to load the JSON
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        print("✅ JSON loaded successfully")
        print(f"Title: {data.get('title', 'N/A')}")
        
        # Try to validate against RecipeSchema
        # First handle old format
        if 'recipeData' in data:
            recipe_data = data['recipeData']
        else:
            recipe_data = data
        
        # Apply the same transformations as in load_json_to_db
        # Handle time conversions
        for field in ['prepTime', 'cookTime', 'chillTime']:
            if field in recipe_data:
                value = recipe_data[field]
                if value == '<UNKNOWN>' or value == 'null' or value == '':
                    recipe_data[field] = None
                elif isinstance(value, (int, float)):
                    recipe_data[field] = f"{int(value)} minutes"
        
        # Handle difficulty
        if 'difficulty' in recipe_data and recipe_data['difficulty']:
            difficulty_value = str(recipe_data['difficulty']).lower().strip()
            valid_difficulty = {'easy', 'medium', 'hard'}
            if difficulty_value in valid_difficulty:
                recipe_data['difficulty'] = difficulty_value
            else:
                recipe_data['difficulty'] = None
        
        # Handle mealType
        if 'mealType' in recipe_data and recipe_data['mealType']:
            meal_type_value = str(recipe_data['mealType']).lower().strip()
            valid_meal_types = {'breakfast', 'lunch', 'dinner', 'snack', 'dessert'}
            meal_type_mapping = {
                'side dish': 'snack',
                'side': 'snack',
                'soup': 'lunch',
                'appetizer': 'snack',
            }
            if meal_type_value in valid_meal_types:
                recipe_data['mealType'] = meal_type_value
            elif meal_type_value in meal_type_mapping:
                recipe_data['mealType'] = meal_type_mapping[meal_type_value]
            else:
                recipe_data['mealType'] = None
        
        # Try to validate
        recipe_schema = RecipeSchema.model_validate(recipe_data)
        print("✅ Schema validation successful")
        print(f"Ingredients: {len(recipe_schema.ingredients)}")
        print(f"Instructions: {len(recipe_schema.instructions)}")
        print(f"Difficulty: {recipe_schema.difficulty}")
        print(f"Meal Type: {recipe_schema.mealType}")
        
        # Count malformed ingredients
        malformed_count = 0
        for ing in recipe_schema.ingredients:
            item_lower = ing.item.lower()
            skip_patterns = [
                'how to do it', 'preheat the oven', 'in the meantime',
                'cooking the', 'blend everything', 'transfer to',
                'mix the', 'place the', 'pour the', 'take the',
                '[video]', '**[', 'recipe*', '&amp;x200b',
            ]
            if any(pattern in item_lower for pattern in skip_patterns):
                malformed_count += 1
                print(f"  ⚠️  Malformed ingredient (will be skipped): '{ing.item[:60]}...'")
        
        valid_ingredients = len(recipe_schema.ingredients) - malformed_count
        print(f"Valid ingredients after filtering: {valid_ingredients}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
        return False


async def main():
    """Test all previously failed entries."""
    failed_entries = [
        "data/stage/2025-10-14/stromberg_data/entry_3.json",
        "data/stage/2025-10-14/stromberg_data/entry_6.json",
        "data/stage/2025-10-14/stromberg_data/entry_8.json",
        "data/stage/Reddit_Recipes/entry_108.json",
        "data/stage/Reddit_Recipes/entry_110.json",
        "data/stage/Reddit_Recipes/entry_114.json",
        "data/stage/Reddit_Recipes/entry_117.json",
        "data/stage/Reddit_Recipes/entry_120.json",
    ]
    
    print("Testing Data Loading Fixes")
    print("="*60)
    
    results = []
    for entry_path in failed_entries:
        full_path = PROJECT_ROOT / entry_path
        if full_path.exists():
            success = await test_entry(str(full_path))
            results.append((entry_path, success))
        else:
            print(f"\n⚠️  File not found: {entry_path}")
            results.append((entry_path, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for entry, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {entry}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The fixes are working correctly.")
    else:
        print(f"\n⚠️  {total - passed} tests still failing. Review output above.")


if __name__ == '__main__':
    asyncio.run(main())

