# Data Loading Fixes

## Overview
This document describes the fixes applied to resolve validation errors and failures during recipe data loading from staged JSON files.

## Issues Fixed

### 1. Stromberg Data Validation Errors

**Problem:**
- `cookTime` field was an integer (e.g., 240) but RecipeSchema expected a string
- `difficulty` field was capitalized (e.g., "Easy") but Recipe model expected lowercase ('easy', 'medium', 'hard')
- `mealType` field had invalid values (e.g., "Soup", "Side dish") not in the allowed set

**Solution:**
Added data normalization in `src/recipes/workflows/activities.py`:
- Convert integer time values to strings with "minutes" suffix
- Normalize difficulty to lowercase and validate against allowed values
- Map common meal type variations to valid values with fallback to None

**Files Modified:**
- `src/recipes/workflows/activities.py` (lines 313-358)

### 2. Reddit Recipe Failures

**Problem:**
- Malformed ingredients containing instructions, HTML entities, and formatting text
- RecipeService.create() returning None due to various issues

**Solution:**

#### a) Improved Ingredient Filtering
Added pattern-based filtering to skip malformed ingredients in `src/recipes/workflows/activities.py`:
- Skip ingredients containing instruction verbs (e.g., "preheat the oven", "blend everything")
- Skip ingredients with Reddit formatting artifacts (e.g., "&amp;x200b", "**[")
- Skip ingredients that are only formatting characters
- Clean HTML entities from ingredient names

**Files Modified:**
- `src/recipes/workflows/activities.py` (lines 381-407, 413-427)

#### b) Enhanced Error Handling and Logging
Improved error messages and handling in `src/recipes/services/recipe_service.py`:
- Added detailed exception logging with tracebacks
- Added specific handling for UUID duplicate key violations
- Better error messages to identify root cause of failures

**Files Modified:**
- `src/recipes/services/recipe_service.py` (lines 62-75, 91-95)

#### c) Better UUID Generation for Staged Recipes
Recipes without source URLs now generate more unique UUIDs using ingredient fingerprints:
- Create MD5 hash from first 5 ingredients
- Use format "staged:{hash}" as source_url for UUID generation
- Prevents UUID collisions between similar recipes

**Files Modified:**
- `src/recipes/workflows/activities.py` (lines 485-513)

#### d) Pre-validation
Added validation checks before attempting to create recipes:
- Check for empty/invalid titles
- Warn about missing ingredients or instructions
- Better error reporting for debugging

**Files Modified:**
- `src/recipes/workflows/activities.py` (lines 515-527)

## Test Results

After applying fixes:
- Basic model tests: **5/5 passed** ✅
- Ingredient parsing tests: **16/17 passed** ✅
  - 1 pre-existing failure unrelated to these changes

## Expected Impact

With these fixes, the data loading should now:
1. ✅ Handle Stromberg data format validation errors
2. ✅ Skip malformed Reddit ingredients instead of failing
3. ✅ Provide better error messages for debugging remaining issues
4. ✅ Reduce UUID collision errors for staged recipes
5. ✅ Successfully load most recipes that were previously failing

## Failed Recipe Categories

Recipes may still fail for legitimate reasons:
- Empty or invalid titles
- Completely malformed data structure
- Database constraint violations (other than UUID)
- Network/connection issues

## Usage

To retry loading the failed recipes after applying these fixes:

```bash
# Reload specific folder
python3 scripts/processing/load_folder_to_db.py data/stage/2025-10-14/stromberg_data
python3 scripts/processing/load_folder_to_db.py data/stage/Reddit_Recipes

# Or reload all staged data
python3 scripts/processing/load_folder_to_db.py data/stage/
```

## Related Documentation

- [UUID Implementation Summary](UUID_IMPLEMENTATION_SUMMARY.md)
- [Migration Guide](MIGRATION_GUIDE.md)
- [Pipeline Example](PIPELINE_EXAMPLE.md)

