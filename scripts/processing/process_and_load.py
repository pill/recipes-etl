#!/usr/bin/env python3
"""
Process and Load Script - One command to process CSVs and load to DB

This script can:
1. Process CSV files (AI or local parsing)
2. Load JSON files to database
3. Handle large datasets like Stromberg (13,389 files)
4. Auto-chunk large operations to avoid Temporal limits

Usage:
    # Process and load Stromberg dataset (local parsing)
    python process_and_load.py stromberg --local --batch-size 1000

    # Process and load Reddit CSVs (AI parsing)
    python process_and_load.py reddit --ai --batch-size 500

    # Load existing JSON files from all of data/stage/
    python process_and_load.py load-only --batch-size 1000

    # Load JSON files from a specific folder
    python process_and_load.py load-only --folder data/stage/stromberg_data --batch-size 1000

    # Process specific CSV file
    python process_and_load.py csv data/raw/Reddit_Recipes.csv --local --batch-size 100
"""

import asyncio
import glob
import os
import sys
import argparse
from pathlib import Path
from typing import List, Optional

# Add src to path (script is now in scripts/processing/)
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from recipes.client import (
    run_recipe_batch_workflow,
    run_recipe_batch_parallel_workflow,
    run_load_recipes_workflow
)


class ProcessAndLoadManager:
    def __init__(self, batch_size: int = 500, parallel: bool = True):
        self.batch_size = batch_size
        self.parallel = parallel
        self.delay_between_batches_ms = 200 if parallel else 0

    async def process_stromberg_dataset(self, use_ai: bool = False) -> None:
        """Process the entire Stromberg dataset (13,389 files)."""
        print("🌊 Processing Stromberg Dataset")
        print("=" * 60)
        
        # Find all Stromberg CSV files
        stromberg_files = sorted(glob.glob('data/stage/stromberg_data/*.json'))
        
        if not stromberg_files:
            print("❌ No Stromberg JSON files found in data/stage/stromberg_data/")
            print("💡 Make sure you've already processed the CSV files first")
            return
        
        print(f"📊 Found {len(stromberg_files)} Stromberg JSON files")
        
        # Load directly to database (they're already processed)
        await self._load_json_files_to_db(stromberg_files, "Stromberg Dataset")

    async def process_reddit_csvs(self, use_ai: bool = False) -> None:
        """Process all Reddit CSV files."""
        print("📱 Processing Reddit Recipe CSVs")
        print("=" * 60)
        
        # Find all Reddit CSV files
        reddit_files = sorted(glob.glob('data/raw/Reddit_Recipes*.csv'))
        
        if not reddit_files:
            print("❌ No Reddit CSV files found in data/raw/")
            return
        
        print(f"📊 Found {len(reddit_files)} Reddit CSV files")
        
        total_entries = 0
        for csv_file in reddit_files:
            # Count entries in each CSV
            try:
                import pandas as pd
                df = pd.read_csv(csv_file)
                entries = len(df)
                total_entries += entries
                print(f"  📄 {os.path.basename(csv_file)}: {entries} entries")
            except Exception as e:
                print(f"  ⚠️  {os.path.basename(csv_file)}: Error counting entries - {e}")
        
        print(f"📊 Total entries to process: {total_entries}")
        print()
        
        # Process each CSV file
        for csv_file in reddit_files:
            print(f"🔄 Processing {os.path.basename(csv_file)}...")
            
            try:
                import pandas as pd
                df = pd.read_csv(csv_file)
                total_entries = len(df)
                
                # Process in batches
                entries_per_batch = min(self.batch_size, 1000)  # Cap at 1000 for processing
                batches = [(i, min(i + entries_per_batch, total_entries)) 
                          for i in range(0, total_entries, entries_per_batch)]
                
                print(f"  📦 Processing in {len(batches)} batches of ~{entries_per_batch} entries each")
                
                for batch_idx, (start, end) in enumerate(batches, 1):
                    print(f"  🔄 Batch {batch_idx}/{len(batches)}: entries {start+1}-{end}")
                    
                    if self.parallel:
                        # Use parallel workflow
                        result = await run_recipe_batch_parallel_workflow(
                            csv_file_path=csv_file,
                            start_entry=start + 1,  # 1-indexed
                            end_entry=end,
                            batch_size=min(10, entries_per_batch // 10 + 1),
                            delay_between_batches_ms=self.delay_between_batches_ms
                        )
                    else:
                        # Use sequential workflow
                        result = await run_recipe_batch_workflow(
                            csv_file_path=csv_file,
                            start_entry=start + 1,  # 1-indexed
                            end_entry=end,
                            delay_between_activities_ms=1000,
                            use_ai=use_ai
                        )
                    
                    print(f"    ✅ Batch complete: {result['successful']} processed, {result['failed']} failed")
                    
                    if batch_idx < len(batches):
                        await asyncio.sleep(1)  # Brief pause between batches
                
                print(f"  ✅ {os.path.basename(csv_file)} complete!")
                
            except Exception as e:
                print(f"  ❌ Error processing {csv_file}: {e}")
                continue
        
        print("\n🎉 All Reddit CSVs processed!")
        
        # Now load all generated JSON files
        json_files = sorted(glob.glob('data/stage/**/*.json', recursive=True))
        if json_files:
            print(f"\n📥 Loading {len(json_files)} JSON files to database...")
            await self._load_json_files_to_db(json_files, "Reddit Recipes")

    async def process_single_csv(self, csv_file: str, use_ai: bool = False) -> None:
        """Process a single CSV file."""
        if not os.path.exists(csv_file):
            print(f"❌ CSV file not found: {csv_file}")
            return
        
        print(f"📄 Processing single CSV: {os.path.basename(csv_file)}")
        print("=" * 60)
        
        try:
            import pandas as pd
            df = pd.read_csv(csv_file)
            total_entries = len(df)
            print(f"📊 Found {total_entries} entries")
            
            # Process in batches
            entries_per_batch = min(self.batch_size, 1000)
            batches = [(i, min(i + entries_per_batch, total_entries)) 
                      for i in range(0, total_entries, entries_per_batch)]
            
            print(f"📦 Processing in {len(batches)} batches of ~{entries_per_batch} entries each")
            
            for batch_idx, (start, end) in enumerate(batches, 1):
                print(f"🔄 Batch {batch_idx}/{len(batches)}: entries {start+1}-{end}")
                
                if self.parallel:
                    # Use parallel workflow
                    result = await run_recipe_batch_parallel_workflow(
                        csv_file_path=csv_file,
                        start_entry=start + 1,
                        end_entry=end,
                        batch_size=min(10, entries_per_batch // 10 + 1),
                        delay_between_batches_ms=self.delay_between_batches_ms
                    )
                else:
                    # Use sequential workflow
                    result = await run_recipe_batch_workflow(
                        csv_file_path=csv_file,
                        start_entry=start + 1,
                        end_entry=end,
                        delay_between_activities_ms=1000,
                        use_ai=use_ai
                    )
                
                print(f"  ✅ Batch complete: {result['successful']} processed, {result['failed']} failed")
                
                if batch_idx < len(batches):
                    await asyncio.sleep(1)
            
            print(f"\n✅ {os.path.basename(csv_file)} processing complete!")
            
            # Load generated JSON files
            json_files = sorted(glob.glob('data/stage/**/*.json', recursive=True))
            if json_files:
                print(f"\n📥 Loading {len(json_files)} JSON files to database...")
                await self._load_json_files_to_db(json_files, os.path.basename(csv_file))
            
        except Exception as e:
            print(f"❌ Error processing {csv_file}: {e}")

    async def load_existing_json_files(self, folder: Optional[str] = None) -> None:
        """Load all existing JSON files to database."""
        print("📥 Loading existing JSON files to database")
        print("=" * 60)
        
        if folder:
            # Load from specific folder
            search_path = os.path.join(folder, '**/*.json')
            json_files = sorted(glob.glob(search_path, recursive=True))
            print(f"📂 Searching in: {folder}")
        else:
            # Load from all of data/stage
            json_files = sorted(glob.glob('data/stage/**/*.json', recursive=True))
            print(f"📂 Searching in: data/stage/")
        
        if not json_files:
            print(f"❌ No JSON files found in {folder if folder else 'data/stage/'}")
            return
        
        print(f"📊 Found {len(json_files)} JSON files")
        dataset_name = os.path.basename(folder) if folder else "Existing JSON Files"
        await self._load_json_files_to_db(json_files, dataset_name)

    async def _load_json_files_to_db(self, json_files: List[str], dataset_name: str) -> None:
        """Load JSON files to database with chunking."""
        if not json_files:
            return
        
        # Split into chunks to avoid Temporal payload size limits
        chunk_size = 500
        chunks = [json_files[i:i + chunk_size] for i in range(0, len(json_files), chunk_size)]
        
        print(f"🔄 Splitting into {len(chunks)} database load workflows ({chunk_size} files each)")
        print(f"💡 Batch size: {self.batch_size} recipes per batch within each workflow")
        print()
        
        total_successful = 0
        total_exists = 0
        total_failed = 0
        total_processed = 0
        
        try:
            for chunk_idx, chunk in enumerate(chunks, 1):
                print(f"\n{'='*60}")
                print(f"📦 Loading chunk {chunk_idx}/{len(chunks)} ({len(chunk)} files)")
                print(f"{'='*60}\n")
                
                result = await run_load_recipes_workflow(
                    json_file_paths=chunk,
                    parallel=self.parallel,
                    batch_size=self.batch_size,
                    delay_between_batches_ms=self.delay_between_batches_ms
                )
                
                total_successful += result['successful']
                total_exists += result['alreadyExists']
                total_failed += result['failed']
                total_processed += result['totalProcessed']
                
                print(f"✅ Chunk {chunk_idx} complete: {result['successful']} loaded, {result['alreadyExists']} existed, {result['failed']} failed")
                
                # Show failed files if any
                if result['failed'] > 0 and 'results' in result:
                    failed_results = [r for r in result['results'] if not r.get('success')]
                    if failed_results:
                        print(f"  ⚠️  Failed recipes:")
                        for failed in failed_results[:10]:  # Show first 10
                            error_msg = failed.get('error', 'Unknown error')
                            file_path = failed.get('jsonFilePath', 'Unknown file')
                            # Shorten error message if too long
                            if len(error_msg) > 100:
                                error_msg = error_msg[:100] + "..."
                            print(f"    - {file_path}: {error_msg}")
                        if len(failed_results) > 10:
                            print(f"    ... and {len(failed_results) - 10} more failures")
            
            print()
            print("=" * 60)
            print(f"📈 {dataset_name} - FINAL RESULTS:")
            print("=" * 60)
            print(f"✅ Successfully loaded: {total_successful} recipes")
            print(f"⏭️  Already existed:    {total_exists} recipes")
            print(f"❌ Failed:             {total_failed} recipes")
            print(f"📊 Total processed:    {total_processed} recipes")
            print("=" * 60)
            
        except Exception as e:
            print(f"❌ Error loading recipes: {e}")
            raise


async def main():
    parser = argparse.ArgumentParser(description='Process and Load Recipe Data')
    parser.add_argument('command', choices=['stromberg', 'reddit', 'csv', 'load-only'],
                       help='Command to run')
    parser.add_argument('--csv-file', type=str, help='CSV file path (for csv command)')
    parser.add_argument('--folder', type=str, help='Specific folder to load from (for load-only command)')
    parser.add_argument('--ai', action='store_true', help='Use AI parsing (default: local)')
    parser.add_argument('--local', action='store_true', help='Use local parsing (default)')
    parser.add_argument('--batch-size', type=int, default=500, 
                       help='Batch size for database loading (default: 500)')
    parser.add_argument('--no-parallel', action='store_true', 
                       help='Disable parallel processing')
    
    args = parser.parse_args()
    
    # Determine parsing method
    use_ai = args.ai and not args.local
    if not args.ai and not args.local:
        use_ai = False  # Default to local
    
    manager = ProcessAndLoadManager(
        batch_size=args.batch_size,
        parallel=not args.no_parallel
    )
    
    print("🍳 Recipe Processing and Loading Tool")
    print("=" * 60)
    print(f"📊 Batch size: {args.batch_size}")
    print(f"🔄 Parallel: {'Yes' if not args.no_parallel else 'No'}")
    print(f"🤖 Parsing method: {'AI' if use_ai else 'Local'}")
    print()
    
    try:
        if args.command == 'stromberg':
            await manager.process_stromberg_dataset(use_ai=use_ai)
        elif args.command == 'reddit':
            await manager.process_reddit_csvs(use_ai=use_ai)
        elif args.command == 'csv':
            if not args.csv_file:
                print("❌ --csv-file required for csv command")
                return
            await manager.process_single_csv(args.csv_file, use_ai=use_ai)
        elif args.command == 'load-only':
            await manager.load_existing_json_files(folder=args.folder)
        
        print("\n🎉 All operations completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == '__main__':
    asyncio.run(main())
