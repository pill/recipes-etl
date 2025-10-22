#!/usr/bin/env python3
"""Test script to verify Python setup."""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_imports():
    """Test that all modules can be imported."""
    try:
        from recipes.models import Recipe, Ingredient, Measurement
        from recipes.services import AIService, RecipeService
        from recipes.database import get_pool
        from recipes.config import db_config
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_models():
    """Test model creation."""
    try:
        from recipes.models import Recipe, Ingredient, Measurement
        
        # Test Recipe model
        recipe = Recipe(
            title="Test Recipe",
            description="A test recipe",
            ingredients=[],
            instructions=["Step 1", "Step 2"]
        )
        assert recipe.title == "Test Recipe"
        
        # Test Ingredient model
        ingredient = Ingredient(name="Flour", category="Baking")
        assert ingredient.name == "Flour"
        
        # Test Measurement model
        measurement = Measurement(name="Cup", unit_type="volume")
        assert measurement.name == "Cup"
        
        print("✅ Model creation successful")
        return True
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False

def test_config():
    """Test configuration loading."""
    try:
        from recipes.config import db_config, ai_config, temporal_config
        
        print(f"Database config: {db_config.host}:{db_config.port}")
        print(f"Temporal config: {temporal_config.host}:{temporal_config.port}")
        
        # Check if AI key is set (don't print it)
        if ai_config.anthropic_api_key:
            print("✅ AI configuration loaded")
        else:
            print("⚠️  AI configuration not set (ANTHROPIC_API_KEY missing)")
        
        print("✅ Configuration loading successful")
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Python setup...")
    print()
    
    tests = [
        ("Imports", test_imports),
        ("Models", test_models),
        ("Configuration", test_config),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"📋 Testing {test_name}...")
        if test_func():
            passed += 1
        print()
    
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Python setup is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the setup.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
