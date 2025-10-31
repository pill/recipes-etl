# Temporal Recipe Processing Guide (Python)

This guide explains how to use the Temporal workflow system with Python to process CSV recipe entries in batches with rate limiting.

## Overview

The Temporal workflow system allows you to:
- Process multiple CSV entries in batches
- Control the rate of API calls to avoid hitting Anthropic rate limits
- Resume processing if interrupted
- Monitor workflow execution status
- Scale processing across multiple workers
- Use AI or local parsing (fast and free)

## Architecture

1. **Activities** (`src/recipes/workflows/activities.py`): Processes a single CSV entry
2. **Workflows** (`src/recipes/workflows/workflows.py`): Orchestrates batch processing with delays
3. **Worker** (`src/recipes/worker.py`): Runs activities and workflows
4. **Client** (`src/recipes/client.py`): Starts workflow executions

## Prerequisites

### 1. Python Environment

```bash
# Activate virtual environment
source venv/bin/activate

# Or install dependencies if not done yet
python3 install.py
```

### 2. Install and Start Temporal Server

Using Docker (recommended):

```bash
# Start Temporal using the Python Docker Compose
docker-compose up -d temporal temporal-ui

# Or start all services including database
docker-compose up -d
```

Or using Temporal CLI:

```bash
# macOS
brew install temporal

# Start local dev server
temporal server start-dev
```

### 3. Verify Temporal is Running

- **Temporal Web UI**: http://localhost:8081 (Python Docker Compose)
- **Or**: http://localhost:8233 (standard Temporal)

## Usage

### Step 1: Start the Worker

In one terminal, start the worker that will execute your activities:

```bash
# Activate virtual environment
source venv/bin/activate

# Start worker
python -m recipes.worker
```

The worker will:
- Connect to the Temporal server at `localhost:7233`
- Wait for workflow tasks on the `recipe-processing` queue
- Process activities with configured retry policies

**Environment Configuration:**

```bash
# Set Temporal host (optional, defaults to localhost:7233)
export TEMPORAL_HOST=localhost
export TEMPORAL_PORT=7233

# Start worker
python -m recipes.worker
```

### Step 2: Start a Workflow

In another terminal, start a workflow to process a batch of entries:

```bash
# Activate virtual environment
source venv/bin/activate

# Run workflow
python -m recipes.client <workflow_type> <csv-file-path> <start-entry> <end-entry> [options]
```

**Workflow Types:**

- `batch` - AI-based processing (slower, costs money)
- `batch-local` - Local parsing (faster, FREE)
- `batch-parallel` - Parallel local parsing (fastest, FREE)

**Examples:**

```bash
# AI-based processing: entries 1-10 with 2 second delay
python -m recipes.client batch data/raw/Reddit_Recipes.csv 1 10

# Local parsing: entries 1-100 with 50ms delay (FAST and FREE)
python -m recipes.client batch-local data/raw/Reddit_Recipes.csv 1 100

# Parallel local parsing: entries 1-100 with batch size 10 (FASTEST)
python -m recipes.client batch-parallel data/raw/Reddit_Recipes.csv 1 100 10
```

**Arguments:**
- `workflow_type`: Type of processing (batch, batch-local, batch-parallel)
- `csv-file-path`: Path to your CSV file
- `start-entry`: First entry number (1-indexed)
- `end-entry`: Last entry number (inclusive)
- `batch-size`: (parallel only) Number of entries to process simultaneously

### Step 3: Monitor Progress

**In the terminal:**
Both the worker and client will show detailed logs of the processing.

**In the Temporal Web UI:**
1. Open http://localhost:8081 (or http://localhost:8233)
2. Click on the workflow ID to see details
3. View execution history, pending activities, and results

**Detaching from the client:**
You can press Ctrl+C on the client terminal - the workflow continues running in the background. Check the Web UI to monitor progress.

## CLI Alternative

You can also use the CLI for single recipe processing:

