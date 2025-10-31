# Recipes Python

AI-powered recipe data parser and analyzer - Python version with Temporal workflows.

## Features

- **AI-Powered Recipe Extraction**: Uses Anthropic Claude to extract structured recipe data from text
- **Local Recipe Parsing**: Fast, free alternative using pattern matching (no AI required)
- **Temporal Workflows**: Robust workflow orchestration with retry logic and parallel processing
- **PostgreSQL Database**: Relational database for storing recipes, ingredients, and measurements
- **Elasticsearch Integration**: Full-text search and recommendations
- **Command-Line Interface**: Easy-to-use CLI for all operations
- **Docker Support**: Containerized deployment with Docker Compose

## Quick Start

### Prerequisites

- Python 3.11+
- Poetry (recommended) or pip
- PostgreSQL 15+
- Temporal Server
- Redis (for Temporal)

### Installation

1. **Clone and setup**:
   ```bash
   git clone <repository>
   cd recipes-python
   python scripts/setup.py
   ```

2. **Install dependencies**:
   ```bash
   # Using Poetry (recommended)
   poetry install
   
   # Or using pip
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp env.example .env
   # Edit .env with your API keys and configuration
   ```

4. **Start services**:
   ```bash
   # Start PostgreSQL, Temporal, and other services
   docker-compose up -d postgres temporal
   
   # Or start all services
   docker-compose up -d
   ```

### Basic Usage

1. **Test connections**:
   ```bash
   python -m recipes.cli test-db
   python -m recipes.cli test-ai
   ```

2. **Process a single recipe**:
   ```bash
   # Using AI (slower, costs money)
   python -m recipes.cli process-recipe data/raw/recipes.csv 1 --use-ai
   
   # Using local parsing (faster, free)
   python -m recipes.cli process-recipe data/raw/recipes.csv 1
   ```

3. **Start the worker**:
   ```bash
   python -m recipes.worker
   ```

4. **Run batch processing**:
   ```bash
   python -m recipes.client batch data/raw/recipes.csv 1 10
   ```

## Architecture

### Core Components

- **Models**: Pydantic models for type-safe data structures
- **Services**: Business logic for AI, database, and search operations
- **Workflows**: Temporal workflows for batch processing and orchestration
- **Activities**: Individual tasks executed by workflows
- **CLI**: Command-line interface for all operations
- **Utils**: Utility functions for CSV parsing, JSON processing, etc.

### Data Flow

1. **CSV Input** → CSV Parser → Raw Data
2. **Raw Data** → AI Service or Local Parser → Structured Recipe Data
3. **Recipe Data** → JSON Processor → JSON Files
4. **JSON Files** → Recipe Service → PostgreSQL Database
5. **Database** → Search Service → Elasticsearch Index

## Workflows

### Recipe Processing Workflows

- **ProcessRecipeBatchWorkflow**: Sequential AI-based processing
- **ProcessRecipeBatchLocalWorkflow**: Sequential local parsing
- **ProcessRecipeBatchLocalParallelWorkflow**: Parallel local parsing

### Database Loading Workflows

- **LoadRecipesToDbWorkflow**: Sequential database loading
- **LoadRecipesToDbParallelWorkflow**: Parallel database loading

## CLI Commands

### Database Operations
```bash
python -m recipes.cli test-db          # Test database connection
python -m recipes.cli list-recipes     # List recent recipes
python -m recipes.cli search-recipes   # Search recipes
python -m recipes.cli stats           # Show database statistics
```

### Recipe Processing
```bash
python -m recipes.cli process-recipe <csv_file> <entry_number> [--use-ai]
python -m recipes.cli load-recipe <json_file>
```

### AI Operations
```bash
python -m recipes.cli test-ai         # Test AI service connection
```

## Configuration

### Environment Variables

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=recipes
DB_USER=postgres
DB_PASSWORD=postgres

# AI
ANTHROPIC_API_KEY=your_api_key_here

# Temporal
TEMPORAL_HOST=localhost
TEMPORAL_PORT=7233

# Elasticsearch
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
```

## Development

### Project Structure

```
src/recipes/
├── models/           # Pydantic data models
├── services/         # Business logic services
├── workflows/        # Temporal workflows and activities
├── database/         # Database connection and queries
├── utils/           # Utility functions
├── cli/             # Command-line interface
└── config.py        # Configuration management
```

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
black src/ tests/

# Type checking
mypy src/

# Linting
ruff src/ tests/
```

## Docker Deployment

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# Start specific services
docker-compose up -d postgres temporal

# View logs
docker-compose logs -f recipes-worker
```

### Services

- **postgres**: PostgreSQL database
- **temporal**: Temporal server
- **temporal-ui**: Temporal Web UI (http://localhost:8081)
- **elasticsearch**: Elasticsearch search engine
- **kibana**: Kibana visualization (http://localhost:5601)
- **recipes-worker**: Python Temporal worker

## Performance Comparison

| Feature | AI Parsing | Local Parsing | Parallel Local |
|---------|-----------|---------------|----------------|
| **Speed** | ~1.5s per recipe | ~0.05s per recipe | ~0.05s per recipe (parallel) |
| **Cost** | ~$0.001-0.01 per recipe | **FREE** | **FREE** |
| **Accuracy** | Excellent | Good | Good |
| **Best for** | Unstructured text | Structured data | Bulk processing |

## Migration from TypeScript

This Python version maintains full compatibility with the original TypeScript version:

- Same database schema
- Same workflow logic
- Same API endpoints
- Same data formats

### Key Improvements

- **Type Safety**: Pydantic models with runtime validation
- **Better Async Support**: Native Python async/await
- **Simplified Dependencies**: Fewer external dependencies
- **Better Error Handling**: More descriptive error messages
- **Enhanced CLI**: More intuitive command-line interface

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check PostgreSQL is running
   - Verify connection parameters in .env
   - Ensure database exists

2. **AI Service Not Working**
   - Verify ANTHROPIC_API_KEY is set
   - Check API key is valid and has credits
   - Test with: `python -m recipes.cli test-ai`

3. **Temporal Worker Not Starting**
   - Check Temporal server is running
   - Verify connection parameters
   - Check worker logs

4. **Import Errors**
   - Ensure PYTHONPATH includes src/
   - Run from project root directory
   - Check all dependencies are installed

### Getting Help

- Check logs: `docker-compose logs -f recipes-worker`
- Test connections: `python -m recipes.cli test-db`
- Verify setup: `python scripts/setup.py`

## License

MIT License - see LICENSE file for details.
