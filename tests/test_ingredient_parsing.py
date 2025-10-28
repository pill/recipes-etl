"""Test suite for ingredient parsing to prevent regressions."""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from recipes.utils.local_parser import LocalRecipeParser


class TestIngredientParsing:
    """Test cases for ingredient parsing."""
    
    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return LocalRecipeParser()
    
    # Good examples that should parse correctly
    
    def test_simple_ingredient_with_unit(self, parser):
        """Test: '2 cups flour' should parse correctly."""
        result = parser._parse_ingredient_smart("2 cups flour")
        assert result is not None
        assert result.item == "flour"
        assert "2" in result.amount
        assert "cup" in result.amount.lower()
    
    def test_ingredient_with_decimal(self, parser):
        """Test: '1.5 tbsp sugar' should parse correctly."""
        result = parser._parse_ingredient_smart("1.5 tbsp sugar")
        assert result is not None
        assert result.item == "sugar"
        assert "1.5" in result.amount
    
    def test_ingredient_with_fraction(self, parser):
        """Test: '1/2 tsp salt' should parse correctly."""
        result = parser._parse_ingredient_smart("1/2 tsp salt")
        assert result is not None
        assert result.item == "salt"
        assert "1/2" in result.amount
    
    def test_reddit_format_with_parenthetical(self, parser):
        """Test Reddit format: '270 g (9.5 oz) Cake Wheat Flour'."""
        result = parser._parse_ingredient_smart("270 g (9.5 oz) Cake Wheat Flour")
        assert result is not None
        assert result.item == "Cake Wheat Flour"
        assert "270" in result.amount
        assert "g" in result.amount
    
    def test_ingredient_with_prep_note(self, parser):
        """Test: '1 cup butter, softened' should keep prep note."""
        result = parser._parse_ingredient_smart("1 cup butter, softened")
        assert result is not None
        assert "butter" in result.item.lower()
    
    def test_ingredient_without_amount(self, parser):
        """Test: 'Salt to taste' should parse correctly."""
        result = parser._parse_ingredient_smart("Salt to taste")
        assert result is not None
        assert "salt" in result.item.lower()
    
    def test_complex_ingredient_name(self, parser):
        """Test: '2 cups all-purpose flour' should parse correctly."""
        result = parser._parse_ingredient_smart("2 cups all-purpose flour")
        assert result is not None
        assert "flour" in result.item.lower()
        assert "all-purpose" in result.item.lower()
    
    # Bad patterns that should be filtered out or fixed
    
    def test_section_header_filtered(self, parser):
        """Test: Section headers should be filtered out."""
        # Headers with colons
        result = parser._parse_ingredient_smart("Waffle Dough:")
        assert result is None or result.item != "Waffle Dough:"
        
        result = parser._parse_ingredient_smart("**Buns:**")
        assert result is None or "**" not in result.item
        
        result = parser._parse_ingredient_smart("#### Broth:")
        assert result is None or "#" not in result.item
    
    def test_markdown_stripped(self, parser):
        """Test: Markdown should be stripped from ingredients."""
        result = parser._parse_ingredient_smart("**2 cups flour**")
        assert result is not None
        assert "**" not in result.item
        assert "flour" in result.item.lower()
    
    def test_instruction_verb_filtered(self, parser):
        """Test: Instructions should not be parsed as ingredients."""
        result = parser._parse_ingredient_smart("Cook pasta until al dente")
        assert result is None
        
        result = parser._parse_ingredient_smart("Mix all ingredients together")
        assert result is None
        
        result = parser._parse_ingredient_smart("Add sugar and stir well")
        assert result is None
    
    def test_just_unit_filtered(self, parser):
        """Test: Just a unit should not be an ingredient."""
        result = parser._parse_ingredient_smart("g")
        assert result is None or len(result.item) > 2
        
        result = parser._parse_ingredient_smart("ml")
        assert result is None or len(result.item) > 2
    
    def test_amount_not_in_item_field(self, parser):
        """Test: Amount should not end up in item field."""
        result = parser._parse_ingredient_smart("270 g Flour")
        assert result is not None
        # Item should not start with a number
        assert not result.item[0].isdigit()
        assert "flour" in result.item.lower()
    
    def test_stromberg_format(self, parser):
        """Test Stromberg format with amount in different field."""
        # Stromberg data comes pre-structured, but test the cleaning
        result = parser._parse_ingredient_smart("frozen corn")
        assert result is not None
        assert result.item == "frozen corn"
    
    def test_egg_notation(self, parser):
        """Test: 'x2 eggs' or '2 eggs' should parse correctly."""
        result = parser._parse_ingredient_smart("2 eggs")
        assert result is not None
        assert "egg" in result.item.lower()
        
        # x2 format is tricky - may need special handling
        result = parser._parse_ingredient_smart("x2 (100 g) eggs")
        # Should at least not crash
        assert result is not None
    
    def test_range_amounts(self, parser):
        """Test: '2-3 cups flour' should parse correctly."""
        result = parser._parse_ingredient_smart("2-3 cups flour")
        assert result is not None
        assert "flour" in result.item.lower()
        assert "2" in result.amount or "3" in result.amount


class TestIngredientExtractionFromText:
    """Test ingredient extraction from full recipe text."""
    
    @pytest.fixture
    def parser(self):
        return LocalRecipeParser()
    
    def test_extract_ingredients_with_sections(self, parser):
        """Test extracting ingredients with section headers."""
        text = """
        **Ingredients:**
        
        Waffle Dough:
        * 270 g (9.5 oz) Cake Wheat Flour
        * 125 g (4.4 oz) Unsalted Butter
        * 2 eggs
        
        Caramel Syrup:
        * 200 g Sugar
        * 50 g Butter
        
        **Instructions:**
        1. Mix ingredients
        """
        
        ingredients = parser._extract_ingredients_robust(text, text.split('\n'))
        
        # Should extract ingredients but not section headers
        ingredient_items = [ing.item for ing in ingredients]
        
        # Should have actual ingredients
        assert any('flour' in item.lower() for item in ingredient_items)
        assert any('butter' in item.lower() for item in ingredient_items)
        assert any('egg' in item.lower() for item in ingredient_items)
        assert any('sugar' in item.lower() for item in ingredient_items)
        
        # Should NOT have section headers as ingredients
        assert not any(item.endswith(':') for item in ingredient_items)
        assert not any('waffle dough:' in item.lower() for item in ingredient_items)
        assert not any('caramel syrup:' in item.lower() for item in ingredient_items)
    
    def test_stop_at_instructions(self, parser):
        """Test that parsing stops at instructions section."""
        text = """
        **Ingredients:**
        * 2 cups flour
        * 1 cup sugar
        
        **Instructions:**
        * Mix the flour and sugar
        * Bake for 30 minutes
        """
        
        ingredients = parser._extract_ingredients_robust(text, text.split('\n'))
        
        # Should have ingredients
        assert len(ingredients) >= 2
        
        # Should NOT have instructions as ingredients
        ingredient_items = [ing.item.lower() for ing in ingredients]
        assert not any('mix' in item for item in ingredient_items)
        assert not any('bake' in item for item in ingredient_items)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

