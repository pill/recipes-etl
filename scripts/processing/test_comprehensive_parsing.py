#!/usr/bin/env python3
"""Comprehensive test to demonstrate improved recipe parsing."""

import asyncio
import sys
import json
from pathlib import Path

# Add src to path (script is now in scripts/processing/)
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from recipes.utils.local_parser import LocalRecipeParser


async def main():
    """Test comprehensive recipe parsing."""
    parser = LocalRecipeParser()
    
    # Realistic recipe text with all metadata
    recipe_text = """
    Thai Red Curry with Vegetables
    
    A flavorful and aromatic Thai curry that's perfect for dinner. This vegetarian 
    version is packed with vegetables and coconut milk for a creamy, satisfying meal.
    
    **Ingredients:**
    - 2 tablespoons red curry paste
    - 1 can (14 oz) coconut milk
    - 2 cups mixed vegetables (bell peppers, bamboo shoots, carrots)
    - 1 tablespoon fish sauce (or soy sauce for vegetarian)
    - 1 tablespoon brown sugar
    - Thai basil leaves
    - 2 cloves garlic, minced
    - 1 tablespoon vegetable oil
    - Cooked jasmine rice for serving
    
    **Instructions:**
    1. Heat oil in a large pan over medium heat
    2. Add curry paste and garlic, cook until fragrant (about 1 minute)
    3. Pour in coconut milk and bring to a simmer
    4. Add vegetables and cook for 8-10 minutes until tender
    5. Stir in fish sauce and sugar
    6. Garnish with Thai basil and serve over jasmine rice
    
    Prep time: 15 minutes
    Cook time: 20 minutes
    Difficulty: easy
    """
    
    result = await parser.extract_recipe_data(recipe_text)
    
    # Convert to dict for pretty printing
    result_dict = {
        'title': result.title,
        'description': result.description,
        'prepTime': result.prepTime,
        'cookTime': result.cookTime,
        'chillTime': result.chillTime,
        'panSize': result.panSize,
        'difficulty': result.difficulty,
        'cuisine': result.cuisine,
        'mealType': result.mealType,
        'dietaryTags': result.dietaryTags,
        'ingredients': [
            {
                'item': ing.item,
                'amount': ing.amount,
                'notes': ing.notes
            }
            for ing in result.ingredients
        ],
        'instructions': [
            {
                'step': inst.step,
                'title': inst.title,
                'description': inst.description
            }
            for inst in result.instructions
        ]
    }
    
    print('='*60)
    print('COMPREHENSIVE RECIPE PARSING DEMONSTRATION')
    print('='*60)
    print(json.dumps(result_dict, indent=2))
    print('='*60)
    print('\n📊 METADATA SUMMARY:')
    print(f'  ⏱️  Prep Time: {result.prepTime or "Not detected"}')
    print(f'  🔥 Cook Time: {result.cookTime or "Not detected"}')
    print(f'  📈 Difficulty: {result.difficulty or "Not detected"}')
    print(f'  🌍 Cuisine: {result.cuisine or "Not detected"}')
    print(f'  🍽️  Meal Type: {result.mealType or "Not detected"}')
    print(f'  🥗 Dietary Tags: {", ".join(result.dietaryTags) if result.dietaryTags else "None"}')
    print(f'  📝 Ingredients: {len(result.ingredients)} items')
    print(f'  👨‍🍳 Instructions: {len(result.instructions)} steps')
    print('='*60)


if __name__ == '__main__':
    asyncio.run(main())

