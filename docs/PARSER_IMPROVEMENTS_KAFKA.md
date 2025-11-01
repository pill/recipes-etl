# Parser Improvements for Kafka Recipes

## Problem Statement

Random sampling of Kafka recipe JSON files revealed major data quality issues:
- **Instructions in ingredients** - "Fill a wok...", "Toss to combine...", "Sift the matcha..."
- **Multi-line ingredient blobs** - Entire ingredient lists crammed into one field
- **Section headers as ingredients** - "For the Cookies", "For the Filling"
- **Standalone notes** - "to taste", "optional", "(Serves 2)"
- **Japanese bullet points** - Not properly split on ・ character

**Impact:** 40%+ of sampled recipes had unusable ingredient lists.

## Solution Implemented

### 1. Multi-Line Ingredient Expansion (`activities.py`)

Added pre-processing to split ingredient blobs before parsing:

```python
# Split on newlines and bullet points (・)
if '\n' in item or '・' in item:
    sub_items = item.split('\n')
    for sub in sub_items:
        # Further split on Japanese bullet points
        if '・' in sub:
            mini_items = sub.split('・')
            # Create separate ingredients
```

**Example:**
```
Before: 1 item = "(Serves 2)\n\n・1/2 tbsp. matcha\n\n・2 tsp. water..."
After:  7 items = ["1/2 tbsp. matcha", "2 tsp. water", "3/4 cup milk", ...]
```

### 2. Enhanced Local Parser (`local_parser.py`)

#### A. Better Splitting in `_extract_ingredients_robust()`

- Split on newlines first (most common format)
- Split on bullet points: `* - • ・`
- Handle embedded `\n\n` patterns
- Split on Japanese bullet points within text

#### B. New Filter Method: `_filter_bad_ingredients()`

Filters out:
- **Instruction verbs**: coat, sift, strain, fill, toss, serve, mix, stir, etc.
- **Instruction phrases**: "in a ", "in the "
- **Section headers**: "For the Cookies", "For Topping"
- **Standalone notes**: "to taste", "optional", "as needed"
- **Serving sizes**: "(Serves 2)"
- **Long sentences**: Ends with period + action verbs + 6+ words

#### C. Improved `_parse_ingredient_smart()`

- Filters instruction verbs: coat, sift, strain, fill, toss
- Detects instruction-like sentences
- Skips section headers and notes

#### D. Applied Filtering to `_extract_ingredients_improved()`

- Now applies filter to line-based extraction too
- Prevents bad ingredients from fallback methods

### 3. Skip Patterns Added

**Activities.py (database load):**
- `'fill a'`, `'fill the'`
- `'toss to'`, `'toss and serve'`
- `'serve with'`, `'combine then serve'`
- `'for the '`, `'for filling'`, `'for topping'`
- `'preheat'`, `'cook '`, `'stir '`
- Standalone notes: `'to taste'`, `'optional'`, etc.
- Sentence detection: period + action verbs + length

**Local_parser.py (recipe extraction):**
- Instruction verbs: `coat`, `sift`, `strain`, `fill`, `toss`, `serve`, etc.
- Instruction phrases: `'in a '`, `'in the '`
- Section markers
- Serving sizes

## Test Coverage

Created 8 comprehensive tests:

### `test_instruction_filtering.py` (4 tests)
1. ✅ `test_instruction_patterns` - Detects "Fill a wok...", "Toss to combine..."
2. ✅ `test_valid_ingredients` - Keeps "1 cup flour", "2 eggs"
3. ✅ `test_edge_cases` - Handles "Preheat oven..."
4. ✅ `test_section_headers_and_notes` - Filters "to taste", "For the Cookies"

### `test_kafka_parsing.py` (4 tests)
1. ✅ `test_matcha_mousse_parsing` - Splits multi-line blobs, filters notes
2. ✅ `test_chicken_nanban_parsing` - Filters all instructions, returns placeholder
3. ✅ `test_section_header_filtering` - Filters "For the X" headers
4. ✅ `test_japanese_bullet_points` - Handles ・ bullet points

**All 8 tests passing!**

## Results

### Before Improvements

**Matcha Mousse:**
```
Ingredients (3):
1. "(Serves 2)\n\n・1/2 tbsp. matcha\n\n・2 tsp. water..."  ❌
2. "Sift the matcha through a fine-mesh strainer..."        ❌
3. "Strain for a smooth texture, then pour..."              ❌
```

**Sicilian Pasta:**
```
Ingredients (13):
...
10. "Fill a wok or large skillet with 3 inches..."          ❌
11. "Meanwhile, bring a pot of salted water..."              ❌
12. "In a large skillet over medium heat add..."             ❌
13. "Toss to combine then serve with ricotta salata."        ❌
```

### After Improvements

