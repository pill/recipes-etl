# UUID in JSON Files - Explained

## Quick Answer

**UUIDs ARE NOW in the JSON files!** They're generated deterministically during JSON creation, not during database insertion.

This is more efficient and makes UUIDs available immediately.

---

## Architecture

### Current Flow (Updated)

```
1. Source Data (CSV/Reddit/Kafka)
   ↓
2. Parse & Extract
   ↓
3. Generate UUID deterministically ← UUID created here!
   ↓
4. Save as JSON with UUID in data/stage/
   ↓
5. Load JSON to database
   ↓
6. Recipe stored with same UUID from JSON
```

### What Each File Contains

**JSON file** (`data/stage/kafka_recipes/a1b2c3d4-e5f6-7890-abcd-ef1234567890.json`):
```json
{
  "title": "Crispy Yurinchi Chicken Breast",
  "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "description": "...",
  "ingredients": [...],
  "instructions": [...]
}
```
✅ Has `uuid` field (generated at JSON creation time)  
✅ Filename is the UUID (easy to find and reference)

**Database record** (`recipes` table):
```sql
uuid: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'  ← Generated here
id: 123
title: "Crispy Yurinchi Chicken Breast"
created_at: '2025-01-15 10:30:00'
```
✅ Has `uuid` field

---

## Why UUIDs ARE in JSON Files

### 1. **Deterministic Generation**
- UUIDs are generated from recipe data (title + ingredients)
- Same recipe always gets the same UUID
- No randomness, fully reproducible

### 2. **Early Deduplication**
- Can check for duplicates before database insertion
- Faster lookups using UUID index
- Reduces database round-trips

### 3. **Easy File Management**
- Filename is the UUID (e.g., `a1b2c3d4-e5f6-7890-abcd-ef1234567890.json`)
- Can find recipe files directly by UUID
- No need to search through numbered files

### 4. **Data Lineage**
- Track recipe from source → JSON → Database
- Consistent identifier across all stages
- Better audit trail

---

## How UUIDs are Generated in JSON

**File**: `src/recipes/utils/json_processor.py`

When saving a recipe to JSON, the UUID is automatically generated:

```python
# Generate deterministic UUID from ingredients
ingredient_fingerprint = '|'.join([
    ing.item[:50] for ing in recipe_data.ingredients[:5]
])
fingerprint_hash = hashlib.md5(ingredient_fingerprint.encode()).hexdigest()[:8]
source_url = f"staged:{fingerprint_hash}"

# Generate UUID using same logic as database
uuid = generate_recipe_uuid(recipe_data.title, source_url)
recipe_dict['uuid'] = uuid
```

**When it runs**: Every time a recipe JSON is created from:
- Kafka consumer processing
- CSV processing (AI or local)
- Reddit scraping
- Any workflow that creates staged JSON files

**No manual steps needed** - it's automatic!

---

## Example Workflow with UUIDs

### Before (without UUID in JSON):
```bash
# 1. Load from Kafka to JSON (no UUID)
python3 scripts/processing/kafka_consumer.py

# 2. Load JSON to database (generates UUID in DB)
python3 scripts/processing/load_folder_to_db.py data/stage/kafka_recipes/

# 3. JSON files don't have UUIDs
cat data/stage/kafka_recipes/entry_123.json
# → No 'uuid' field

# 4. Query database to get UUID
SELECT uuid FROM recipes WHERE title = '...';
```

### After (with UUID in JSON):
```bash
# 1. Load from Kafka to JSON (no UUID)
python3 scripts/processing/kafka_consumer.py

# 2. Load JSON to database (generates UUID, writes back to JSON)
python3 scripts/processing/load_folder_to_db.py data/stage/kafka_recipes/

# 3. JSON files now have UUID
cat data/stage/kafka_recipes/entry_123.json
# → Has 'uuid' field!

# 4. Use UUID directly from JSON
cat entry_123.json | jq -r '.uuid'
```

---

## Benefits of Having UUID in JSON

### 1. **Direct Reference**
```python
# Without UUID in JSON
json_data = load_json()
recipe = db.get_by_title(json_data['title'])  # Slow lookup

# With UUID in JSON
json_data = load_json()
recipe = db.get_by_uuid(json_data['uuid'])  # Fast direct lookup
```

### 2. **Tracking & Auditing**
- Know which JSON corresponds to which database record
- Track data lineage from source → JSON → Database

### 3. **Deduplication**
- Check if recipe already exists before processing
- Can query database by UUID to avoid re-inserting

---

## Files Modified

| File | Change | Purpose |
|------|--------|---------|
| `json_processor.py` | Lines 35-51 | Generate UUID during JSON creation + use as filename |
| `activities.py` | Line 506, 522 | Use UUID from JSON if available |
| `add_uuids_to_json.py` | New script | Manual UUID backfill for old files |

---

## Usage

### For New Recipes (Automatic)

UUIDs are **automatically added** when JSON files are created:

```bash
# Process Kafka recipes - UUIDs generated automatically
python3 scripts/processing/kafka_consumer.py

# Process CSV recipes - UUIDs generated automatically  
python3 -m recipes process-csv data/raw/Reddit_Recipes.csv --local

# Check the UUID is in the file
ls data/stage/kafka_recipes/ | head -1 | xargs -I {} cat data/stage/kafka_recipes/{} | jq .uuid
# Output: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

# Or find a specific recipe by UUID
cat data/stage/kafka_recipes/a1b2c3d4-e5f6-7890-abcd-ef1234567890.json | jq .title
```

### For Existing JSON Files (Manual Backfill)

If you have old JSON files without UUIDs, you can add them:

```bash
# Backfill UUIDs for recipes already in the database
python3 scripts/add_uuids_to_json.py data/stage/kafka_recipes/

# This will:
# 1. Look up each recipe in the database by title
# 2. Get its UUID
# 3. Add the UUID to the JSON file
```

---

## Summary

| Question | Answer |
|----------|--------|
| Do JSON files have UUIDs? | Yes, automatically added during JSON creation |
| Where are UUIDs generated? | During JSON creation (before database) |
| Are they deterministic? | Yes, same recipe always gets the same UUID |
| Can I add UUIDs to old JSONs? | Yes, use `scripts/add_uuids_to_json.py` |

---

## Related Documentation

- [UUID Implementation Summary](UUID_IMPLEMENTATION_SUMMARY.md)
- [Migration Guide](MIGRATION_GUIDE.md)
- [Schema Improvements](SCHEMA_IMPROVEMENTS.md)

