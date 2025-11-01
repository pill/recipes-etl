# UUID Generation Simplification

## Change Summary

**Before:** UUIDs were generated from title + ingredient fingerprint (first 5 ingredients)  
**After:** UUIDs are generated from **title only** (+ source URL when available)

## Rationale

### Problems with Ingredient-Based UUIDs

1. **Ingredient Filtering Changes** - When ingredient filtering logic improved, it would reorder or remove ingredients, causing UUID changes even though it's the same recipe
2. **Inconsistent UUIDs** - Same recipe could get different UUIDs due to minor ingredient variations
3. **Debugging Difficulty** - Hard to predict what UUID a recipe would get
4. **Unnecessary Complexity** - Ingredient fingerprinting added complexity without clear benefits

### Benefits of Title-Only UUIDs

1. **Stability** - UUID only changes if title changes (much rarer)
2. **Predictability** - Easy to predict UUID from title alone
3. **Simplicity** - No need to hash ingredients
4. **Better Deduplication** - Recipes with same title are considered duplicates, regardless of ingredient variations
5. **Faster** - No need to process ingredients for UUID generation

## Implementation

### UUID Generation Logic

```python
def generate_recipe_uuid(title: str, source_url: Optional[str] = None) -> str:
    """
    Generate a deterministic UUID for a recipe based on title and source URL.
    
    Args:
        title: Recipe title (required)
        source_url: Source URL of the recipe (optional)
    
    Returns:
        String representation of UUID
    """
    # Normalize title (lowercase, strip whitespace)
    normalized_title = title.strip().lower()
    
    # Normalize source_url
    normalized_source = source_url.strip().lower() if source_url else ''
    
    # Create content string for UUID generation
    content = f"{normalized_title}:{normalized_source}"
    
    # Generate deterministic UUID using uuid5
    return str(uuid.uuid5(RECIPE_UUID_NAMESPACE, content))
```

### Examples

**Recipe with source URL (e.g., Reddit):**
```python
generate_recipe_uuid("Sicilian Pasta with Eggplant", "reddit:t3_abc123")
# UUID based on: "sicilian pasta with eggplant:reddit:t3_abc123"
```

**Recipe without source URL (staged recipes):**
```python
generate_recipe_uuid("Sicilian Pasta with Eggplant", None)
# UUID based on: "sicilian pasta with eggplant:"
```

**Same title = same UUID:**
```python
uuid1 = generate_recipe_uuid("Chocolate Chip Cookies", None)
uuid2 = generate_recipe_uuid("Chocolate Chip Cookies", None)
# uuid1 == uuid2 ✅
```

## Migration Impact

### Existing Recipes

Existing recipes in the database are NOT automatically migrated. The old UUIDs remain valid.

### New/Reprocessed Recipes

When recipes are reprocessed:
- They will get new UUIDs based on title only
- The `reload-recipe` command will detect UUID changes
- Both old and new UUIDs can coexist in the system

### Finding UUID Changes

If you want to find recipes where UUIDs changed:

```bash
# Reload a recipe and check for UUID change warning
./CMD.sh reload-recipe 11088052-b7a5-566a-9422-9f9b85fa88cb

# Output will show:
# ⚠️  UUID changed during load!
#    Expected: 11088052-b7a5-566a-9422-9f9b85fa88cb
#    Got:      8faa4a5f-4f52-56db-92aa-fa574ed6b62c
#    This happens when recipe content (title/ingredients) changed.
```

## Modified Files

1. **`src/recipes/utils/json_processor.py`**
   - Removed ingredient fingerprinting
   - Simplified to title-only UUID generation

2. **`src/recipes/workflows/activities.py`**
   - Removed ingredient fingerprint creation for UUID
   - Set `source_url=None` for staged recipes

3. **`src/recipes/utils/uuid_utils.py`**
   - No changes (already supported title-only generation)

4. **Documentation Updates:**
   - `docs/UUID_TRACKING.md`
   - `docs/UUID_GENERATION_IMPROVEMENT.md`
   - `docs/RECIPE_RELOAD_GUIDE.md`
   - `docs/UUID_SIMPLIFICATION.md` (this file)

## Use Cases

### Deduplication

Recipes with the same title are now automatically considered duplicates:

```python
# These will have the SAME UUID
"Chocolate Chip Cookies" with ingredients: [flour, sugar, eggs, butter, chocolate chips]
"Chocolate Chip Cookies" with ingredients: [flour, sugar, eggs, butter, chocolate chips, vanilla]
```

This is **desirable** because:
- Same recipe from different sources often has minor ingredient variations
- Title is the primary identifier users recognize
- Easier to manage duplicates

### Different Recipes, Same Title

If two recipes have the same title but are actually different recipes, they will get the same UUID. Solutions:

1. **Differentiate by source URL:**
   ```python
   generate_recipe_uuid("Chocolate Chip Cookies", "source1.com")
   generate_recipe_uuid("Chocolate Chip Cookies", "source2.com")
   # Different UUIDs ✅
   ```

2. **Use descriptive titles:**
   ```python
   "Classic Chocolate Chip Cookies"
   "Vegan Chocolate Chip Cookies"
   "Gluten-Free Chocolate Chip Cookies"
   # Different UUIDs ✅
   ```

## Testing

### Verify Title-Only Generation

```bash
# Test UUID generation
python3 << EOF
from src.recipes.utils.uuid_utils import generate_recipe_uuid

# Same title, different ingredients should give same UUID
uuid1 = generate_recipe_uuid("Test Recipe", None)
uuid2 = generate_recipe_uuid("Test Recipe", None)
print(f"UUID 1: {uuid1}")
print(f"UUID 2: {uuid2}")
print(f"Match: {uuid1 == uuid2}")
EOF
```

### Reload a Recipe

```bash
# Find a recipe with old ingredient-based UUID
./CMD.sh reload-recipe <old-uuid>

# Check if UUID changed (it should if it was ingredient-based)
# New UUID will be title-only based
```

## Rollback

If you need to rollback to ingredient-based UUIDs:

1. Restore `json_processor.py` and `activities.py` from git history
2. Reprocess recipes to regenerate UUIDs with ingredient fingerprints

```bash
git checkout <commit-before-change> -- src/recipes/utils/json_processor.py
git checkout <commit-before-change> -- src/recipes/workflows/activities.py
```

## Related Documentation

- [UUID_TRACKING.md](./UUID_TRACKING.md) - Complete UUID tracking guide
- [UUID_GENERATION_IMPROVEMENT.md](./UUID_GENERATION_IMPROVEMENT.md) - UUID in JSON files
- [RECIPE_RELOAD_GUIDE.md](./RECIPE_RELOAD_GUIDE.md) - Reloading recipes with UUID changes