```bash
# Process single recipe with AI
python -m recipes.cli process-recipe data/raw/recipes.csv 5 --use-ai

# Process single recipe with local parsing (FREE)
python -m recipes.cli process-recipe data/raw/recipes.csv 5
```

## Rate Limiting Strategy

### Anthropic Rate Limits

Default limits (as of 2024):
- **Claude Sonnet/Haiku**: 50 requests per minute
- **Higher tiers**: 100-1000+ requests per minute

### Recommended Settings

**For AI-based processing (50 requests/minute limit):**
```python
# 1200ms delay = 50 requests/min (safe)
python -m recipes.client batch data/raw/Reddit_Recipes.csv 1 100

# Workflows default to 1000ms (1 second) delay
```

**For local parsing (NO API LIMITS):**
```python
# Local parsing is FREE and fast - no rate limits!
python -m recipes.client batch-local data/raw/Reddit_Recipes.csv 1 1000

# Parallel processing for maximum speed
python -m recipes.client batch-parallel data/raw/Reddit_Recipes.csv 1 1000 20
```

### Performance Comparison

| Method | Speed | Cost | Best For |
|--------|-------|------|----------|
| **AI (batch)** | ~1.5s/recipe | $0.001-0.01 per recipe | Unstructured text |
| **Local (batch-local)** | ~0.05s/recipe | **FREE** | Structured data |
| **Parallel Local** | ~0.01s/recipe | **FREE** | **Bulk processing (1000s)** |

**Recommendation**: Use local or parallel local parsing for most cases. It's 30x faster and completely free!

## Output Files

Processed entries are saved to:
```
data/stage/entry_{number}.json
```

Example:
- `data/stage/entry_1.json`
- `data/stage/entry_2.json`

**Skip Logic:** If a file already exists, it will be skipped (no re-processing).

## Common Workflows

### Process Entire CSV with Local Parsing (Recommended)

```bash
# Start worker
python -m recipes.worker

# Process 1000 entries with parallel local parsing (FAST and FREE)
python -m recipes.client batch-parallel data/raw/recipes.csv 1 1000 20
```

### Process with AI (for unstructured text)

```bash
# Start worker
python -m recipes.worker

# Process entries 1-50 with AI
python -m recipes.client batch data/raw/Reddit_Recipes.csv 1 50
```

### Resume Failed Batch

If processing fails, you can resume from where it stopped:

```bash
# Original batch failed at entry 25
# Resume from entry 25 onwards
python -m recipes.client batch-local data/raw/recipes.csv 25 100
```

### Process Different CSV Files

```bash
# Start worker once
python -m recipes.worker

# Terminal 2: Process first CSV
python -m recipes.client batch-local data/raw/Reddit_Recipes.csv 1 100

# Terminal 3 (after first finishes): Process second CSV  
python -m recipes.client batch-local data/raw/stromberg_data.csv 1 100
```

## Database Loading Workflow

Load extracted JSON files into the database efficiently.

### Quick Start

```bash
# Terminal 1: Worker (if not already running)
python -m recipes.worker

# Terminal 2: Load single recipe
python -m recipes.cli load-recipe data/stage/entry_1.json
```

### Using Temporal for Batch Loading

```python
# In your Python code
from recipes.client import run_load_recipes_workflow
import asyncio

async def load_batch():
    json_files = [
        "data/stage/entry_1.json",
        "data/stage/entry_2.json",
        # ... more files
    ]
    
    # Sequential loading
    result = await run_load_recipes_workflow(
        json_file_paths=json_files,
        delay_between_activities_ms=100
    )
    
    # Or parallel loading (faster)
    result = await run_load_recipes_workflow(
        json_file_paths=json_files,
        parallel=True,
        batch_size=10,
        delay_between_batches_ms=0
    )
    
    print(f"Loaded {result['successful']} recipes")

asyncio.run(load_batch())
```

### Features

- **Duplicate Detection**: Automatically skips recipes already in database (by title)
- **Fast Processing**: Typical rate is 10+ recipes/second
- **Error Handling**: Failed inserts are logged but don't stop the workflow
- **Resume Support**: Can re-run to process any new files added

