#!/usr/bin/env python3
"""Script to load JSON files from a specific folder into the database."""

import asyncio
import glob
import sys
from pathlib import Path

# Add src to path (script is now in scripts/processing/)
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from recipes.client import run_load_recipes_workflow


async def main():
    """Load JSON files from specified folder into the database."""
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/processing/load_folder_to_db.py <folder_path>")
        print()
        print("Examples:")
        print("  python3 scripts/processing/load_folder_to_db.py data/stage/stromberg_data")
        print("  python3 scripts/processing/load_folder_to_db.py data/stage/2025-10-14/stromberg_data")
        print("  python3 scripts/processing/load_folder_to_db.py data/stage/Reddit_Recipes")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    
    # Validate folder exists
    if not Path(folder_path).exists():
        print(f"❌ Folder not found: {folder_path}")
        sys.exit(1)
    
    if not Path(folder_path).is_dir():
        print(f"❌ Path is not a directory: {folder_path}")
        sys.exit(1)
    
    # Get all JSON files from specified folder and subdirectories
    json_files = sorted(glob.glob(f'{folder_path}/**/*.json', recursive=True))
    
    if not json_files:
        print(f"❌ No JSON files found in {folder_path}")
        sys.exit(1)
    
    print(f"📂 Loading from: {folder_path}")
    print(f"📊 Found {len(json_files)} JSON files to load")
    
    # Split into chunks to avoid Temporal payload size limits
    # Process max 500 files per workflow
    chunk_size = 500
    chunks = [json_files[i:i + chunk_size] for i in range(0, len(json_files), chunk_size)]
    
    print(f"🔄 Splitting into {len(chunks)} workflows ({chunk_size} files each)")
    print(f"💡 Batch size: 20 recipes per batch within each workflow")
    print()
    
    total_successful = 0
    total_exists = 0
    total_failed = 0
    total_processed = 0
    
    try:
        for chunk_idx, chunk in enumerate(chunks, 1):
            print(f"\n{'='*60}")
            print(f"📦 Processing chunk {chunk_idx}/{len(chunks)} ({len(chunk)} files)")
            print(f"{'='*60}\n")
            
            result = await run_load_recipes_workflow(
                json_file_paths=chunk,
                parallel=True,
                batch_size=20,  # Moderate batch size
                delay_between_batches_ms=200  # Pause between batches
            )
            
            total_successful += result['successful']
            total_exists += result['alreadyExists']
            total_failed += result['failed']
            total_processed += result['totalProcessed']
            
            print(f"✅ Chunk {chunk_idx} complete: {result['successful']} loaded, {result['alreadyExists']} existed, {result['failed']} failed")
        
        print()
        print("=" * 60)
        print("📈 FINAL RESULTS:")
        print("=" * 60)
        print(f"✅ Successfully loaded: {total_successful} recipes")
        print(f"⏭️  Already existed:    {total_exists} recipes")
        print(f"❌ Failed:             {total_failed} recipes")
        print(f"📊 Total processed:    {total_processed} recipes")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error loading recipes: {e}")
        raise


if __name__ == '__main__':
    asyncio.run(main())

