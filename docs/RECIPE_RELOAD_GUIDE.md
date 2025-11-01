# Recipe Reload Guide

How to reload a specific recipe from JSON through the entire pipeline (JSON → PostgreSQL → Elasticsearch) using its UUID.

## Overview

The `reload-recipe` command allows you to reload a single recipe by UUID through the complete data pipeline:
1. **Locate JSON file** by UUID
2. **Load to PostgreSQL** database (insert or update)
3. **Sync to Elasticsearch** for search indexing

This is useful for:
- Fixing data inconsistencies
- Reindexing after manual JSON edits
- Debugging UUID changes
- Testing recipe modifications
- Recovering from partial pipeline failures

## Quick Start

### Basic Usage

```bash
# Reload a recipe by UUID (searches data/stage recursively)
./CMD.sh reload-recipe 8faa4a5f-4f52-56db-92aa-fa574ed6b62c
```

### Custom Directory

```bash
# Search in a specific directory
./CMD.sh reload-recipe 8faa4a5f-4f52-56db-92aa-fa574ed6b62c --json-dir data/stage/Reddit_Recipes
```

## Prerequisites

1. **Services Running:**
   ```bash
   docker-compose up -d
   ```

2. **JSON File Exists:**
   - File must be named `{UUID}.json`
   - Located in search directory or subdirectories
   - Contains valid recipe JSON

3. **Elasticsearch (Optional):**
   - If Elasticsearch is not running, recipe will still load to database
   - Elasticsearch sync will be skipped with a warning

## Step-by-Step Process

### 1. Find the Recipe UUID

If you don't know the UUID, you can:

**Search by title:**
```bash
./CMD.sh search 'Sicilian Pasta'
```

**List recent recipes:**
```bash
./CMD.sh list
```

**Get UUID from JSON filename:**
```bash
ls data/stage/Reddit_Recipes/
# Look for: 8faa4a5f-4f52-56db-92aa-fa574ed6b62c.json
```

### 2. Run the Reload Command

```bash
./CMD.sh reload-recipe 8faa4a5f-4f52-56db-92aa-fa574ed6b62c
```

### 3. Expected Output

**Normal case (UUID unchanged):**
```
🔍 Looking for recipe JSON with UUID: 8faa4a5f-4f52-56db-92aa-fa574ed6b62c...
✅ Found JSON file: data/stage/Reddit_Recipes/8faa4a5f-4f52-56db-92aa-fa574ed6b62c.json
💾 Loading recipe to database...
✅ Recipe loaded to database
   ID: 1234
   Title: Sicilian Pasta with Eggplant
   UUID: 8faa4a5f-4f52-56db-92aa-fa574ed6b62c
🔄 Syncing recipe to Elasticsearch...
✅ Recipe synced to Elasticsearch

🎉 Recipe reload complete!
   📄 JSON: data/stage/Reddit_Recipes/8faa4a5f-4f52-56db-92aa-fa574ed6b62c.json
   💾 Database ID: 1234
   🔍 Elasticsearch: Indexed
   🏷️  Original UUID: 8faa4a5f-4f52-56db-92aa-fa574ed6b62c
```

**UUID changed during load:**
```
🔍 Looking for recipe JSON with UUID: 11088052-b7a5-566a-9422-9f9b85fa88cb...
✅ Found JSON file: data/stage/Reddit_Recipes/11088052-b7a5-566a-9422-9f9b85fa88cb.json
💾 Loading recipe to database...
✅ Recipe loaded to database
   ID: 1234
   Title: Sicilian Pasta with Eggplant
   UUID: 11088052-b7a5-566a-9422-9f9b85fa88cb
🔄 Syncing recipe to Elasticsearch...
⚠️  UUID changed during load!
   Expected: 11088052-b7a5-566a-9422-9f9b85fa88cb
   Got:      8faa4a5f-4f52-56db-92aa-fa574ed6b62c
   This happens when recipe content (title/ingredients) changed.
✅ Recipe synced to Elasticsearch

🎉 Recipe reload complete!
   📄 JSON: data/stage/Reddit_Recipes/11088052-b7a5-566a-9422-9f9b85fa88cb.json
   💾 Database ID: 1234
   🔍 Elasticsearch: Indexed
   🏷️  Original UUID: 11088052-b7a5-566a-9422-9f9b85fa88cb
   🏷️  Current UUID:  8faa4a5f-4f52-56db-92aa-fa574ed6b62c (changed)
```

**Note:** UUIDs are deterministic based on recipe **title only** (and source URL if available). If the title changed between when the JSON was created and now, the UUID will be regenerated. Ingredient changes do not affect UUIDs.

## Use Cases

### 1. Fix UUID Change Issue

You noticed a recipe changed UUIDs after reprocessing:

```bash
# Old UUID: 11088052-b7a5-566a-9422-9f9b85fa88cb
# New UUID: 8faa4a5f-4f52-56db-92aa-fa574ed6b62c

# Reload using the OLD UUID filename - command will detect the change
./CMD.sh reload-recipe 11088052-b7a5-566a-9422-9f9b85fa88cb

# The command will show:
# ⚠️  UUID changed during load!
#    Expected: 11088052-b7a5-566a-9422-9f9b85fa88cb
#    Got:      8faa4a5f-4f52-56db-92aa-fa574ed6b62c
#    This happens when recipe content (title/ingredients) changed.

# Now you can look up by the NEW UUID
./CMD.sh get-by-uuid 8faa4a5f-4f52-56db-92aa-fa574ed6b62c
```

**Why UUIDs change:**
- UUIDs are deterministic, based on **title only** (+ source URL if available)
- If the recipe title changed, UUID changes
- Ingredient changes do NOT affect UUID (title-only matching)
- The command automatically handles UUID changes and syncs with the new UUID

