# Project Reorganization Plan

## Current Issues

1. **Root directory clutter**: Too many loose files at project root
2. **Mixed concerns**: Test files, scripts, and docs all mixed together
3. **Duplicate/unclear naming**: `scripts/` folder vs `scripts.py` file
4. **Test organization**: Mix of JS and Python tests in same directory
5. **Data management**: No clear structure for processed data

## Proposed New Structure

```
recipes-etl/
├── README.md
├── pyproject.toml
├── requirements.txt
├── docker-compose.yml
├── .env.example
│
├── docs/                          # 📚 All documentation
│   ├── README.md                  # Docs index
│   ├── quickstart.md
│   ├── guides/
│   │   ├── elasticsearch.md
│   │   ├── temporal.md
│   │   ├── migration.md
│   │   └── pipeline.md
│   └── schemas/
│       └── improvements.md
│
├── src/
│   └── recipes/                   # 🐍 Core Python package (GOOD)
│       ├── cli/
│       ├── models/
│       ├── services/
│       ├── utils/
│       ├── workflows/
│       ├── database/
│       ├── config.py
│       ├── client.py
│       └── worker.py
│
├── client/                        # ⚛️ Frontend React app
│   ├── src/
│   ├── public/
│   └── package.json
│
├── scripts/                       # 🔧 Utility scripts
│   ├── setup/
│   │   ├── install.py
│   │   ├── setup-db.sh
│   │   └── test-setup.py
│   ├── processing/
│   │   ├── process-and-load.py
│   │   ├── load-to-db.py
│   │   └── batch-process.py
│   └── examples/
│       └── recipe-extraction-example.js
│
├── tests/                         # 🧪 All tests
│   ├── python/                    # Separate by language
│   │   ├── conftest.py
│   │   ├── test_models.py
│   │   ├── test_services.py
│   │   ├── test_parsers.py
│   │   └── integration/
│   │       └── test_workflows.py
│   └── typescript/
│       ├── models/
│       └── services/
│
├── data/                          # 📁 Data directory
│   ├── raw/                       # Source CSV files
│   ├── processed/                 # Parsed JSON (renamed from 'stage')
│   │   └── {dataset_name}/
│   ├── samples/                   # Test data
│   └── .gitignore                 # Ignore large files
│
├── db/                            # 🗄️ Database files
│   ├── migrations/                # NEW: Version controlled migrations
│   │   ├── 001_initial_schema.sql
│   │   └── 002_add_metadata_fields.sql
│   ├── schema.sql                 # Current schema
│   └── seeds/                     # NEW: Test data
│       └── sample_recipes.sql
│
├── infra/                         # 🏗️ Infrastructure
│   ├── docker/
│   │   ├── Dockerfile.worker
│   │   └── docker-compose.python.yml
│   └── k8s/                       # NEW: If you scale up
│
├── .github/                       # 🔄 CI/CD (NEW)
│   └── workflows/
│       ├── test.yml
│       └── lint.yml
│
└── venv/                          # Virtual environment
```

## Migration Steps

### Phase 1: Documentation (Low Risk)
```bash
mkdir -p docs/guides docs/schemas
mv ELASTICSEARCH_GUIDE.md docs/guides/elasticsearch.md
mv TEMPORAL_GUIDE.md docs/guides/temporal.md
mv MIGRATION_GUIDE.md docs/guides/migration.md
mv MIGRATION_COMPLETE.md docs/guides/migration-complete.md
mv PIPELINE_EXAMPLE.md docs/guides/pipeline.md
mv STROMBERG_PIPELINE_GUIDE.md docs/guides/stromberg-pipeline.md
mv QUICK_START.md docs/quickstart.md
mv SCHEMA_IMPROVEMENTS.md docs/schemas/improvements.md
mv ELASTICSEARCH_QUERIES.md docs/guides/elasticsearch-queries.md
mv README_PYTHON.md docs/python-migration.md
```

### Phase 2: Scripts (Medium Risk)
```bash
mkdir -p scripts/setup scripts/processing
mv install.py scripts/setup/
mv test_setup.py scripts/setup/
mv load_to_db.py scripts/processing/
mv process_and_load.py scripts/processing/
mv test_comprehensive_parsing.py scripts/processing/
rm scripts.py  # Consolidate functionality elsewhere
```

### Phase 3: Tests (Medium Risk)
```bash
mkdir -p tests/python tests/typescript
mv tests/test_basic.py tests/python/
mv tests/models/*.test.js tests/typescript/models/
mv tests/services/*.test.js tests/typescript/services/
mv tests/schemas/*.test.js tests/typescript/schemas/
```

### Phase 4: Infrastructure (Low Risk)
```bash
mkdir -p infra/docker
mv docker-compose.python.yml infra/docker/
mv Dockerfile.worker infra/docker/
```

### Phase 5: Database (Medium Risk)
```bash
mkdir -p db/migrations db/seeds
# Keep schema.sql in db/
# Create migration files for version control
```

### Phase 6: Data (Low Risk)
```bash
cd data
mv stage processed
# Update code references from 'stage' to 'processed'
```

## Code Changes Required

### Update imports/paths in:
1. `src/recipes/workflows/activities.py` - Update data paths
2. `load_to_db.py` (now `scripts/processing/load-to-db.py`)
3. `process_and_load.py` - Update paths
4. `activate.sh` - Update PYTHONPATH if needed
5. Docker compose files - Update volume mounts
6. README.md - Update all command examples

### Update configuration:
```python
# src/recipes/config.py
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
RAW_DATA_DIR = DATA_DIR / 'raw'
PROCESSED_DATA_DIR = DATA_DIR / 'processed'  # Changed from 'stage'
```

## Benefits

1. **Cleaner root directory**: Only essential files visible
2. **Better discoverability**: Clear where everything lives
3. **Easier onboarding**: New developers can navigate easily
4. **Scalability**: Structure supports growth
5. **CI/CD ready**: Clear test structure for automation
6. **Documentation**: Centralized and organized

## Alternative: Minimal Reorganization

If full reorganization is too much, do this minimal cleanup:

```bash
# Just clean up the root
mkdir -p docs scripts/setup scripts/processing
mv *.md docs/  # Except README.md
mv install.py test_setup.py scripts/setup/
mv load_to_db.py process_and_load.py test_comprehensive_parsing.py scripts/processing/
```

## Risks & Considerations

1. **Breaking changes**: Will break existing scripts/commands
2. **Documentation updates**: All guides need path updates
3. **Team coordination**: If others are working on this
4. **CI/CD pipelines**: May break existing automation
5. **Docker volumes**: Need to update mount paths

## Recommendation

Start with **Phase 1 (Documentation)** - zero risk, immediate benefit.
Then do **Phase 2 (Scripts)** to clean up root directory.
Save phases 3-6 for when you have time for thorough testing.

