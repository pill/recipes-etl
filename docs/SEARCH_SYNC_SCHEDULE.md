# Elasticsearch Search Sync Schedule

This document explains how to use the Temporal scheduled workflow to automatically sync recipes from PostgreSQL to Elasticsearch on a regular interval.

## Overview

The search sync schedule automatically runs the Elasticsearch sync workflow at regular intervals (default: every hour). This keeps your Elasticsearch index up to date with the latest recipes from your PostgreSQL database.

## Components

### 1. SearchSyncWorkflow (`src/recipes/workflows/search_sync_workflow.py`)
- Temporal workflow that orchestrates the sync process
- Runs the sync activity with retry logic

### 2. sync_search_activity (`src/recipes/workflows/search_sync_activities.py`)
- Activity that performs the actual sync
- Connects to Elasticsearch and PostgreSQL
- Syncs recipes in batches

### 3. Schedule Runner (`scripts/runners/run_search_sync_schedule.py`)
- CLI tool to create and manage the schedule

## Usage

### Prerequisites

1. Start required services:
```bash
./CMD.sh start
```

2. Start a Temporal worker (in a separate terminal):
```bash
./CMD.sh worker
```

### Create a Schedule

Create a schedule to sync every hour (default):
```bash
./CMD.sh search-sync-schedule create
```

Create a schedule with custom interval (e.g., every 30 minutes):
```bash
./CMD.sh search-sync-schedule create --interval 30
```

Create a schedule with custom batch size:
```bash
./CMD.sh search-sync-schedule create --batch-size 500 --interval 60
```

### Manage the Schedule

**Check schedule status:**
```bash
./CMD.sh search-sync-schedule describe
```

**Trigger immediately (without waiting for next scheduled run):**
```bash
./CMD.sh search-sync-schedule trigger
```

**Pause the schedule:**
```bash
./CMD.sh search-sync-schedule pause
```

**Resume the schedule:**
```bash
./CMD.sh search-sync-schedule unpause
```

**Delete the schedule:**
```bash
./CMD.sh search-sync-schedule delete
```

## Schedule Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--schedule-id` | `search-sync-every-hour` | Unique identifier for the schedule |
| `--batch-size` | `1000` | Number of recipes to process per batch |
| `--interval` | `60` | Minutes between sync runs |
| `--host` | `localhost:7233` | Temporal server address |

## How It Works

1. The schedule triggers the `SearchSyncWorkflow` at the specified interval
2. The workflow executes the `sync_search_activity` 
3. The activity:
   - Connects to Elasticsearch
   - Checks Elasticsearch health
   - Creates/verifies the index
   - Fetches recipes from PostgreSQL in batches
   - Syncs them to Elasticsearch
4. Results are logged and visible in the Temporal UI

## Monitoring

### Temporal UI
View the schedule and workflow executions at:
- **Schedules**: http://localhost:8081/schedules/search-sync-every-hour
- **Workflows**: http://localhost:8081/workflows

### Logs
Worker logs will show:
- Sync start/completion
- Number of recipes synced
- Any errors that occurred

## Troubleshooting

### Schedule creation fails with "already exists"
Delete the existing schedule first:
```bash
./CMD.sh search-sync-schedule delete
./CMD.sh search-sync-schedule create
```

### Elasticsearch not healthy
Make sure Elasticsearch is running:
```bash
docker-compose ps elasticsearch
docker-compose up -d elasticsearch
```

Wait ~30 seconds for Elasticsearch to be ready.

### No worker running
Start the Temporal worker:
```bash
./CMD.sh worker
```

The worker must be running for scheduled workflows to execute.

### Check activity logs
Look at the worker terminal output for detailed activity logs showing:
- Elasticsearch connection status
- Batch processing progress
- Success/failure counts

## Best Practices

1. **Start with longer intervals**: Begin with 60+ minute intervals to avoid overloading Elasticsearch
2. **Monitor performance**: Watch Elasticsearch and PostgreSQL resource usage
3. **Adjust batch size**: Increase batch size (up to 2000+) if sync is too slow
4. **Use pause/unpause**: Temporarily pause during maintenance windows
5. **Check Temporal UI**: Regularly review the schedule history for failures

## Related Documentation

- [ELASTICSEARCH_GUIDE.md](./ELASTICSEARCH_GUIDE.md) - Elasticsearch setup and usage
- [TEMPORAL_SCHEDULES.md](./TEMPORAL_SCHEDULES.md) - General Temporal schedules guide
- [TEMPORAL_GUIDE.md](./TEMPORAL_GUIDE.md) - Temporal workflow orchestration

## Example Workflow

A typical workflow to set up and use the search sync schedule:

```bash
# 1. Start all services
./CMD.sh start

# 2. Wait for services to be ready (~30 seconds)
sleep 30

# 3. Start the Temporal worker (in a separate terminal)
./CMD.sh worker

# 4. Create the search sync schedule
./CMD.sh search-sync-schedule create --interval 60

# 5. Check the schedule was created
./CMD.sh search-sync-schedule describe

# 6. Trigger an immediate sync to test it
./CMD.sh search-sync-schedule trigger

# 7. Monitor in Temporal UI
# Visit: http://localhost:8081/schedules/search-sync-every-hour
```

The schedule will now run automatically every hour, keeping your Elasticsearch index in sync with PostgreSQL!

