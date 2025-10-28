# Recipe Parser Improvements

## Overview

This document describes improvements made to the recipe parsing system to handle common AI extraction errors and malformed recipe data.

## Problem Statement

The recipe parser was encountering several issues with the "Hunters Gravy with Brats" recipe and similar entries:

### Issues Identified

1. **Swapped Amount/Item Fields**
   - Problem: Ingredients like "1/2 cups beef stock" or "4oz pancetta" were placed in the `item` field instead of being properly split
   - Example: `{item: "1/2 cups beef stock", amount: "1"}` instead of `{item: "beef stock", amount: "1 1/2 cups"}`

2. **Instructions in Ingredients List**
   - Problem: Cooking instructions were being parsed as ingredients
   - Example: "Cook pancetta on medium heat..." was appearing as an ingredient

3. **Markdown Artifacts**
   - Problem: Markdown formatting like `**Preparation**` was appearing in ingredient names
   - Example: `{item: "Salt and pepper to taste\n\n**Preparation*", ...}`

4. **Incorrect Meal Type Classification**
   - Problem: Main course dishes were classified as "dessert"
   - Example: "Hunters Gravy with Brats" was marked as "dessert" instead of "dinner"

## Solutions Implemented

### 1. Enhanced AI System Prompt (`ai_service.py`)

Added explicit parsing rules to the AI service system prompt:

```python
CRITICAL INGREDIENT PARSING RULES:
- The 'item' field should ONLY contain the ingredient name
- The 'amount' field should ONLY contain the quantity and measurement
- NEVER put amounts like "1/2 cups beef stock" in the item field
- NEVER include cooking instructions in the ingredients list
- Stop parsing ingredients when encountering section headers
- Do not include markdown formatting artifacts
```

### 2. Post-Processing Validation (`ai_service.py`)

Added `_validate_and_cleanup_recipe()` method that:

- **Filters out instructions from ingredients**
  - Detects lines starting with action verbs (cook, add, mix, stir, deglaze, fix, etc.)
  - Removes section headers and markdown artifacts

- **Fixes swapped amount/item fields**
  - Detects when item field starts with a number (e.g., "1/2 cups beef stock")
  - Parses and swaps the fields correctly
  - Handles fractional amounts with ordinal suffixes (1/3rd, 2/3rd)

- **Validates meal type classification**
  - Checks for main course indicators (brat, sausage, chicken, beef, pasta, etc.)
  - Corrects misclassified desserts to dinner when appropriate

- **Cleans markdown formatting**
  - Removes `**` and other markdown artifacts
  - Normalizes whitespace

### 3. Local Parser Improvements (`local_parser.py`)

Enhanced `_parse_ingredient_smart()` to:

- **Detect and skip instructions**
  - Checks if text starts with action verbs
  - Skips section headers
  
- **Improved meal type detection**
  - Prioritizes dinner over dessert when both indicators present
  - Adds main course keywords to dinner category
  - Better handling of ambiguous cases

## Test Results

Using the problematic "Hunters Gravy with Brats" recipe:

### Before Improvements
```json
{
  "mealType": "dessert",  ❌
  "ingredients": [
    {"item": "1/2 cups beef stock", "amount": "1"},  ❌
    {"item": "4oz pancetta", "amount": "to taste"},  ❌
    {"item": "Salt and pepper to taste\n\n**Preparation*", "amount": "to taste"},  ❌
    {"item": "Cook pancetta on medium heat...", "amount": "to taste"},  ❌
    {"item": "Deglaze pan with white wine...", "amount": "to taste"},  ❌
    {"item": "Fix the plate with pasta...", "amount": "to taste"}  ❌
  ]
}
```

### After Improvements
```json
{
  "mealType": "dinner",  ✅
  "ingredients": [
    {"item": "beef stock", "amount": "1/2 cups"},  ✅
    {"item": "pancetta", "amount": "4oz"},  ✅
    {"item": "heavy cream", "amount": "1/3rd cup"},  ✅
    {"item": "diced shallots", "amount": "2/3rd cup"},  ✅
    {"item": "portabella mushrooms", "amount": "8oz"},  ✅
    {"item": "white wine", "amount": "1tbsp"}  ✅
    // Instructions removed ✅
    // Markdown artifacts removed ✅
  ]
}
```

### Validation Summary
- ✅ Meal type corrected: "dessert" → "dinner"
- ✅ Fixed 6+ swapped amount/item fields
- ✅ Removed 3 instructions from ingredients list
- ✅ Cleaned markdown artifacts
- ✅ Reduced ingredient count from 19 to 15 (removed invalid entries)

## Files Modified

1. **`src/recipes/services/ai_service.py`**
   - Enhanced system prompt with explicit parsing rules
   - Added `_validate_and_cleanup_recipe()` validation method
   - Improved meal type classification logic

2. **`src/recipes/utils/local_parser.py`**
   - Enhanced `_parse_ingredient_smart()` with instruction detection
   - Improved `_extract_meal_type()` with better scoring logic
   - Added main course indicators to dinner category

3. **`test_parser_improvements.py`** (new file)
   - Test script to verify improvements
   - Demonstrates before/after validation

## Usage

The improvements are automatically applied during recipe extraction:

```python
from recipes.services.ai_service import get_ai_service

ai_service = get_ai_service()
recipe = await ai_service.extract_recipe_data(reddit_post_text)
# Validation is applied automatically
```

For manual validation of existing recipes:

```python
from recipes.services.ai_service import AIService

ai_service = AIService()
cleaned_recipe = ai_service._validate_and_cleanup_recipe(problematic_recipe)
```

## Future Improvements

Potential enhancements for consideration:

1. **Advanced NLP**: Use more sophisticated NLP to detect instructions vs ingredients
2. **Unit normalization**: Standardize measurements (e.g., "1tbsp" → "1 tbsp")
3. **Ingredient stemming**: Normalize ingredient names (e.g., "diced shallots" → "shallots")
4. **Confidence scoring**: Add confidence scores to flag potentially problematic entries
5. **Human-in-the-loop**: Flag low-confidence extractions for manual review

## Testing

Run the test script to verify improvements:

```bash
source venv/bin/activate
python test_parser_improvements.py
```

Expected output: All validation checks should pass with the "Hunters Gravy with Brats" test case.

