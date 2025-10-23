#!/usr/bin/env python3
"""Script to load all JSON files from data/stage into the database."""

import asyncio
import glob
import sys
from pathlib import Path

# Add src to path (script is now in scripts/processing/)
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from recipes.client import run_load_recipes_workflow


async def main():
    """Load all JSON files into the database."""
    # Get all JSON files from stage directory and subdirectories
    json_files = sorted(glob.glob('data/stage/**/*.json', recursive=True))
    
    # If no files in subdirectories, check root stage directory
    if not json_files:
        json_files = sorted(glob.glob('data/stage/*.json'))
    
    if not json_files:
        print("❌ No JSON files found in data/stage/")
        return
    
    print(f"📊 Found {len(json_files)} JSON files to load")
    
    # Split into chunks to avoid Temporal payload size limits
    # Process max 500 files per workflow
    chunk_size = 500
    chunks = [json_files[i:i + chunk_size] for i in range(0, len(json_files), chunk_size)]
    
    print(f"🔄 Splitting into {len(chunks)} workflows ({chunk_size} files each)")
    print(f"💡 Batch size: 5 recipes per batch within each workflow")
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
                batch_size=5,  # Moderate batch size
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

