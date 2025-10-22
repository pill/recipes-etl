#!/usr/bin/env python3
"""Script runner for common recipes operations."""

import sys
import subprocess
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"🚀 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False


def main():
    """Main script runner."""
    if len(sys.argv) < 2:
        print("Usage: python scripts.py <command>")
        print("Available commands:")
        print("  setup          - Run project setup")
        print("  test-db        - Test database connection")
        print("  test-ai        - Test AI service")
        print("  worker         - Start Temporal worker")
        print("  client         - Run Temporal client")
        print("  test           - Run tests")
        print("  lint           - Run linting")
        print("  format         - Format code")
        return
    
    command = sys.argv[1]
    
    # Add src to Python path
    src_path = str(Path(__file__).parent / 'src')
    
    if command == "setup":
        run_command(f"PYTHONPATH={src_path} python scripts/setup.py", "Project setup")
    
    elif command == "test-db":
        run_command(f"PYTHONPATH={src_path} python -m recipes.cli test-db", "Database connection test")
    
    elif command == "test-ai":
        run_command(f"PYTHONPATH={src_path} python -m recipes.cli test-ai", "AI service test")
    
    elif command == "worker":
        run_command(f"PYTHONPATH={src_path} python -m recipes.worker", "Start Temporal worker")
    
    elif command == "client":
        if len(sys.argv) < 6:
            print("Usage: python scripts.py client <workflow_type> <csv_file> <start> <end> [options]")
            return
        args = " ".join(sys.argv[2:])
        run_command(f"PYTHONPATH={src_path} python -m recipes.client {args}", "Run Temporal client")
    
    elif command == "test":
        run_command("pytest tests/ -v", "Run tests")
    
    elif command == "lint":
        run_command("ruff src/ tests/", "Run linting")
    
    elif command == "format":
        run_command("black src/ tests/", "Format code")
    
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
