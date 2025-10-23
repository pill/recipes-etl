# Documentation

Welcome to the Recipes ETL documentation! This directory contains all project documentation organized by topic.

## 🚀 Getting Started

- **[QUICK_START.md](QUICK_START.md)** - Quick start guide for new users
- **[AGENTS.md](AGENTS.md)** - Code style and testing guidelines for AI agents
- **[README_PYTHON.md](README_PYTHON.md)** - Python migration notes

## 📚 Guides

### Pipeline & Processing
- **[PIPELINE_EXAMPLE.md](PIPELINE_EXAMPLE.md)** - Example pipeline workflows
- **[STROMBERG_PIPELINE_GUIDE.md](STROMBERG_PIPELINE_GUIDE.md)** - Guide for processing Stromberg dataset

### Infrastructure
- **[TEMPORAL_GUIDE.md](TEMPORAL_GUIDE.md)** - Temporal workflow setup and usage
- **[ELASTICSEARCH_GUIDE.md](ELASTICSEARCH_GUIDE.md)** - Elasticsearch setup and configuration
- **[ELASTICSEARCH_QUERIES.md](ELASTICSEARCH_QUERIES.md)** - Common Elasticsearch query examples

### Migration & History
- **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)** - Migration from TypeScript to Python
- **[MIGRATION_COMPLETE.md](MIGRATION_COMPLETE.md)** - Migration completion notes

## 🗄️ Database & Schema

- **[SCHEMA_IMPROVEMENTS.md](SCHEMA_IMPROVEMENTS.md)** - Database schema improvements and notes

## 🔧 Development

- **[REFACTORING_PLAN.md](REFACTORING_PLAN.md)** - Project reorganization plan

## 💡 Quick Links

### Common Tasks
```bash
# Start the project
source activate.sh
docker-compose -f docker-compose.python.yml up -d

# Process recipes
python -m recipes.client batch-parallel data/raw/recipes.csv 1 100 20

# Load to database
python load_to_db.py

# Search recipes
python -m recipes.cli search-recipes "chicken"
```

### Need Help?
- Check [QUICK_START.md](QUICK_START.md) for setup instructions
- See [TEMPORAL_GUIDE.md](TEMPORAL_GUIDE.md) for workflow help
- Read [AGENTS.md](AGENTS.md) for code style guidelines