### Monitoring

Track database loading:
- View real-time progress in Temporal Web UI
- Check CLI output for success/failure counts
- Review logs for any errors

## Troubleshooting

### "Connection refused" error

**Problem:** Temporal server is not running

**Solution:**
```bash
# Check if Temporal is running
docker-compose ps

# Start Temporal if needed
docker-compose up -d temporal temporal-ui
```

### Rate limit errors (AI processing)

**Problem:** Hitting API rate limits

**Solution:** Switch to local parsing (FREE and faster):
```bash
python -m recipes.client batch-local data/raw/recipes.csv 1 100
```

### Worker not picking up tasks

**Problem:** Worker and client configuration mismatch

**Solution:**
```bash
# Check worker logs
docker-compose logs recipes-worker

# Verify Temporal connection
python -m recipes.cli test-db
```

### Import errors

**Problem:** Virtual environment not activated

**Solution:**
```bash
# Always activate venv before running Python commands
source venv/bin/activate

# Or use the full path
venv/bin/python -m recipes.worker
```

## Environment Variables

Create/update your `.env` file:

```bash
# Required
ANTHROPIC_API_KEY=your_api_key_here

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=recipes
DB_USER=postgres
DB_PASSWORD=postgres

# Temporal configuration
TEMPORAL_HOST=localhost
TEMPORAL_PORT=7233
```

## Docker Deployment

Run everything in Docker:

```bash
# Start all services (database, Temporal, worker)
docker-compose up -d

# View worker logs
docker-compose logs -f recipes-worker

# Check services status
docker-compose ps
```

## Advanced: Multiple Workers

Scale processing by running multiple workers:

```bash
# Terminal 1-3: Start 3 workers
source venv/bin/activate
python -m recipes.worker

# Terminal 4: Start large batch
python -m recipes.client batch-local data/raw/recipes.csv 1 500
```

Work is automatically distributed across all available workers.

## Python vs TypeScript Differences

| Feature | TypeScript | Python |
|---------|-----------|--------|
| **Workflow Definition** | Function-based | Class-based with decorators |
| **Type Safety** | Compile-time | Runtime with Pydantic |
| **Activity Timeout** | 10 minutes | 10 minutes (same) |
| **Retry Policy** | Same logic | Same logic |
| **Task Queue** | `recipe-processing` | `recipe-processing` (same) |

## Benefits of Using Temporal with Python

1. **Reliability**: Workflows survive process crashes and restarts
2. **Observability**: Track every step in the Web UI
3. **Rate Limiting**: Built-in delays and concurrency control
4. **Scalability**: Add more workers to process faster
5. **Idempotency**: Already-processed entries are skipped
6. **Resume**: Continue from where you left off if interrupted
7. **Type Safety**: Pydantic models provide runtime validation
8. **Better Performance**: Python async/await for efficient I/O

## Quick Reference

```bash
# Setup
python3 install.py
source venv/bin/activate

# Start services
docker-compose up -d

# Start worker
python -m recipes.worker

# Process recipes (pick one):
python -m recipes.client batch data/file.csv 1 50           # AI (slow, costs $)
python -m recipes.client batch-local data/file.csv 1 1000   # Local (fast, FREE)
python -m recipes.client batch-parallel data/file.csv 1 1000 20  # Parallel (fastest, FREE)

# Load to database
python -m recipes.cli load-recipe data/stage/entry_1.json

# Monitor
http://localhost:8081  # Temporal Web UI
```

## Recommended Workflow

For most users, we recommend:

1. **Start with local parsing** - It's fast and free
2. **Use parallel processing** - Process 1000s of recipes quickly
3. **Reserve AI for complex cases** - Only when local parsing isn't accurate enough
4. **Monitor via Web UI** - Track progress in real-time
5. **Load to database in batches** - Use CLI or Temporal workflows

This approach is 30x faster and completely free compared to AI-based processing!
