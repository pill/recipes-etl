#!/usr/bin/env python3
"""Installation script for the recipes Python project."""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"🚀 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False


def create_virtual_environment():
    """Create a virtual environment."""
    venv_path = Path(__file__).parent / 'venv'
    if venv_path.exists():
        print("ℹ️  Virtual environment already exists")
        return True
    
    print("📦 Creating virtual environment...")
    return run_command("python3 -m venv venv", "Virtual environment creation")


def install_dependencies():
    """Install Python dependencies."""
    print("📦 Installing Python dependencies...")
    
    # Check if poetry is available
    try:
        subprocess.run(["poetry", "--version"], check=True, capture_output=True)
        print("📦 Using Poetry to install dependencies...")
        return run_command("poetry install", "Poetry installation")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("📦 Poetry not found, using pip with virtual environment...")
        
        # Create virtual environment first
        if not create_virtual_environment():
            return False
        
        # Install dependencies in virtual environment
        venv_pip = Path(__file__).parent / 'venv' / 'bin' / 'pip'
        return run_command(f"{venv_pip} install -r requirements.txt", "Pip installation in virtual environment")


def setup_environment():
    """Set up environment variables."""
    print("🔧 Setting up environment...")
    
    env_file = Path(__file__).parent / '.env'
    env_example = Path(__file__).parent / 'env.example'
    
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


def main():
    """Main installation function."""
    print("🚀 Installing Recipes Python project...")
    print()
    
    # Setup steps
    steps = [
        ("Environment", setup_environment),
        ("Directories", setup_directories),
        ("Dependencies", install_dependencies),
    ]
    
    for step_name, step_func in steps:
        print(f"📋 {step_name} setup...")
        try:
            success = step_func()
            if not success:
                print(f"❌ {step_name} setup failed!")
                return False
            print()
        except Exception as e:
            print(f"❌ {step_name} setup failed with error: {e}")
            return False
    
    print("🎉 Installation completed successfully!")
    print()
    print("Next steps:")
    print("1. Update your .env file with actual API keys")
    print("2. Activate the environment:")
    print("   source activate.sh")
    print("3. Test the setup:")
    print("   python test_setup.py")
    print("4. Test the CLI:")
    print("   ./recipes --help")
    print("   ./recipes test-db")
    print("5. Or use Python directly:")
    print("   python -m recipes.cli test-db")
    print("   python -m recipes.worker")
    print("   python -m recipes.client")
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
