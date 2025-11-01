# Eggplant Ingredient Parsing Fix

## Problem

Recipe `11088052-b7a5-566a-9422-9f9b85fa88cb` (Sicilian Casarecce alla Norma Pasta) from the `kafka_recipes` folder was missing the eggplant ingredient due to incorrect parsing.

### Root Cause

The ingredient parsing logic in `LocalRecipeParser._parse_ingredient_smart()` was treating capitalized ingredient names as measurement units.

**Original ingredient in CSV:**
```
* 1 Eggplant cut into cubes
```

**Incorrectly parsed as:**
- `item`: "cut into cubes"
- `amount`: "1 Eggplant"
- `notes`: null

**Should have been:**
- `item`: "Eggplant"
- `amount`: "1"
- `notes`: "cut into cubes"

### Why This Happened

The regex pattern `r'^([\d/\-\.]+)\s+([a-zA-Z]+)\s+(.+)$'` matched the ingredient as:
1. Group 1 (amount): `1`
2. Group 2 (unit): `Eggplant`
3. Group 3 (item): `cut into cubes`

The parser assumed Group 2 was a measurement unit (like "cup" or "tbsp") and combined it with Group 1 to form the amount string.

## Solutions Implemented

### 1. Fixed the Existing JSON File

Manually corrected `/Users/pavery/dev/recipes-etl/data/stage/kafka_recipes/11088052-b7a5-566a-9422-9f9b85fa88cb.json`:

**Fixed ingredients:**
- ✅ Eggplant: item="Eggplant", amount="1", notes="cut into cubes"
- ✅ Garlic Cloves: item="Garlic Cloves", amount="2", notes="minced"
- ✅ Spanish Onion: item="Spanish Onion", amount="1", notes="finely chopped"
- ✅ Ricotta Salata: Added (was missing entirely)
- ✅ Removed instruction lines that were incorrectly included as ingredients

### 2. Enhanced Local Parser

Updated `src/recipes/utils/local_parser.py` in the `_parse_ingredient_smart()` method to:

1. Detect when the second word is a capitalized ingredient name (not a standard unit)
2. Check against a comprehensive list of standard measurement units
3. If the word is capitalized AND not a standard unit, treat it as the ingredient name
4. Extract prep notes from the third group

**Code change:**
```python
# Check if "unit" is actually an ingredient name (capitalized, not a standard unit)
unit_lower = unit.strip().lower()
standard_units = ['cup', 'cups', 'c', 'tbsp', 'tsp', ...]

if unit_lower not in standard_units and unit[0].isupper():
    # This is likely an ingredient name, not a unit
    amount_str = amount.strip()
    item_str = unit.strip()
    notes = item.strip() if item.strip() else None
    return RecipeIngredientSchema(item=item_str, amount=amount_str, notes=notes)
```

### 3. Enhanced AI Service Parser

Updated `src/recipes/services/ai_service.py` in the `_validate_and_cleanup_recipe()` method to handle similar field-swapping issues when AI parsing is used.

### 4. Added Tests

Created comprehensive test suite in `tests/unit/test_sicilian_pasta_recipe.py`:
- ✅ Tests individual ingredient patterns (eggplant, garlic, onion)
- ✅ Tests full recipe parsing end-to-end
- ✅ Verifies eggplant is correctly extracted with proper item/amount/notes
- ✅ Ensures standard units still work correctly

## Impact

This fix prevents similar parsing errors for ingredients like:
- "1 Eggplant cut into cubes"
- "2 Garlic cloves minced"
- "1 Spanish Onion finely chopped"
- "3 Tomatoes diced"
- Any pattern where: `[number] [CapitalizedIngredient] [prep notes]`

## Testing

All unit tests pass (26/26), with only one pre-existing test failure unrelated to this fix.

```bash
pytest tests/unit/test_sicilian_pasta_recipe.py -v
# ✅ PASSED test_full_recipe_parsing
# ✅ PASSED test_individual_ingredient_patterns
```

## Files Modified

1. `data/stage/kafka_recipes/11088052-b7a5-566a-9422-9f9b85fa88cb.json` - Fixed existing data
2. `src/recipes/utils/local_parser.py` - Enhanced ingredient parsing logic
3. `src/recipes/services/ai_service.py` - Enhanced field-swap detection
4. `tests/unit/test_sicilian_pasta_recipe.py` - Added comprehensive tests
5. `docs/EGGPLANT_FIX.md` - This documentation

