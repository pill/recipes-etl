# Temporal Schedules for Reddit Recipe Scraping

Run the Reddit scraper every 5 minutes (or custom interval) using [Temporal Schedules](https://temporal.io/blog/temporal-schedules-reliable-scalable-and-more-flexible-than-cron-jobs) - a better alternative to cron jobs.

## Why Temporal Schedules?

Temporal Schedules are superior to cron jobs:

✅ **Enhanced control & observability** - Monitor, pause, resume, and trigger schedules  
✅ **Flexible scheduling** - Handle overlapping runs, backfill missed runs  
✅ **No external dependencies** - Built into Temporal  
✅ **Reliable execution** - Guaranteed delivery with retry logic  
✅ **Easy management** - Start, stop, pause via CLI or UI

## Quick Start

### 1. Start Services

```bash
# Start all services (including Temporal)
./COMMANDS.sh start

# Start Temporal worker
./COMMANDS.sh worker
```

### 2. Create Schedule (Every 5 Minutes)

```bash
# Create schedule to run every 5 minutes
./COMMANDS.sh schedule create

# Custom interval (every 10 minutes)
./COMMANDS.sh schedule create --interval 10

# Different subreddit
./COMMANDS.sh schedule create --subreddit cooking --limit 50
```

### 3. Monitor in Temporal UI

Open http://localhost:8081/schedules to view:
- Schedule status (active/paused)
- Recent runs
- Upcoming runs
- Execution history

## Schedule Management

### View Schedule Status

```bash
./COMMANDS.sh schedule describe
```

Output:
```
📋 Schedule: reddit-scraper-every-5min
============================================================
State: Active
Actions taken: 12
Recent actions: 5

Recent runs:
  - reddit-scraper-reddit-scraper-every-5min-2025-10-26T10:30:00Z
  - reddit-scraper-reddit-scraper-every-5min-2025-10-26T10:25:00Z
  - reddit-scraper-reddit-scraper-every-5min-2025-10-26T10:20:00Z
============================================================
```

### Pause Schedule

```bash
# Pause scraping temporarily
./COMMANDS.sh schedule pause
```

### Resume Schedule

```bash
# Resume after pause
./COMMANDS.sh schedule unpause
```

### Trigger Immediately

```bash
# Run scraper right now (doesn't affect schedule)
./COMMANDS.sh schedule trigger
```

### Delete Schedule

```bash
# Stop and remove the schedule
./COMMANDS.sh schedule delete
```

## Advanced Usage

### Python API

```python
from scripts.runners.run_reddit_schedule import create_schedule

# Create custom schedule
await create_schedule(
    schedule_id="my-custom-scraper",
    subreddit="cooking",
    limit=50,
    interval_minutes=10,
    use_kafka=True
)
```

### Multiple Schedules

```bash
# Create schedule for r/recipes (every 5 min)
./COMMANDS.sh schedule create --schedule-id recipes-5min --subreddit recipes --interval 5

# Create schedule for r/cooking (every 15 min)  
./COMMANDS.sh schedule create --schedule-id cooking-15min --subreddit cooking --interval 15

# List all schedules in Temporal UI
open http://localhost:8081/schedules
```

### Backfill Missed Runs

If the worker was down, Temporal can backfill missed runs:

```python
# Via Python API
handle = client.get_schedule_handle("reddit-scraper-every-5min")
await handle.backfill([
    # Backfill specific time ranges
])
```

## Configuration

### Schedule Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--schedule-id` | `reddit-scraper-every-5min` | Unique schedule identifier |
| `--subreddit` | `recipes` | Subreddit to scrape |
| `--limit` | `25` | Posts to check per run |
| `--interval` | `5` | Minutes between runs |
| `--no-kafka` | `false` | Save to CSV instead of Kafka |

### Workflow Details

- **Workflow**: `RedditScraperWorkflow`
- **Activity**: `scrape_reddit_recipes_activity`
- **Task Queue**: `recipe-tasks`
- **Timeout**: 10 minutes per run
- **Retry Policy**: 3 attempts with exponential backoff

## Complete Workflow

### Event-Driven Recipe Collection

```bash
# 1. Start all services
./COMMANDS.sh start

# 2. Start Temporal worker
./COMMANDS.sh worker

# 3. Create schedule (scraper runs every 5 min, publishes to Kafka)
./COMMANDS.sh schedule create --interval 5

# 4. Start Kafka consumer (processes events from Kafka)
./COMMANDS.sh kafka-consumer --save-csv

# 5. Monitor
open http://localhost:8081/schedules        # Temporal schedules
open http://localhost:8082                  # Kafka UI
```

### Data Flow

```
┌─────────────────┐
│  Temporal       │
│  Schedule       │ ⏰ Every 5 minutes
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Reddit         │
│  Scraper        │ 📡 Fetch new posts
│  Workflow       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Kafka          │ 📨 Message queue
│  Topic          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Consumer       │ ⚙️  Process & store
│  (Database)     │
└─────────────────┘
```

## Monitoring

### Temporal UI

View comprehensive schedule information:

1. **Navigate to Schedules**: http://localhost:8081/schedules
2. **Click schedule**: `reddit-scraper-every-5min`
3. **View details**:
   - Recent runs (success/failure)
   - Upcoming runs
   - Schedule configuration
   - Execution history

### Workflow Runs

Each schedule execution creates a workflow run:

1. **Navigate to Workflows**: http://localhost:8081/workflows
2. **Filter** by `reddit-scraper` prefix
3. **Click workflow** to see:
   - Input parameters
   - Activity results
   - Execution timeline
   - Logs and errors

## Troubleshooting

### Schedule Not Running

```bash
# Check schedule status
./COMMANDS.sh schedule describe

# Check if paused
# If paused, unpause it
./COMMANDS.sh schedule unpause

# Check worker is running
# Worker must be running to execute workflows
ps aux | grep worker
```

### Worker Not Running

```bash
# Start worker in foreground (see logs)
./COMMANDS.sh worker

# Or start in background
nohup ./COMMANDS.sh worker > worker.log 2>&1 &
```

### View Workflow Errors

```bash
# Check Temporal UI for failed workflows
open http://localhost:8081/workflows

# Filter by:
# - Status: Failed
# - Workflow Type: RedditScraperWorkflow
```

### Schedule Already Exists

```bash
# Delete existing schedule first
./COMMANDS.sh schedule delete

# Then create new one
./COMMANDS.sh schedule create --interval 5
```

## Comparison with Alternatives

| Feature | Temporal Schedule | Cron | Kubernetes CronJob |
|---------|------------------|------|-------------------|
| Reliability | ✅ Guaranteed | ❌ Best effort | ⚡ Good |
| Observability | ✅ Full history | ❌ Limited | ⚡ Moderate |
| Pause/Resume | ✅ Yes | ❌ No | ❌ No |
| Backfill | ✅ Yes | ❌ No | ❌ No |
| Retry Logic | ✅ Built-in | ❌ Manual | ⚡ Limited |
| Complexity | ⚡ Moderate | ✅ Simple | ❌ Complex |
| Scale | ✅ Excellent | ❌ Limited | ✅ Excellent |

## Benefits

1. **Visibility**: See all scheduled runs in one place
2. **Control**: Pause, resume, trigger on-demand
3. **Reliability**: Automatic retries on failure
4. **Flexibility**: Change schedule without code changes
5. **History**: Full execution history and logs
6. **Testing**: Trigger runs manually for testing

## Next Steps

1. **Alerts**: Set up alerts for failed workflows
2. **Metrics**: Monitor execution times and success rates
3. **Multiple Subreddits**: Create schedules for different subreddits
4. **Dynamic Scheduling**: Adjust intervals based on activity
5. **Conditional Logic**: Skip runs if no new posts

## Resources

- [Temporal Schedules Docs](https://docs.temporal.io/workflows#schedule)
- [Temporal Schedules Blog](https://temporal.io/blog/temporal-schedules-reliable-scalable-and-more-flexible-than-cron-jobs)
- [Temporal Python SDK](https://docs.temporal.io/dev-guide/python)
- [Temporal UI](http://localhost:8081)

