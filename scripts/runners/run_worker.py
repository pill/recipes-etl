#!/usr/bin/env python3
"""Script to run the Temporal worker."""

import asyncio
import sys
from pathlib import Path

# Add src to path (script is now in scripts/runners/)
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from recipes.worker import main


if __name__ == '__main__':
    print("🚀 Starting Temporal worker...")
    asyncio.run(main())
