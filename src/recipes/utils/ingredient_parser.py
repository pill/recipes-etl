"""Utility to parse ingredient strings and convert to database format."""

import re
from typing import Dict, Optional, Tuple
from fractions import Fraction


class IngredientParser:
    """Parser for ingredient amounts and measurements."""
    
    # Common measurement mappings (string -> (canonical_name, abbreviation, unit_type))
    MEASUREMENT_MAP = {
        # Volume
        'cup': ('cup', 'c', 'volume'),
        'cups': ('cup', 'c', 'volume'),
        'c': ('cup', 'c', 'volume'),
        'tablespoon': ('tablespoon', 'tbsp', 'volume'),
        'tablespoons': ('tablespoon', 'tbsp', 'volume'),
        'tbsp': ('tablespoon', 'tbsp', 'volume'),
        'tbs': ('tablespoon', 'tbsp', 'volume'),
        'teaspoon': ('teaspoon', 'tsp', 'volume'),
        'teaspoons': ('teaspoon', 'tsp', 'volume'),
        'tsp': ('teaspoon', 'tsp', 'volume'),
        'liter': ('liter', 'L', 'volume'),
        'liters': ('liter', 'L', 'volume'),
        'l': ('liter', 'L', 'volume'),
        'milliliter': ('milliliter', 'mL', 'volume'),
        'milliliters': ('milliliter', 'mL', 'volume'),
        'ml': ('milliliter', 'mL', 'volume'),
        'pint': ('pint', 'pt', 'volume'),
        'pints': ('pint', 'pt', 'volume'),
        'quart': ('quart', 'qt', 'volume'),
        'quarts': ('quart', 'qt', 'volume'),
        'gallon': ('gallon', 'gal', 'volume'),
        'gallons': ('gallon', 'gal', 'volume'),
        
        # Weight
        'pound': ('pound', 'lb', 'weight'),
        'pounds': ('pound', 'lb', 'weight'),
        'lb': ('pound', 'lb', 'weight'),
        'lbs': ('pound', 'lb', 'weight'),
        'ounce': ('ounce', 'oz', 'weight'),
        'ounces': ('ounce', 'oz', 'weight'),
        'oz': ('ounce', 'oz', 'weight'),
        'gram': ('gram', 'g', 'weight'),
        'grams': ('gram', 'g', 'weight'),
        'g': ('gram', 'g', 'weight'),
        'gr': ('gram', 'g', 'weight'),
        'kilogram': ('kilogram', 'kg', 'weight'),
        'kilograms': ('kilogram', 'kg', 'weight'),
        'kg': ('kilogram', 'kg', 'weight'),
        
        # Count
        'piece': ('piece', 'pc', 'count'),
        'pieces': ('piece', 'pc', 'count'),
        'pc': ('piece', 'pc', 'count'),
        'pcs': ('piece', 'pc', 'count'),
        'whole': ('whole', 'whole', 'count'),
        'item': ('item', 'item', 'count'),
        'items': ('item', 'item', 'count'),
        
        # Other
        'pinch': ('pinch', 'pinch', 'other'),
        'pinches': ('pinch', 'pinch', 'other'),
        'dash': ('dash', 'dash', 'other'),
        'dashes': ('dash', 'dash', 'other'),
        'to taste': ('to taste', 'to taste', 'other'),
        'as needed': ('as needed', 'as needed', 'other'),
    }
    
    def parse_amount_string(self, amount_str: str) -> Tuple[Optional[float], Optional[str], Optional[str]]:
        """
        Parse an amount string into (amount, measurement, unit_type).
        
        Examples:
            "1 cup" -> (1.0, "cup", "volume")
            "1/2 tbsp" -> (0.5, "tablespoon", "volume")
            "2-3 cups" -> (2.5, "cup", "volume")  # Takes average
            "200g" -> (200.0, "gram", "weight")
            "to taste" -> (None, "to taste", "other")
        """
        if not amount_str or not amount_str.strip():
            return (None, None, None)
        
        amount_str = amount_str.strip().lower()
        
        # Handle "to taste", "as needed", etc.
        if amount_str in ['to taste', 'as needed', 'taste', 'needed']:
            return (None, 'to taste', 'other')
        
        # Try to extract number and unit
        # Pattern: handle formats like "1", "1/2", "1 1/2", "2-3", "200g"
        pattern = r'^(\d+(?:\.\d+)?)?(?:\s+(\d+)\/(\d+))?(?:\s*-\s*(\d+(?:\.\d+)?))?\s*([a-zA-Z]+)?'
        match = re.match(pattern, amount_str)
        
        if not match:
            # Can't parse, return None
            return (None, None, None)
        
        whole, frac_num, frac_denom, range_end, unit_str = match.groups()
        
        # Calculate amount
        amount = None
        
        if whole or frac_num:
            try:
                if frac_num and frac_denom:
                    # Fraction like "1/2" or "1 1/2"
                    whole_part = float(whole) if whole else 0
                    frac_part = float(Fraction(int(frac_num), int(frac_denom)))
                    amount = whole_part + frac_part
                elif range_end:
                    # Range like "2-3"
                    start = float(whole) if whole else 0
                    end = float(range_end)
                    amount = (start + end) / 2  # Take average
                else:
                    # Just a number
                    amount = float(whole) if whole else None
            except (ValueError, ZeroDivisionError):
                amount = None
        
        # Find measurement
        measurement = None
        unit_type = None
        
        if unit_str:
            unit_str = unit_str.strip()
            if unit_str in self.MEASUREMENT_MAP:
                measurement, _, unit_type = self.MEASUREMENT_MAP[unit_str]
        
        return (amount, measurement, unit_type)
    
    def parse_ingredient_item(self, item_str: str) -> str:
        """
        Clean up ingredient name.
        Remove quantities, measurements, and common prep instructions at the start.
        """
        if not item_str:
            return ""
        
        # Remove common prep instructions in parentheses at the end
        item_str = re.sub(r'\([^)]*\)$', '', item_str)
        
        # Only remove leading numbers followed by measurements (not just any word)
        # Match patterns like: "200 g ", "1.5 cup ", "2 tbsp "
        # But NOT single letters or short words that might be ingredient names
        common_units = r'(?:cups?|c\.|tbsp?|tsp?|tablespoons?|teaspoons?|oz|ounces?|lbs?|pounds?|g|grams?|kg|ml|l|liters?|pieces?|pkg|packages?|cans?|jars?|bottles?)'
        item_str = re.sub(rf'^\d+(?:\.\d+)?(?:/\d+)?\s*{common_units}\s+', '', item_str, flags=re.IGNORECASE)
        
        # Clean up whitespace
        item_str = ' '.join(item_str.split())
        
        return item_str.strip()


_parser_instance = None


def get_ingredient_parser() -> IngredientParser:
    """Get singleton ingredient parser instance."""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = IngredientParser()
    return _parser_instance

