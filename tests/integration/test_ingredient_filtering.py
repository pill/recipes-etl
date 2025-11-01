#!/usr/bin/env python3
"""Test script to verify fixes for new failed recipe entries."""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from recipes.models.schemas import RecipeSchema


def test_ingredient_filtering(recipe_json):
    """Test ingredient filtering logic."""
    # Parse as RecipeSchema
    recipe_schema = RecipeSchema.model_validate(recipe_json)
    
    # Apply filtering logic
    skip_patterns = [
        # Instructions/directions
        'how to do it', 'directions*', 'instructions',
        
        # Cooking actions
        'preheat the', 'in the meantime', 'cooking the', 'bake at', 'bake for',
        'blend everything', 'transfer to', 'mix the', 'place the', 'pour the', 
        'take the', 'add the', 'stir', 'remove from', 'set aside', 'let sit',
        'let it rest', 'allow it to', 'continue cooking', 'reduce heat',
        'warm a', 'heat a', 'bring to a boil',
        
        # Common instruction starters
        'rinse ', 'drain ', 'clean and', 'top with', 'cover with', 'line a',
        'spread the', 'evenly spread', 'put crab', 'start by adding',
        'you can find', 'if you', 'grease baking', 'stretch the',
        
        # Formatting/metadata
        '[video]', '**[', 'recipe*', '&amp;x200b', 'optional as topping',
        'check out my instagram', 'support from', 'if you make this',
        'if you like my recipes',
    ]
    
    valid_count = 0
    skipped_count = 0
    skipped_examples = []
    
    for ing in recipe_schema.ingredients:
        # Check if should be skipped
        if len(ing.item) > 500:
            skipped_count += 1
            skipped_examples.append(('TOO_LONG', ing.item[:60]))
            continue
        
        item_lower = ing.item.lower()
        should_skip = False
        
        for pattern in skip_patterns:
            if pattern in item_lower:
                skipped_count += 1
                skipped_examples.append((pattern, ing.item[:60]))
                should_skip = True
                break
        
        if should_skip:
            continue
        
        if not ing.item.strip('*[]()- \n\t'):
            skipped_count += 1
            skipped_examples.append(('EMPTY', ing.item))
            continue
        
        valid_count += 1
    
    return valid_count, skipped_count, len(recipe_schema.ingredients), skipped_examples


async def test_entry(json_path: str):
    """Test loading a single entry."""
    print(f"\n{'='*70}")
    print(f"Testing: {json_path}")
    print(f"{'='*70}")
    
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        print(f"Title: {data.get('title', 'N/A')}")
        
        valid_count, skipped_count, total_count, examples = test_ingredient_filtering(data)
        
        print(f"Ingredient Analysis:")
        print(f"  Total: {total_count}")
        print(f"  Valid: {valid_count}")
        print(f"  Skipped: {skipped_count}")
        
        if skipped_count > 0:
            print(f"\n  Sample skipped ingredients (showing first 5):")
            for i, (reason, text) in enumerate(examples[:5]):
                print(f"    [{reason}] {text}...")
        
        if valid_count < 2:
            print(f"\n  ❌ WOULD FAIL: Too few valid ingredients ({valid_count} < 2)")
            print(f"     Error message would be: 'Recipe has too few valid ingredients after filtering ({valid_count} valid, {skipped_count} skipped out of {total_count} total)'")
            return False
        else:
            print(f"\n  ✅ WOULD PASS: Has {valid_count} valid ingredients")
            return True
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
        return False


async def main():
    """Test all newly failed entries."""
    failed_entries = [
        "data/stage/Reddit_Recipes_2/entry_616.json",
        "data/stage/Reddit_Recipes_2/entry_623.json",
        "data/stage/Reddit_Recipes_2/entry_63.json",
        "data/stage/Reddit_Recipes_2/entry_633.json",
        "data/stage/Reddit_Recipes_2/entry_642.json",
        "data/stage/Reddit_Recipes_2/entry_644.json",
        "data/stage/Reddit_Recipes_2/entry_647.json",
        "data/stage/Reddit_Recipes_2/entry_649.json",
        "data/stage/Reddit_Recipes_2/entry_652.json",
        "data/stage/Reddit_Recipes_2/entry_653.json",
    ]
    
    print("Testing Enhanced Ingredient Filtering")
    print("="*70)
    
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
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    
    would_pass = sum(1 for _, success in results if success)
    would_fail = sum(1 for _, success in results if not success)
    total = len(results)
    
    print(f"\n✅ Would PASS (has valid ingredients): {would_pass}")
    print(f"❌ Would FAIL (too few ingredients): {would_fail}")
    print(f"\nTotal: {total}")
    
    if would_fail > 0:
        print(f"\n📊 Analysis: {would_fail} recipes have mostly instructions in the ingredients list")
        print("These recipes will now fail gracefully with clear error messages instead of")
        print("silently failing with 'RecipeService.create returned None'")
    
    if would_pass > 0:
        print(f"\n🎯 Good news: {would_pass} recipes should now load successfully with enhanced filtering!")


if __name__ == '__main__':
    asyncio.run(main())

