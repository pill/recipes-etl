# Recipes (Python)

AI-powered recipe data parser and analyzer - now in Python with Temporal workflows!

## 📊 Datasets

- **Reddit Recipes**: [Kaggle dataset](https://www.kaggle.com/datasets/michau96/recipes-from-reddit)
- **Stromberg Dataset**: [2M+ recipes](https://www.kaggle.com/datasets/wilmerarltstrmberg/recipe-dataset-over-2m)
- **Nutrition Data**: [USDA FoodData Central](https://fdc.nal.usda.gov/download-datasets#bkmk-1)

## 🚀 Quick Start

### Installation

```bash
# Install and setup
python3 install.py

# Activate virtual environment
source venv/bin/activate

# Configure environment
cp env.example .env
# Edit .env with your API keys

# Start services
docker-compose -f docker-compose.python.yml up -d
```

### Test Setup

```bash
# Test Python setup
python test_setup.py

# Test database connection
python -m recipes.cli test-db

# Test AI service
python -m recipes.cli test-ai
```

## 🎯 Core Features

- **AI-Powered Extraction**: Uses Anthropic Claude for recipe parsing
- **Local Parsing**: Fast, free alternative using pattern matching (30x faster!)
- **Temporal Workflows**: Robust batch processing with retry logic
- **PostgreSQL Database**: Relational storage with full schema
- **UUID Tracking**: Track recipes through entire pipeline with unique identifiers
- **Elasticsearch**: Full-text search and recommendations
- **CLI Interface**: Easy command-line tools
- **Docker Support**: Complete containerization

## 📖 Usage Guide

### Transform Single Recipe from CSV

**With AI (slower, costs money):**
```bash
source venv/bin/activate
python -m recipes.cli process-recipe data/raw/Reddit_Recipes.csv 5 --use-ai
cat data/stage/entry_5.json
```

**With Local Parsing (faster, FREE!):**
```bash
source venv/bin/activate
python -m recipes.cli process-recipe data/raw/Reddit_Recipes.csv 5
cat data/stage/entry_5.json
```

💡 **Tip**: Use local parsing for fast, free processing. It uses pattern matching to extract ingredients and instructions. Reserve AI for messy/unstructured recipes.

### Transform Multiple Recipes (Temporal Workflows - Recommended)

**Prerequisites:** Install and start Temporal server (see [TEMPORAL_GUIDE.md](./TEMPORAL_GUIDE.md))

**With AI (slower, costs money):**
```bash
# Terminal 1: Start the worker
source venv/bin/activate
python -m recipes.worker

# Terminal 2: Process entries 1-20
source venv/bin/activate
python -m recipes.client batch data/raw/Reddit_Recipes.csv 1 20
```

**With LOCAL parsing (faster, FREE!):**
```bash
# Terminal 1: Start the worker
source venv/bin/activate
python -m recipes.worker

# Terminal 2: Process entries 1-100 (much faster!)
source venv/bin/activate
python -m recipes.client batch-local data/raw/Reddit_Recipes.csv 1 100
```

**With PARALLELIZED LOCAL parsing (fastest, FREE!):**
```bash
# Terminal 1: Start the worker
source venv/bin/activate
python -m recipes.worker

# Terminal 2: Process entries 1-100 with parallel batches
source venv/bin/activate
python -m recipes.client batch-parallel data/raw/Reddit_Recipes.csv 1 100 20
```

## 🚀 One-Command Processing & Loading

For large datasets, use the comprehensive `process_and_load.py` script:

```bash
# Process and load Stromberg dataset (13,389 files) - local parsing
python process_and_load.py stromberg --local --batch-size 1000

# Process and load Reddit CSVs - local parsing  
python process_and_load.py reddit --local --batch-size 500

# Process single CSV file
python process_and_load.py csv data/raw/Reddit_Recipes.csv --local --batch-size 100

# Load existing JSON files only
python process_and_load.py load-only --batch-size 1000
```

This script automatically:
- ✅ Handles large datasets with auto-chunking
- ✅ Processes CSVs and loads to database in one command
- ✅ Supports both AI and local parsing
- ✅ Provides progress tracking and error handling
- ✅ Avoids Temporal payload size limits

**Performance Comparison:**

| Feature | AI Parsing | Local Parsing | Parallelized Local |
|---------|-----------|---------------|-------------------|
| **Speed** | ~1.5s per recipe | ~0.05s per recipe (30x faster) | ~0.01s per recipe (parallel) |
| **Cost** | ~$0.001-0.01 per recipe | **FREE** | **FREE** |
| **Accuracy** | Excellent for messy text | Good for structured data | Good for structured data |
| **Batch Processing** | Sequential | Sequential | **Parallel batches** |
| **Best for** | Unstructured Reddit posts | Well-formatted recipes | **Bulk processing (1000s)** |
| **100 recipes** | ~3 minutes + API costs | ~5 seconds, free | **~1-2 seconds, free** |

**Benefits:**
- Built-in rate limiting to avoid API limits
- Automatic retry on failures
- Resume from where you left off if interrupted
- Monitor progress in Temporal Web UI (http://localhost:8081)
- Scale with multiple workers

See [TEMPORAL_GUIDE.md](./TEMPORAL_GUIDE.md) for complete documentation.

### Load Recipe JSON into Database

After processing CSV entries into JSON, load them into the database:

**Single recipe (CLI):**
```bash
source venv/bin/activate
python -m recipes.cli load-recipe data/stage/entry_5.json
```

**Batch loading (recommended):**
```bash
# Process all JSON files in a directory
for file in data/stage/*.json; do
    python -m recipes.cli load-recipe "$file"
done
```

**Using Temporal workflows (for large batches):**
```python
# In your Python code
from recipes.client import run_load_recipes_workflow
import asyncio

async def load_all():
    json_files = ["data/stage/entry_1.json", "data/stage/entry_2.json", ...]
    result = await run_load_recipes_workflow(
        json_file_paths=json_files,
        parallel=True,
        batch_size=10
    )
    print(f"Loaded {result['successful']} recipes")

asyncio.run(load_all())
```

**Features:**
- Automatically checks if recipe already exists (by title)
- Skips duplicate recipes
- Creates ingredients and measurements automatically
- Returns the created recipe ID
- Temporal workflow provides: reliability, resumability, and monitoring

**Prerequisites:** Database must be running and configured (see Docker setup below)

### 📡 Scrape Fresh Recipes from Reddit

Monitor Reddit for new recipes and save them to CSV:

```bash
# Scrape once (run immediately and exit)
source venv/bin/activate
./COMMANDS.sh scrape --subreddit recipes --limit 50

# Monitor continuously (check every 5 minutes)
./COMMANDS.sh scrape-continuous --interval 300

# Scrape from different subreddit
./COMMANDS.sh scrape --subreddit cooking --limit 25

# Output saved to: data/raw/Reddit_recipes_scraped.csv
```

**What it does:**
- Fetches recent posts from r/recipes (or any subreddit)
- Extracts recipe text from OP's comments or self-posts
- Saves in CSV format matching existing Reddit_Recipes.csv structure
- Tracks processed posts to avoid duplicates

**After scraping**, process the new recipes through the pipeline:

```bash
# Process and load the scraped recipes
python scripts/processing/process_and_load.py
```

**See:** [REDDIT_SCRAPER_GUIDE.md](./docs/REDDIT_SCRAPER_GUIDE.md) for complete documentation

### ⏰ Schedule with Temporal (Recommended)

Run the scraper automatically every 5 minutes using Temporal Schedules - better than cron:

```bash
# 1. Start services and worker
./COMMANDS.sh start
./COMMANDS.sh worker

# 2. Create schedule (runs every 5 minutes)
./COMMANDS.sh schedule create --interval 5

# 3. Monitor in Temporal UI
open http://localhost:8081/schedules

# Manage schedule
./COMMANDS.sh schedule pause      # Pause scraping
./COMMANDS.sh schedule unpause    # Resume scraping
./COMMANDS.sh schedule trigger    # Run immediately
./COMMANDS.sh schedule describe   # View status
./COMMANDS.sh schedule delete     # Remove schedule
```

**Benefits:**
- ✅ Reliable execution with retry logic
- ✅ Full observability in Temporal UI
- ✅ Pause/resume without code changes
- ✅ Backfill missed runs
- ✅ No external cron dependencies

**See:** [TEMPORAL_SCHEDULES.md](./docs/TEMPORAL_SCHEDULES.md) for complete guide

### 🚀 Stream Recipes with Kafka (Event-Driven)

For scalable, event-driven recipe collection, use Kafka:

```bash
# 1. Start Kafka services
docker-compose -f docker-compose.python.yml up -d zookeeper kafka kafka-ui

# 2. Scrape and publish to Kafka (producer)
./COMMANDS.sh scrape-kafka --continuous --interval 300

# 3. Consume and process events (consumer)
./COMMANDS.sh kafka-consumer --save-csv

# Monitor at: http://localhost:8082 (Kafka UI)
```

**Benefits:**
- ⚡ Decoupled scraping and processing
- 📈 Scalable with multiple consumers
- 🔄 Reliable message delivery
- 🔁 Replay capability for reprocessing

**See:** [KAFKA_GUIDE.md](./docs/KAFKA_GUIDE.md) for complete documentation

### Search with Elasticsearch

Enable full-text search and recommendations:

```bash
# 1. Start Elasticsearch and Kibana
docker-compose -f docker-compose.python.yml up -d elasticsearch kibana

# 2. Wait ~30 seconds for Elasticsearch to be ready

# 3. Sync recipes from database to Elasticsearch
source venv/bin/activate
python -m recipes.cli sync-search

# Access Kibana at http://localhost:5601
# Access Elasticsearch at http://localhost:9200
```

**Test your search:**
```bash
# Search for recipes
curl "http://localhost:9200/recipes/_search?q=chicken&pretty"

# Count recipes
curl "http://localhost:9200/recipes/_count?pretty"
```

See [ELASTICSEARCH_GUIDE.md](./ELASTICSEARCH_GUIDE.md) for complete search documentation.

---

**📚 Complete Documentation**:
- [TEMPORAL_GUIDE.md](./TEMPORAL_GUIDE.md) - Workflow orchestration guide
- [README_PYTHON.md](./README_PYTHON.md) - Detailed Python documentation
- [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) - TypeScript to Python migration
- [MIGRATION_COMPLETE.md](./MIGRATION_COMPLETE.md) - Migration summary

## 🛠️ Tech Stack

### Backend (Python)
- **Python 3.11+** - Modern Python with async/await
- **Pydantic** - Runtime type validation and schema management
- **asyncpg** - High-performance PostgreSQL driver
- **Anthropic SDK** - Claude AI integration
- **Temporal** - Workflow orchestration and rate limiting
- **pytest** - Testing framework
- **asyncpraw** - Reddit async API wrapper

### Data & Infrastructure
- **PostgreSQL 15** - Relational database
- **Elasticsearch 8** - Full-text search and recommendations
- **Docker** - Containerization and deployment
- **Redis** - Caching (future)

### Frontend (Separate)
- **React + TypeScript** - Modern web frontend (`client/recipe-client/`)
- **Vite** - Build tool

## 📋 CLI Commands

### Database Operations
```bash
python -m recipes.cli test-db          # Test database connection
python -m recipes.cli list-recipes     # List recent recipes
python -m recipes.cli search-recipes   # Search recipes
python -m recipes.cli stats            # Show statistics
```

### Recipe Processing
```bash
python -m recipes.cli process-recipe <csv> <entry> [--use-ai]
python -m recipes.cli load-recipe <json-file>
```

### AI Operations
```bash
python -m recipes.cli test-ai          # Test AI connection
```

### Workflow Operations
```bash
python -m recipes.worker               # Start Temporal worker
python -m recipes.client batch <csv> <start> <end>
python -m recipes.client batch-local <csv> <start> <end>
python -m recipes.client batch-parallel <csv> <start> <end> <batch-size>
```

## 🐳 Docker Setup

### Start All Services
```bash
docker-compose -f docker-compose.python.yml up -d
```

This starts:
- PostgreSQL database
- Temporal server
- Temporal Web UI (http://localhost:8081)
- Elasticsearch (optional)
- Kibana (optional)
- Python Temporal worker

### Service-Specific Commands
```bash
# Start only database
docker-compose -f docker-compose.python.yml up -d postgres

# Start Temporal stack
docker-compose -f docker-compose.python.yml up -d temporal temporal-ui

# View worker logs
docker-compose -f docker-compose.python.yml logs -f recipes-worker

# Stop all services
docker-compose -f docker-compose.python.yml down
```

## 🏗️ Architecture

### Data Flow

1. **CSV Input** → CSV Parser → Raw Data
2. **Raw Data** → AI Service or Local Parser → Structured Recipe Data
3. **Recipe Data** → JSON Processor → JSON Files
4. **JSON Files** → Recipe Service → PostgreSQL Database
5. **Database** → Search Service → Elasticsearch Index

### Project Structure

```
recipes-python/
├── src/recipes/              # Main Python package
│   ├── models/              # Pydantic data models
│   ├── services/            # Business logic (AI, DB, Search, Reddit)
│   ├── workflows/           # Temporal workflows & activities
│   ├── database/            # Database connection & queries
│   ├── utils/               # Utility functions
│   ├── cli/                 # Command-line interface
│   └── config.py            # Configuration management
├── tests/                   # Test suite
├── scripts/                 # Setup & utility scripts
├── data/                    # Data directories
├── client/recipe-client/    # React frontend (separate)
└── docker-compose.python.yml # Docker configuration
```

## 🔄 Workflows

### Recipe Extraction Pipeline

1. **Get Raw Data**: Reddit, Kaggle CSV, or direct scraping
2. **Transform**: AI or local parsing to structured JSON
3. **Clean**: Deduplication and validation
4. **Load**: Insert into PostgreSQL database
5. **Index**: Sync to Elasticsearch for search

### Future Features

- **Recommender System**:
  - Ingredient-based recommendations
  - Nutrition scoring
  - Cost optimization with grocery prices
  - User preference feedback loop
  - Skill level matching

## 📦 Development

### Running Tests
```bash
source venv/bin/activate
pytest tests/
```

### Code Quality
```bash
# Format code
black src/ tests/

# Lint
ruff src/ tests/

# Type checking
mypy src/
```

## 📈 Version History

### v2.1
- data firehose from Reddit data (r/recipes)
- Kafka topic to collect scraper data

### v2.0 (Current - Python)
- Complete migration to Python
- Pydantic models with runtime validation
- Better async/await support
- Improved CLI interface
- Temporal workflows preserved
- 30x faster local parsing
- Lower memory usage

### v1.2 (TypeScript)
- Optimized CSV → JSON → DB processing
- Parallel processing implementation
- Chained workflows
- Large dataset support (2M recipes)

### v1.1 (TypeScript)
- LLM generated transform scripts
- Reduced API calls

### v1.0 (TypeScript)
- Initial implementation
- Direct LLM calls
- Basic data processing

## Future Ideas
- categorization
    - ML for categorization

- agent for ?
    - cleaning data?


## 🆘 Troubleshooting

### Common Issues

**Virtual environment not activated:**
```bash
source venv/bin/activate
```

**Database connection failed:**
```bash
docker-compose -f docker-compose.python.yml up -d postgres
python -m recipes.cli test-db
```

**AI service not working:**
```bash
# Check .env file has ANTHROPIC_API_KEY set
python -m recipes.cli test-ai
```

**Temporal worker not starting:**
```bash
docker-compose -f docker-compose.python.yml up -d temporal
docker-compose -f docker-compose.python.yml logs temporal
```

### Getting Help

- Check logs: `docker-compose -f docker-compose.python.yml logs -f`
- Run tests: `pytest tests/`
- Review documentation: [docs/](./docs/)
- Quick start: [docs/QUICK_START.md](./docs/QUICK_START.md)
- Temporal workflows: [docs/TEMPORAL_GUIDE.md](./docs/TEMPORAL_GUIDE.md)
- Code guidelines: [docs/AGENTS.md](./docs/AGENTS.md)

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- **Datasets**: Kaggle contributors, USDA
- **AI**: Anthropic Claude
- **Orchestration**: Temporal
- **Community**: Python and TypeScript ecosystems

---

## 📚 Documentation

All project documentation is now organized in the [`docs/`](./docs/) directory:

- **[Quick Start Guide](./docs/QUICK_START.md)** - Get up and running quickly
- **[Temporal Guide](./docs/TEMPORAL_GUIDE.md)** - Workflow setup and usage
- **[Elasticsearch Guide](./docs/ELASTICSEARCH_GUIDE.md)** - Search setup and queries
- **[Pipeline Examples](./docs/PIPELINE_EXAMPLE.md)** - Processing examples
- **[Code Guidelines](./docs/AGENTS.md)** - Style and testing standards
- **[Migration Notes](./docs/MIGRATION_COMPLETE.md)** - TypeScript to Python migration

See [docs/README.md](./docs/README.md) for the complete documentation index.

---

**Note**: This is the Python version of the recipes project. The TypeScript client application in `client/` remains unchanged and can communicate with this Python backend.
