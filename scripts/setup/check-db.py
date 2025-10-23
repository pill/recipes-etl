#!/usr/bin/env python3
"""Setup script for the recipes Python project."""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path (script is now in scripts/setup/)
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from recipes.database import test_connection
from recipes.config import db_config


async def setup_database():
    """Set up the database connection and test it."""
    print("🔧 Setting up database connection...")
    
    # Test connection
    success = await test_connection()
    if not success:
        print("❌ Database connection failed!")
        print("Make sure PostgreSQL is running and accessible at:")
        print(f"  Host: {db_config.host}")
        print(f"  Port: {db_config.port}")
        print(f"  Database: {db_config.database}")
        print(f"  User: {db_config.user}")
        return False
    
    print("✅ Database connection successful!")
    return True


def setup_environment():
    """Set up environment variables."""
    print("🔧 Setting up environment...")
    
    env_file = Path(__file__).parent.parent / '.env'
    env_example = Path(__file__).parent.parent / 'env.example'
    
    if not env_file.exists() and env_example.exists():
        print("📝 Creating .env file from template...")
        with open(env_example, 'r') as f:
            content = f.read()
        with open(env_file, 'w') as f:
            f.write(content)
        print("✅ .env file created!")
        print("⚠️  Please update the .env file with your actual API keys and configuration")
    else:
        print("ℹ️  .env file already exists")
    
    return True


def setup_directories():
    """Set up required directories."""
    print("🔧 Setting up directories...")
    
    directories = [
        'data/raw',
        'data/stage',
        'data/samples',
        'logs'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {directory}")
    
    return True


async def main():
    """Main setup function."""
    print("🚀 Setting up Recipes Python project...")
    print()
    
    # Setup steps
    steps = [
        ("Environment", setup_environment),
        ("Directories", setup_directories),
        ("Database", setup_database),
    ]
    
    for step_name, step_func in steps:
        print(f"📋 {step_name} setup...")
        try:
            if asyncio.iscoroutinefunction(step_func):
                success = await step_func()
            else:
                success = step_func()
            
            if not success:
                print(f"❌ {step_name} setup failed!")
                return False
            
            print()
        except Exception as e:
            print(f"❌ {step_name} setup failed with error: {e}")
            return False
    
    print("🎉 Setup completed successfully!")
    print()
    print("Next steps:")
    print("1. Update your .env file with actual API keys")
    print("2. Start the Temporal worker: python -m recipes.worker")
    print("3. Test the CLI: python -m recipes.cli test-db")
    print("4. Process some recipes: python -m recipes.cli process-recipe <csv_file> <entry_number>")
    
    return True


if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
