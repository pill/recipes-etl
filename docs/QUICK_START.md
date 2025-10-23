# Quick Start Guide

Get up and running with the Recipes Python project in minutes!

## 🚀 Installation (One-Time Setup)

```bash
# 1. Clone/navigate to the project
cd recipes-python

# 2. Run installation script
python3 install.py

# 3. Update .env file with your API keys
nano .env  # or your preferred editor
```

## 🎯 Environment Activation (Each Session)

```bash
# Method 1: Use the activation script (Recommended)
source activate.sh

# Method 2: Activate venv manually
source venv/bin/activate
export PYTHONPATH=$PWD/src:$PYTHONPATH
```

## 📋 Quick Commands

### Using the CLI Wrapper (Easiest)

```bash
# After activating, you can use the wrapper script
./recipes --help
./recipes test-db
./recipes test-ai
./recipes process-recipe data/raw/recipes.csv 1
./recipes list-recipes
```

### Using Python Directly

```bash
# Make sure environment is activated first
source activate.sh

# Then run commands
python -m recipes.cli --help
python -m recipes.cli test-db
python -m recipes.worker
python -m recipes.client batch data/raw/recipes.csv 1 10
```

## 🐳 Docker (No Python Setup Required)

```bash
# Start all services
docker-compose -f docker-compose.python.yml up -d

# View worker logs
docker-compose -f docker-compose.python.yml logs -f recipes-worker

# Stop services
docker-compose -f docker-compose.python.yml down
```

## 🧪 Testing Your Setup

```bash
# 1. Activate environment
source activate.sh

# 2. Run setup test
python test_setup.py

# 3. Test database connection
./recipes test-db

# 4. Test AI service
./recipes test-ai
```

## 📖 Common Tasks

### Process a Single Recipe

```bash
# With local parsing (fast, free)
./recipes process-recipe data/raw/recipes.csv 5

# With AI (slower, costs money)
./recipes process-recipe data/raw/recipes.csv 5 --use-ai
```

### Process Multiple Recipes (Temporal)

```bash
# Terminal 1: Start worker
python -m recipes.worker

# Terminal 2: Process batch with local parsing
python -m recipes.client batch-local data/raw/recipes.csv 1 100

# Terminal 2: Process batch with parallel local parsing (fastest!)
python -m recipes.client batch-parallel data/raw/recipes.csv 1 1000 20
```

### Load Recipes to Database

```bash
# Load single recipe
./recipes load-recipe data/stage/entry_1.json

# Load multiple recipes
for file in data/stage/*.json; do
    ./recipes load-recipe "$file"
done
```

### Search and Query

```bash
# List recent recipes
./recipes list-recipes

# Search recipes
./recipes search-recipes "chicken"

# View statistics
./recipes stats
```

## 🛠️ Development

### Run Tests

```bash
source activate.sh
pytest tests/
```

### Format Code

```bash
source activate.sh
black src/ tests/
```

### Type Checking

```bash
source activate.sh
mypy src/
```

## 🆘 Troubleshooting

### "No module named recipes"

**Solution**: Activate the environment first
```bash
source activate.sh
```

### "Cannot connect to database"

**Solution**: Start database services
```bash
docker-compose -f docker-compose.python.yml up -d postgres
./recipes test-db
```

### "API key not set"

**Solution**: Update .env file
```bash
nano .env
# Add: ANTHROPIC_API_KEY=your_key_here
```

## 📚 More Documentation

- [README.md](./README.md) - Complete project documentation
- [TEMPORAL_GUIDE.md](./TEMPORAL_GUIDE.md) - Workflow orchestration
- [README_PYTHON.md](./README_PYTHON.md) - Python-specific details
- [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) - TypeScript to Python migration

## 💡 Tips

1. **Always activate the environment first**: `source activate.sh`
2. **Use local parsing for speed**: It's 30x faster and free!
3. **Use the wrapper script**: `./recipes` is easier than `python -m recipes.cli`
4. **Monitor Temporal workflows**: http://localhost:8081
5. **Check logs often**: `docker-compose logs -f recipes-worker`

---

**Need help?** Check the full documentation or run `./recipes --help`