**Matcha Mousse:**
```
Ingredients (7):
1. "1/2 tbsp. matcha"         ✅
2. "2 tsp. water"             ✅
3. "3/4 cup milk"             ✅
4. "2 1/2 oz marshmallows"    ✅
5. "2 tbsp. heavy cream"      ✅
6. "whipped cream"            ✅
7. "matcha"                   ✅

Filtered out: "(Serves 2)", "Instructions", "optional" notes, 2 instruction sentences
```

**Sicilian Pasta:**
```
Ingredients (10):
1. "Vegetable Oil for deep frying"  ✅
2. "Olive Oil"                       ✅
3. "Eggplant"                        ✅
...

Filtered out: 3 instruction-like items
```

## Improvement Metrics

Testing 5 random Kafka recipes:
- **Before**: 40% had good ingredients (2/5)
- **After**: 80% have good ingredients (4/5)
- **Filtered out**: 10+ bad ingredient items across all recipes

### What Gets Filtered

✅ "Fill a wok or large skillet with 3 inches of vegetable oil over medium high heat."  
✅ "Toss to combine then serve with ricotta salata."  
✅ "Sift the matcha through a fine-mesh strainer. Add the water..."  
✅ "Coat the chicken pieces evenly with potato starch..."  
✅ "In a separate pan, combine C ingredients..."  
✅ "(Serves 2)"  
✅ "For the Cookies"  
✅ "to taste" (standalone)  
✅ "optional" (standalone)  
✅ "Instructions" (header)  

### What Gets Kept

✅ "1/2 tbsp. matcha"  
✅ "2 tsp. water"  
✅ "3/4 cup milk"  
✅ "Eggplant"  
✅ "Olive Oil"  
✅ "pork shoulder"  
✅ "Salt and pepper, to taste" (combined with ingredient)  

## Edge Cases Handled

### 1. Recipe with No Real Ingredients

When all ingredients are filtered (they were all instructions):
- Returns placeholder: "Ingredients listed in recipe text"
- Prevents validation errors
- Indicates data quality issue

### 2. Japanese Recipe Format

Properly handles:
- Bullet points: ・
- Multi-line ingredient lists
- Embedded serving sizes
- Optional markers

### 3. Section Headers

Filters headers like:
- "For the Cookies"
- "For Topping"
- "For Filling"

But keeps ingredients that happen to start with "for":
- "for frying" (has a purpose, not a section)

## Files Modified

1. **`src/recipes/workflows/activities.py`**
   - Added multi-line ingredient expansion
   - Enhanced skip patterns
   - Added sentence detection with action verbs
   - Added standalone note filtering

2. **`src/recipes/utils/local_parser.py`**
   - Improved `_extract_ingredients_robust()` with newline splitting
   - Added `_filter_bad_ingredients()` method
   - Enhanced `_parse_ingredient_smart()` with better instruction detection
   - Added filtering to `_extract_ingredients_improved()`
   - Prevented fallback to lenient extraction when filtering removes all items

3. **Tests Added**
   - `tests/unit/test_instruction_filtering.py` (4 tests)
   - `tests/unit/test_kafka_parsing.py` (4 tests)

## How to Use

### Reprocess Kafka Recipes

```bash
# Delete old Kafka recipes from database
python3 << 'EOF'
import asyncio
from recipes.database import get_pool

async def delete_kafka():
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM recipes WHERE source_url LIKE '%kafka%' OR uuid IN (SELECT uuid FROM recipes LIMIT 0)"
        )
        print(f"Deleted {result} recipes")

asyncio.run(delete_kafka())
EOF

# Reload Kafka recipes folder with improved parsing
./CMD.sh load-folder data/stage/kafka_recipes
```

### Test Individual Recipe

```bash
# Get a recipe UUID from Kafka
ls data/stage/kafka_recipes/ | head -1

# Reload it
./CMD.sh reload-recipe <uuid>

# Check results
./CMD.sh get-by-uuid <uuid>
```

## Known Limitations

1. **No Source Ingredients** - If a recipe has NO real ingredients in the source (like Chicken Nanban example), we can't fix it with parsing
2. **Complex Merged Items** - "(Optional) 1 tsp vanilla extract For the Mousse Filling" needs better upstream parsing
3. **Contextual Ingredients** - "for frying" vs "For Frying" (section header) relies on capitalization

## Future Improvements

1. **AI Parsing** - Use AI for complex/malformed recipes
2. **Better Section Detection** - ML-based section classification
3. **Ingredient Validation** - Check against known ingredient database
4. **Source Quality Scoring** - Flag low-quality source data early

## Related Documentation

- [PARSER_IMPROVEMENTS.md](./PARSER_IMPROVEMENTS.md) - General parser improvements
- [UUID_SIMPLIFICATION.md](./UUID_SIMPLIFICATION.md) - UUID generation changes
- [EGGPLANT_FIX.md](./EGGPLANT_FIX.md) - Ingredient filtering examples

