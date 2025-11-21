# Recipe ETL pipeline

AI-powered recipe data parser and analyzer (Temporal, Kafka, Postgres, Elasticsearch)

## 📊 Datasets

- **Reddit Recipes**: [Kaggle dataset](https://www.kaggle.com/datasets/michau96/recipes-from-reddit)
- **Stromberg Dataset**: [2M+ recipes](https://www.kaggle.com/datasets/wilmerarltstrmberg/recipe-dataset-over-2m)
- **Nutrition Data**: [USDA FoodData Central](https://fdc.nal.usda.gov/download-datasets#bkmk-1)

## 🚀 Quick Start

### Installation

```bash
# Install and setup
python3 scripts/setup/install.py

# Activate virtual environment
source venv/bin/activate

# Configure environment
cp env.example .env
# Edit .env with your API keys

# Start services
docker-compose up -d
```

### Test Setup

```bash
# Test Python setup
python scripts/setup/test_setup.py

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
- **Semantic Search**: Vector embeddings for meaning-based recipe discovery
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

**Prerequisites:** Install and start Temporal server (see [TEMPORAL_GUIDE.md](./docs/TEMPORAL_GUIDE.md))

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
python scripts/processing/process_and_load.py stromberg --local --batch-size 1000

# Process and load Reddit CSVs - local parsing  
python scripts/processing/process_and_load.py reddit --local --batch-size 500

# Process single CSV file
python scripts/processing/process_and_load.py csv data/raw/Reddit_Recipes.csv --local --batch-size 100

# Load existing JSON files only
python scripts/processing/process_and_load.py load-only --batch-size 1000
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

See [TEMPORAL_GUIDE.md](./docs/TEMPORAL_GUIDE.md) for complete documentation.

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
./CMD.sh scrape --subreddit recipes --limit 50

# Monitor continuously (check every 5 minutes)
./CMD.sh scrape-continuous --interval 300

# Scrape from different subreddit
./CMD.sh scrape --subreddit cooking --limit 25

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
./CMD.sh start
./CMD.sh worker

# 2. Create schedule (runs every 5 minutes)
./CMD.sh schedule create --interval 5

# 3. Monitor in Temporal UI
open http://localhost:8081/schedules

# Manage schedule
./CMD.sh schedule pause      # Pause scraping
./CMD.sh schedule unpause    # Resume scraping
./CMD.sh schedule trigger    # Run immediately
./CMD.sh schedule describe   # View status
./CMD.sh schedule delete     # Remove schedule
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
docker-compose up -d zookeeper kafka kafka-ui

# 2. Scrape and publish to Kafka (producer)
./CMD.sh scrape-kafka --continuous --interval 300

# 3. Consume and process events (consumer)
./CMD.sh kafka-consumer --save-csv

# Monitor at: http://localhost:8082 (Kafka UI)
```

**Benefits:**
- ⚡ Decoupled scraping and processing
- 📈 Scalable with multiple consumers
- 🔄 Reliable message delivery
- 🔁 Replay capability for reprocessing

**See:** [KAFKA_GUIDE.md](./docs/KAFKA_GUIDE.md) for complete documentation

### Search with Elasticsearch

Enable full-text search, semantic search, and recommendations:

```bash
# 1. Start Elasticsearch and Kibana
docker-compose up -d elasticsearch kibana

# 2. Wait ~30 seconds for Elasticsearch to be ready

# 3. Sync recipes from database to Elasticsearch (with embeddings)
source activate.sh
python -m recipes.cli sync-search

# Access Kibana at http://localhost:5601
# Access Elasticsearch at http://localhost:9200
```

**Test your search:**
```bash
# Traditional text search
curl "http://localhost:9200/recipes/_search?q=chicken&pretty"

# Count recipes
curl "http://localhost:9200/recipes/_count?pretty"
```

**Semantic Search:**
- Finds recipes by meaning, not just keywords
- Great for queries like "comfort food" or "healthy breakfast"
- Uses vector embeddings (384 dimensions) stored in Elasticsearch
- See [EMBEDDINGS_GUIDE.md](./docs/EMBEDDINGS_GUIDE.md) for details

See [ELASTICSEARCH_GUIDE.md](./docs/ELASTICSEARCH_GUIDE.md) for complete search documentation.

### React Client (Web UI)

Explore and search recipes with a modern web interface:

```bash
# Start the React client
cd client
npm install
npm run dev

# Access at: http://localhost:5173
```

**Features:**
- 🎲 **Random Recipe** - Discover random recipes
- 🔍 **Full-Text Search** - Search by keywords using Elasticsearch
- 🧠 **Semantic Search** - Find recipes by meaning (e.g., "comfort food", "healthy breakfast")
- 🔀 **Hybrid Search** - Combines text and semantic search for best results
- 🏷️ **UUID Search** - Look up specific recipes by UUID (perfect for debugging!)
- 🥘 **Ingredient Search** - Filter by ingredients
- ⚡ **Quick & Easy** - Find fast recipes
- 🌍 **Cuisine Analysis** - Analyze recipes by cuisine

**Semantic Search Examples:**
- "comfort food" → Finds hearty, warming dishes
- "healthy breakfast" → Finds nutritious morning meals
- "quick weeknight dinner" → Finds fast, simple recipes
- "party appetizers" → Finds finger foods and snacks

**UUID Search Use Cases:**
- Track recipes through the ETL pipeline
- Debug UUID changes after reprocessing
- Compare different versions of the same recipe
- Direct recipe lookups for debugging

Example: Search for `8faa4a5f-4f52-56db-92aa-fa574ed6b62c` to see full recipe details.

**Search API Server:**
For semantic search, start the API server:
```bash
source activate.sh
python -m recipes.api
# API runs on http://localhost:8000
```

See [SEMANTIC_SEARCH_CLIENT.md](./docs/SEMANTIC_SEARCH_CLIENT.md) for complete setup.

---

**📚 Complete Documentation**:
- [TEMPORAL_GUIDE.md](./docs/TEMPORAL_GUIDE.md) - Workflow orchestration guide
- [EMBEDDINGS_GUIDE.md](./docs/EMBEDDINGS_GUIDE.md) - Vector embeddings and semantic search
- [SEMANTIC_SEARCH_CLIENT.md](./docs/SEMANTIC_SEARCH_CLIENT.md) - Using semantic search from React client
- [ELASTICSEARCH_GUIDE.md](./docs/ELASTICSEARCH_GUIDE.md) - Elasticsearch setup and queries
- [README_PYTHON.md](./docs/README_PYTHON.md) - Detailed Python documentation
- [MIGRATION_GUIDE.md](./docs/MIGRATION_GUIDE.md) - TypeScript to Python migration
- [MIGRATION_COMPLETE.md](./docs/MIGRATION_COMPLETE.md) - Migration summary

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
- **PostgreSQL 15** - Relational database with pgvector extension
- **Elasticsearch 8** - Full-text search, semantic search, and recommendations
- **Vector Embeddings** - 384-dimensional embeddings using sentence-transformers
- **Docker** - Containerization and deployment
- **Redis** - Caching (future)

### Frontend (Separate)
- **React + TypeScript** - Modern web frontend (`client/`)
- **Vite** - Build tool with API proxy
- **FastAPI** - Search API server for semantic search

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

### Search API Operations
```bash
python -m recipes.api                  # Start search API server (port 8000)
python -m recipes.cli sync-search      # Sync recipes to Elasticsearch with embeddings
```

## 🐳 Docker Setup

### Start All Services
```bash
docker-compose up -d
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
docker-compose up -d postgres

# Start Temporal stack
docker-compose up -d temporal temporal-ui

# View worker logs
docker-compose logs -f recipes-worker

# Stop all services
docker-compose down
```

## 🏗️ Architecture

### Data Flow

1. **CSV Input** → CSV Parser → Raw Data
2. **Raw Data** → AI Service or Local Parser → Structured Recipe Data
3. **Recipe Data** → JSON Processor → JSON Files
4. **JSON Files** → Recipe Service → PostgreSQL Database (with embeddings)
5. **Database** → Search Service → Elasticsearch Index (with vector embeddings)
6. **Search API** → Generates query embeddings → kNN search in Elasticsearch

### Project Structure

```
recipes-etl/
├── src/recipes/              # Main Python package
│   ├── models/              # Pydantic data models
│   ├── services/            # Business logic (AI, DB, Search, Reddit, Embeddings)
│   ├── api/                 # FastAPI search endpoints
│   ├── workflows/           # Temporal workflows & activities
│   ├── database/            # Database connection & queries
│   ├── utils/               # Utility functions
│   ├── cli/                 # Command-line interface
│   └── config.py            # Configuration management
├── tests/                   # Test suite
├── scripts/                 # Setup & utility scripts
├── data/                    # Data directories
├── client/                  # React frontend (separate)
└── docker-compose.yml       # Docker configuration
```

## 🔄 Workflows

### Recipe Extraction Pipeline

1. **Get Raw Data**: Reddit, Kaggle CSV, or direct scraping
2. **Transform**: AI or local parsing to structured JSON
3. **Clean**: Deduplication and validation
4. **Load**: Insert into PostgreSQL database (with vector embeddings)
5. **Index**: Sync to Elasticsearch for search (with vector embeddings)
6. **Search**: Text search, semantic search, or hybrid search via API

### Current Features

- **Semantic Search**: Vector embeddings for meaning-based recipe discovery
- **Hybrid Search**: Combines keyword and semantic search
- **Vector Embeddings**: 384-dimensional embeddings using sentence-transformers
- **Search API**: FastAPI server for semantic search queries

### Future Features

- **Recommender System**:
  - Ingredient-based recommendations
  - Nutrition scoring
  - Cost optimization with grocery prices
  - User preference feedback loop
  - Skill level matching
  - Similar recipe recommendations using embeddings

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

### Maintenance Scripts

```bash
# Clean up legacy JSON files (without UUIDs)
./scripts/cleanup/delete_legacy_json_files.sh
```

This script helps maintain data consistency by removing old `entry_*.json` files that don't follow the UUID naming convention.

## 📈 Version History

### v2.2 (Current)
- **Semantic Search**: Vector embeddings for meaning-based recipe discovery
- **Search API**: FastAPI server for semantic and hybrid search
- **Vector Embeddings**: 384-dimensional embeddings using sentence-transformers
- **React Client Updates**: Semantic and hybrid search modes in web UI
- **Elasticsearch Integration**: kNN search with dense vector fields
- **Database Support**: pgvector extension for embedding storage (optional cache)

### v2.1
- data firehose from Reddit data (r/recipes)
- Kafka topic to collect scraper data

### v2.0 (Python)
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
docker-compose up -d postgres
python -m recipes.cli test-db
```

**AI service not working:**
```bash
# Check .env file has ANTHROPIC_API_KEY set
python -m recipes.cli test-ai
```

**Temporal worker not starting:**
```bash
docker-compose up -d temporal
docker-compose logs temporal
```

### Getting Help

- Check logs: `docker-compose logs -f`
- Run tests: `pytest tests/`
- Review documentation: [docs/](./docs/)
- Quick start: [docs/QUICK_START.md](./docs/QUICK_START.md)
- Temporal workflows: [docs/TEMPORAL_GUIDE.md](./docs/TEMPORAL_GUIDE.md)
- Code guidelines: [AGENTS.md](./AGENTS.md)

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
- **[Code Guidelines](./AGENTS.md)** - Style and testing standards
- **[Migration Notes](./docs/MIGRATION_COMPLETE.md)** - TypeScript to Python migration

See [docs/README.md](./docs/README.md) for the complete documentation index.

---

**Note**: This is the Python version of the recipes project. The TypeScript client application in `client/` remains unchanged and can communicate with this Python backend.
