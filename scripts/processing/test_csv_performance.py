#!/usr/bin/env python3
"""Test CSV parser performance on large files."""

import asyncio
import time
import sys
from pathlib import Path

# Add src to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from recipes.utils.csv_parser import CSVParser


async def test_stromberg_performance():
    """Test performance on Stromberg dataset."""
    csv_file = 'data/raw/stromberg_data.csv'
    
    print("🧪 Testing CSV Parser Performance on Stromberg Dataset (2.2GB)\n")
    print("=" * 70)
    
    parser = CSVParser()
    
    # Test 1: Single entry (beginning)
    print("\n📊 Test 1: Fetch entry #1 (beginning)")
    start = time.time()
    entry = await parser.get_entry(csv_file, 1)
    elapsed = time.time() - start
    print(f"   ⏱️  Time: {elapsed:.3f}s")
    print(f"   ✅ Recipe: {entry['title'][:50] if entry else 'None'}...")
    
    # Test 2: Single entry (middle)
    print("\n📊 Test 2: Fetch entry #1000 (middle)")
    start = time.time()
    entry = await parser.get_entry(csv_file, 1000)
    elapsed = time.time() - start
    print(f"   ⏱️  Time: {elapsed:.3f}s")
    print(f"   ✅ Recipe: {entry['title'][:50] if entry else 'None'}...")
    
    # Test 3: Batch of 10 entries
    print("\n📊 Test 3: Fetch batch of 10 entries (1-10)")
    start = time.time()
    batch = await parser.get_entries_batch(csv_file, 1, 10)
    elapsed = time.time() - start
    print(f"   ⏱️  Time: {elapsed:.3f}s")
    print(f"   ✅ Retrieved: {len(batch)} recipes")
    
    # Test 4: Count entries
    print("\n📊 Test 4: Count total entries")
    start = time.time()
    count = await parser.count_entries(csv_file)
    elapsed = time.time() - start
    print(f"   ⏱️  Time: {elapsed:.3f}s")
    print(f"   ✅ Total recipes: {count:,}")
    
    print("\n" + "=" * 70)
    print("✅ All tests complete!")
    print("\n💡 Key Improvements:")
    print("   • Streams file line-by-line (no 2.2GB memory load)")
    print("   • Caches encoding detection")
    print("   • Only parses requested rows")
    print("   • Batch fetching for multiple consecutive entries")


if __name__ == '__main__':
    asyncio.run(test_stromberg_performance())

