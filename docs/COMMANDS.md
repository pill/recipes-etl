# Command Reference

Quick reference for all common commands after the reorganization.

## 🚀 Setup & Installation

```bash
# Install dependencies
python3 scripts/setup/install.py

# Activate environment
source activate.sh

# Test setup
python3 scripts/setup/test_setup.py

# Check database connection
python3 scripts/setup/check-db.py

# Setup database
./scripts/setup/setup-db.sh
```

## 🏃 Running Services

### Start Infrastructure (Docker)
```bash
# Start all services (Temporal, PostgreSQL, Elasticsearch)
docker-compose -f docker-compose.python.yml up -d

# Check logs
docker-compose -f docker-compose.python.yml logs -f

# Stop services
docker-compose -f docker-compose.python.yml down
```

### Start Temporal Worker
```bash
# Method 1: Using runner script
source activate.sh
python3 scripts/runners/run_worker.py

# Method 2: Direct module
source activate.sh
python -m recipes.worker
```

### Start Temporal Client
```bash
# Method 1: Using runner script
source activate.sh
python3 scripts/runners/run_client.py batch-parallel data/raw/recipes.csv 1 100 20

# Method 2: Direct module
source activate.sh
python -m recipes.client batch-parallel data/raw/recipes.csv 1 100 20
```

## 📊 Processing Recipes

### Process CSV Files

**Local parsing (fast, free):**
```bash
source activate.sh

# Single recipe
python -m recipes.cli process-recipe data/raw/Reddit_Recipes.csv 5

# Batch with parallel local parsing (recommended)
python -m recipes.client batch-parallel data/raw/Reddit_Recipes.csv 1 100 20
#                                       ^CSV file          ^start ^end ^batch size
```

**AI parsing (slower, costs money):**
```bash
source activate.sh
python -m recipes.cli process-recipe data/raw/Reddit_Recipes.csv 5 --use-ai
```

### Load to Database

```bash
source activate.sh

# Load all processed JSON files to database (parallel)
python3 scripts/processing/load_to_db.py

# Load JSON files from a specific folder to database
python3 scripts/processing/load_folder_to_db.py data/stage/Reddit_Recipes
python3 scripts/processing/load_folder_to_db.py data/stage/2025-10-14/stromberg_data

# Process AND load in one command
python3 scripts/processing/process_and_load.py stromberg --local --batch-size 1000
```

## 🔍 Database & CLI Operations

### Search & Query Recipes

```bash
source activate.sh

# List recent recipes
python -m recipes.cli list-recipes

# Search recipes
python -m recipes.cli search-recipes "chicken"

# Get recipe by ID
python -m recipes.cli get-recipe 123

# View statistics
python -m recipes.cli stats
```

### Database Operations

```bash
# Test database connection
python -m recipes.cli test-db

# Run database queries directly
psql -h localhost -U recipes_user -d recipes
```

## 🧪 Testing & Development

### Run Tests

```bash
source activate.sh

# Test recipe parsing
python3 scripts/processing/test_comprehensive_parsing.py

# Run Python tests
pytest tests/

# Run specific test
pytest tests/python/test_models.py
```

### Code Quality

```bash
source activate.sh

# Format code
black src/ tests/

# Lint code
ruff check src/

# Type checking
mypy src/
```

## 📁 File Locations Reference

### Scripts (all in `scripts/` now)
- **Setup**: `scripts/setup/`
  - `install.py` - Install dependencies
  - `test_setup.py` - Test Python setup
  - `check-db.py` - Check database connection
  - `setup-db.sh` - Initialize database

- **Processing**: `scripts/processing/`
  - `load_to_db.py` - Load JSON files to database
  - `process_and_load.py` - Process CSVs and load in one command
  - `test_comprehensive_parsing.py` - Test recipe parsing

- **Runners**: `scripts/runners/`
  - `run_worker.py` - Start Temporal worker
  - `run_client.py` - Run Temporal client

- **Tests**: `scripts/tests/`
  - `test-db.js` - Database connection test (Node.js)

- **Examples**: `scripts/examples/`
  - `recipe-extraction-example.js` - Recipe extraction example

### Documentation (all in `docs/` now)
- `docs/QUICK_START.md` - Quick start guide
- `docs/TEMPORAL_GUIDE.md` - Temporal workflows guide
- `docs/ELASTICSEARCH_GUIDE.md` - Elasticsearch setup
- `docs/PIPELINE_EXAMPLE.md` - Pipeline examples
- `docs/AGENTS.md` - Code style guidelines

### Data Directories
- `data/raw/` - Original CSV files
- `data/stage/` - Processed JSON files
- `data/samples/` - Sample data for testing

## 🎯 Common Workflows

### Complete Processing Workflow

```bash
# 1. Activate environment
source activate.sh

# 2. Start services (in one terminal)
docker-compose -f docker-compose.python.yml up -d

# 3. Start worker (in another terminal)
source activate.sh
python3 scripts/runners/run_worker.py

# 4. Process recipes (in third terminal)
source activate.sh
python -m recipes.client batch-parallel data/raw/Reddit_Recipes.csv 1 1000 50

# 5. Load to database
python3 scripts/processing/load_to_db.py

# 6. Search recipes
python -m recipes.cli search-recipes "pasta"
```

### Quick Test Workflow

```bash
# Test everything is working
source activate.sh
python3 scripts/setup/test_setup.py
python3 scripts/processing/test_comprehensive_parsing.py
python -m recipes.cli test-db
```

## 💡 Tips

1. **Always activate environment first**: `source activate.sh`
2. **Check logs if something fails**: `docker-compose -f docker-compose.python.yml logs -f`
3. **Use absolute paths when unsure**: `/Users/pavery/dev/recipes-etl/scripts/...`
4. **Parallel processing is fastest**: Use `batch-parallel` with batch size 20-50
5. **Local parsing is 30x faster**: Only use AI when you need higher accuracy

## 🆘 Troubleshooting

**Script not found?**
```bash
# Use absolute path
/Users/pavery/dev/recipes-etl/scripts/setup/test_setup.py

# Or make executable
chmod +x scripts/setup/test_setup.py
```

**Module not found?**
```bash
# Always use activate.sh (sets PYTHONPATH)
source activate.sh
```

**Database connection error?**
```bash
# Check services are running
docker-compose -f docker-compose.python.yml ps

# Check database connection
python3 scripts/setup/check-db.py
```

