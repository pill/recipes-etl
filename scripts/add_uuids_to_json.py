#!/usr/bin/env python3
"""Add UUIDs to JSON files after database insertion."""

import asyncio
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from recipes.database import get_pool
from recipes.services.recipe_service import RecipeService


async def add_uuid_to_json(json_path: str):
    """Add UUID from database to JSON file."""
    # Load recipe from database by title
    with open(json_path, 'r') as f:
        recipe_data = json.load(f)
    
    title = recipe_data.get('title', '').strip()
    if not title:
        print(f"⚠️  No title in {json_path}")
        return False
    
    # Get recipe from database
    recipe = await RecipeService.get_by_title(title)
    
    if not recipe:
        print(f"⚠️  Recipe not found in database: '{title[:50]}'")
        return False
    
    if not recipe.uuid:
        print(f"⚠️  No UUID in database for recipe: '{title[:50]}'")
        return False
    
    # Add UUID to JSON
    recipe_data['uuid'] = str(recipe.uuid)
    
    # Write back
    with open(json_path, 'w') as f:
        json.dump(recipe_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Added UUID {recipe.uuid} to {Path(json_path).name}")
    return True


async def main():
    """Add UUIDs to all JSON files in a directory."""
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/add_uuids_to_json.py <json_file_or_directory>")
        sys.exit(1)
    
    target = Path(sys.argv[1])
    
    if target.is_file():
        files = [target]
    elif target.is_dir():
        files = list(target.glob('**/*.json'))
    else:
        print(f"❌ Not a valid file or directory: {target}")
        sys.exit(1)
    
    print(f"📂 Processing {len(files)} JSON files...")
    
    success = 0
    failed = 0
    
    for json_file in files:
        try:
            if await add_uuid_to_json(str(json_file)):
                success += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Error processing {json_file}: {e}")
            failed += 1
    
    print(f"\n📊 Results: {success} updated, {failed} skipped/failed")


if __name__ == '__main__':
    asyncio.run(main())

