#!/usr/bin/env python3
"""Test UUID filename generation."""

import asyncio
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from recipes.utils.json_processor import JSONProcessor
from recipes.models.schemas import RecipeSchema, RecipeIngredientSchema, RecipeInstructionSchema


async def test_uuid_filename():
    """Test that JSON files are saved with UUID as filename."""
    print("Testing UUID filename generation...")
    
    # Create a test recipe
    test_recipe = RecipeSchema(
        title="Test Recipe",
        description="A test recipe",
        ingredients=[
            RecipeIngredientSchema(item="flour", amount="1 cup", notes=None),
            RecipeIngredientSchema(item="sugar", amount="2 tbsp", notes=None),
        ],
        instructions=[
            RecipeInstructionSchema(step=1, title="Step 1", description="Mix ingredients"),
            RecipeInstructionSchema(step=2, title="Step 2", description="Bake for 30 minutes"),
        ],
        prepTime="10 minutes",
        cookTime="30 minutes",
        difficulty="easy",
        cuisine="American",
        mealType="dessert"
    )
    
    # Save to JSON
    processor = JSONProcessor()
    output_path = await processor.save_recipe_json(
        test_recipe,
        entry_number=123,  # This should be ignored
        subdirectory="test_uuid"
    )
    
    print(f"Saved to: {output_path}")
    
    # Check filename format
    filename = Path(output_path).name
    print(f"Filename: {filename}")
    
    # Should be UUID.json format
    if filename.endswith('.json'):
        uuid_part = filename[:-5]  # Remove .json
        if len(uuid_part) == 36 and uuid_part.count('-') == 4:
            print("✅ Filename is valid UUID format")
        else:
            print(f"❌ Filename is not UUID format: {uuid_part}")
            return False
    else:
        print("❌ Filename doesn't end with .json")
        return False
    
    # Check file contents
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    if 'uuid' in data:
        print(f"✅ UUID in file: {data['uuid']}")
        if data['uuid'] == uuid_part:
            print("✅ UUID in filename matches UUID in content")
        else:
            print("❌ UUID in filename doesn't match UUID in content")
            return False
    else:
        print("❌ No UUID in file content")
        return False
    
    # Clean up
    os.remove(output_path)
    os.rmdir(Path(output_path).parent)
    
    print("✅ Test passed!")
    return True


async def main():
    """Run the test."""
    success = await test_uuid_filename()
    if success:
        print("\n🎉 UUID filename generation works correctly!")
    else:
        print("\n❌ UUID filename generation failed!")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())