### 2. Manual JSON Edit

You edited a recipe JSON file manually:

```bash
# Edit the JSON
vim data/stage/Reddit_Recipes/8faa4a5f-4f52-56db-92aa-fa574ed6b62c.json

# Reload to database and Elasticsearch
./CMD.sh reload-recipe 8faa4a5f-4f52-56db-92aa-fa574ed6b62c

# Verify changes
./CMD.sh get-by-uuid 8faa4a5f-4f52-56db-92aa-fa574ed6b62c
```

### 3. Reindex to Elasticsearch

Recipe is in database but missing from Elasticsearch:

```bash
# Reload (will update database and reindex to Elasticsearch)
./CMD.sh reload-recipe 8faa4a5f-4f52-56db-92aa-fa574ed6b62c
```

### 4. Test Recipe Changes

Testing ingredient filtering or parsing improvements:

```bash
# Reload with new parsing logic
./CMD.sh reload-recipe 8faa4a5f-4f52-56db-92aa-fa574ed6b62c

# Check results in React client
# Visit: http://localhost:5173
# Click "By UUID" tab
# Enter: 8faa4a5f-4f52-56db-92aa-fa574ed6b62c
```

## Advanced Usage

### Using Python CLI Directly

```bash
source activate.sh

# Basic reload
python -m recipes.cli reload-recipe 8faa4a5f-4f52-56db-92aa-fa574ed6b62c

# Custom directory
python -m recipes.cli reload-recipe \
  8faa4a5f-4f52-56db-92aa-fa574ed6b62c \
  --json-dir data/stage/2025-10-14/stromberg_data

# Get help
python -m recipes.cli reload-recipe --help
```

### Search Patterns

The command searches for JSON files in this order:
1. `{json-dir}/{uuid}.json`
2. `{json-dir}/*/{uuid}.json`
3. `{json-dir}/*/*/{uuid}.json`

This allows for nested directory structures like:
```
data/stage/
  ├── Reddit_Recipes/
  │   └── 8faa4a5f-4f52-56db-92aa-fa574ed6b62c.json
  └── 2025-10-14/
      └── stromberg_data/
          └── 11088052-b7a5-566a-9422-9f9b85fa88cb.json
```

## Error Handling

### JSON File Not Found

```
❌ No JSON file found for UUID: 8faa4a5f-4f52-56db-92aa-fa574ed6b62c
   Searched in: data/stage
   Expected filename: 8faa4a5f-4f52-56db-92aa-fa574ed6b62c.json
```

**Solution:** Check the UUID or specify correct directory with `--json-dir`

### Database Load Failed

```
❌ Failed to load recipe to database: Recipe has too few valid ingredients after filtering
```

**Solution:** Check the JSON file for data quality issues

### Elasticsearch Not Running

```
⚠️  Elasticsearch is not healthy - skipping sync
💡 Start Elasticsearch with: docker-compose up -d elasticsearch
```

**Solution:** Recipe is still loaded to database. Start Elasticsearch and run again to sync.

### Recipe Not Found in Database (Fixed)

This error has been fixed in the latest version. The command now:
1. Fetches the recipe by database ID (not UUID)
2. Detects if the UUID changed
3. Successfully syncs even when UUID changes

If you see this error, update to the latest code.

## Verification

After reloading, verify the recipe:

### 1. Check Database

```bash
./CMD.sh get-by-uuid 8faa4a5f-4f52-56db-92aa-fa574ed6b62c
```

### 2. Check Elasticsearch

```bash
# Using curl
curl -X POST "localhost:9200/recipes/_search?pretty" \
  -H 'Content-Type: application/json' \
  -d '{
    "query": {
      "term": {
        "uuid.keyword": "8faa4a5f-4f52-56db-92aa-fa574ed6b62c"
      }
    }
  }'
```

### 3. Check React Client

1. Visit http://localhost:5173
2. Click "By UUID" tab
3. Enter UUID: `8faa4a5f-4f52-56db-92aa-fa574ed6b62c`
4. View complete recipe

## Related Commands

```bash
# View recipe details
./CMD.sh get-by-uuid <uuid>

# Search for recipes
./CMD.sh search '<term>'

# Sync all recipes to Elasticsearch
python -m recipes.cli sync-search

# Load entire folder to database
./CMD.sh load-folder data/stage/Reddit_Recipes
```

## Troubleshooting

### Command Not Found

```bash
# Make sure you're in the project root
cd /Users/pavery/dev/recipes-etl

# Make CMD.sh executable
chmod +x CMD.sh

# Try running directly
./CMD.sh reload-recipe <uuid>
```

### Import Errors

```bash
# Activate virtual environment
source activate.sh

# Or source venv directly
source venv/bin/activate

# Verify Python path
python -m recipes.cli --help
```

### Permission Errors

```bash
# Check file permissions
ls -l data/stage/Reddit_Recipes/*.json

# Fix if needed
chmod 644 data/stage/Reddit_Recipes/*.json
```

## Best Practices

1. **Backup First:** Before reloading modified recipes, backup the original JSON
2. **Verify UUID:** Double-check the UUID before running the command
3. **Check Services:** Ensure PostgreSQL and Elasticsearch are running
4. **Test in Dev:** Test recipe changes in development before production
5. **Monitor Logs:** Watch for errors during reload process

## See Also

- [COMMANDS.md](./COMMANDS.md) - Complete command reference
- [UUID_TRACKING.md](./UUID_TRACKING.md) - UUID generation and tracking
- [ELASTICSEARCH_GUIDE.md](./ELASTICSEARCH_GUIDE.md) - Elasticsearch setup and usage

