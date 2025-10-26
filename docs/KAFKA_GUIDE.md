# Kafka Integration Guide

Event-driven recipe data collection using Apache Kafka for scalable, real-time recipe processing.

## Overview

Kafka enables decoupled, scalable recipe data processing:
- **Producer**: Reddit scraper publishes recipe events to Kafka
- **Kafka**: Event queue/stream for reliable message delivery
- **Consumer**: Processes recipe events (save to CSV, database, etc.)

## Architecture

```
┌──────────────┐      ┌────────┐      ┌───────────────┐
│   Reddit     │─────▶│ Kafka  │─────▶│   Consumer    │
│   Scraper    │      │ Topic  │      │  (Process &   │
│  (Producer)  │      │        │      │   Store)      │
└──────────────┘      └────────┘      └───────────────┘
```

### Benefits

1. **Decoupling**: Scraper and processor run independently
2. **Scalability**: Multiple consumers can process in parallel
3. **Reliability**: Kafka guarantees message delivery
4. **Flexibility**: Easy to add new consumers for different purposes
5. **Replay**: Can reprocess historical data

## Quick Start

### 1. Start Kafka Services

```bash
# Start Kafka (includes Zookeeper and Kafka UI)
docker-compose -f docker-compose.python.yml up -d zookeeper kafka kafka-ui

# Verify Kafka is running
docker ps | grep kafka
```

### 2. Scrape and Publish to Kafka

```bash
# Scrape once and publish to Kafka
./COMMANDS.sh scrape-kafka --limit 10

# Monitor continuously and publish to Kafka
./COMMANDS.sh scrape-kafka --continuous --interval 300
```

### 3. Consume and Process Events

```bash
# Consume events (process and load to database)
./COMMANDS.sh kafka-consumer

# Consume and save to CSV only
./COMMANDS.sh kafka-consumer --save-csv --no-process --no-db

# Consume 10 messages and exit
python scripts/processing/kafka_consumer.py --max-messages 10
```

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_RECIPES=reddit-recipes
KAFKA_CONSUMER_GROUP=recipe-processors
```

### Docker Services

Three Kafka-related services are configured in `docker-compose.python.yml`:

1. **Zookeeper** (port 2181) - Kafka coordination
2. **Kafka** (ports 9092, 29092) - Message broker
3. **Kafka UI** (port 8082) - Web-based monitoring

## Usage Examples

### Producer (Scraper)

#### Scrape to Kafka Once

```bash
# Basic usage
python scripts/processing/scrape_reddit_recipes.py --use-kafka --limit 25

# Different subreddit
python scripts/processing/scrape_reddit_recipes.py --use-kafka --subreddit cooking --limit 50
```

#### Continuous Monitoring

```bash
# Check every 5 minutes
python scripts/processing/scrape_reddit_recipes.py --use-kafka --continuous

# Check every 10 minutes
python scripts/processing/scrape_reddit_recipes.py --use-kafka --continuous --interval 600
```

### Consumer

#### Process and Load to Database

```bash
# Default: process and load to database
python scripts/processing/kafka_consumer.py
```

#### Save to CSV

```bash
# Save to CSV and load to database
python scripts/processing/kafka_consumer.py --save-csv

# Save to CSV only (no processing or database)
python scripts/processing/kafka_consumer.py --save-csv --no-process --no-db

# Custom CSV file
python scripts/processing/kafka_consumer.py --save-csv --csv-file data/my_recipes.csv
```

#### Processing Options

```bash
# Use AI for processing (default: local parser)
python scripts/processing/kafka_consumer.py --use-ai

# Disable database loading
python scripts/processing/kafka_consumer.py --no-db

# Disable recipe processing
python scripts/processing/kafka_consumer.py --no-process

# Consume maximum 100 messages and exit
python scripts/processing/kafka_consumer.py --max-messages 100
```

## Kafka Topics

### Default Topic: `reddit-recipes`

Recipe events are published to the `reddit-recipes` topic with the following structure:

```json
{
  "date": "2025-10-26",
  "num_comments": 45,
  "title": "Korean Beef Bulgogi",
  "user": "recipe_lover",
  "comment": "## Ingredients\n- 1 lb beef\n- 2 tbsp soy sauce\n...",
  "n_char": 856,
  "_kafka_metadata": {
    "source": "reddit-scraper",
    "version": "1.0"
  }
}
```

### Message Keys

Messages are keyed by Reddit username for partitioning.

## Monitoring with Kafka UI

Access the Kafka UI at **http://localhost:8082**

Features:
- View topics and messages
- Monitor consumer groups
- Check partition distribution
- View message contents
- Monitor lag and throughput

## Advanced Usage

### Multiple Consumers

Run multiple consumers in parallel for faster processing:

```bash
# Terminal 1: Save to CSV
python scripts/processing/kafka_consumer.py --save-csv --no-process --no-db

# Terminal 2: Process and load to database
python scripts/processing/kafka_consumer.py

# Terminal 3: Custom processing
python scripts/processing/kafka_consumer.py --use-ai
```

### Consumer Groups

Different consumer groups maintain separate offsets:

```bash
# Default group: recipe-processors
python scripts/processing/kafka_consumer.py

# Custom group (processes all messages from beginning)
KAFKA_CONSUMER_GROUP=my-processors python scripts/processing/kafka_consumer.py
```

### Programmatic Usage

```python
from recipes.services.kafka_service import get_kafka_service

# Publish a recipe
kafka_service = get_kafka_service()
recipe_data = {
    'date': '2025-10-26',
    'title': 'My Recipe',
    'user': 'chef_123',
    'comment': 'Recipe text here...',
    'num_comments': 10,
    'n_char': 500
}

kafka_service.publish_recipe(recipe_data, key='chef_123')

# Consume recipes
def process_recipe(recipe_data):
    print(f"Processing: {recipe_data['title']}")

kafka_service.consume_recipes(callback=process_recipe)
```

## Complete Workflow Example

### Scenario: Collect, Process, and Analyze Recipes

```bash
# 1. Start all services
docker-compose -f docker-compose.python.yml up -d

# 2. Start scraper (publish to Kafka)
./COMMANDS.sh scrape-kafka --continuous --interval 600 &

# 3. Start consumer (save to CSV for backup)
./COMMANDS.sh kafka-consumer --save-csv &

# 4. Monitor with Kafka UI
open http://localhost:8082

# 5. Search processed recipes
./COMMANDS.sh search "korean"

# 6. View stats
./COMMANDS.sh stats
```

## Troubleshooting

### Kafka Not Starting

```bash
# Check if ports are in use
lsof -i :9092
lsof -i :2181

# Restart services
docker-compose -f docker-compose.python.yml restart zookeeper kafka
```

### No Messages Being Consumed

```bash
# Check if topic exists
docker exec -it recipes-kafka kafka-topics --list --bootstrap-server localhost:9092

# Check topic has messages
docker exec -it recipes-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic reddit-recipes \
  --from-beginning \
  --max-messages 1
```

### Consumer Lag

Check Kafka UI at http://localhost:8082 to monitor consumer lag.

### Connection Errors

Verify Kafka health:

```python
from recipes.services.kafka_service import get_kafka_service

kafka = get_kafka_service()
if kafka.health_check():
    print("✅ Kafka is healthy")
else:
    print("❌ Kafka connection failed")
```

## Performance Tips

1. **Batch Size**: Adjust consumer `max_poll_records` for optimal throughput
2. **Partitions**: Increase topic partitions for parallel processing
3. **Compression**: Enable compression for large recipe texts
4. **Retention**: Set appropriate retention policy for your use case

## Configuration Options

### Producer Configuration

- `acks='all'`: Wait for all replicas (highest durability)
- `retries=3`: Retry failed sends
- `compression_type`: Optional compression (gzip, snappy, lz4)

### Consumer Configuration

- `auto_offset_reset='earliest'`: Start from beginning for new groups
- `enable_auto_commit=True`: Automatically commit offsets
- `max_poll_records=10`: Messages per poll

## Deduplication

**Important**: Kafka does NOT automatically handle duplicates!

We handle duplicates at the **database layer**:

### Database-Level Deduplication
- The `load_json_to_db` function checks `get_by_title` before inserting
- If a recipe with the same title exists, it returns `alreadyExists: True`
- This works across all consumers and persists across restarts

```python
# In load_json_to_db (workflows/activities.py)
existing = await RecipeService.get_by_title(recipe.title)
if existing:
    return {
        'success': True,
        'alreadyExists': True,
        'recipeId': existing.id
    }
```

### CSV Mode (Scraper Only)
- When saving to CSV (not Kafka), the scraper tracks `processed_ids` in-memory
- This prevents duplicate entries within a single scraping session
- Only applies to `--output` CSV mode, not Kafka mode

**See**: [KAFKA_DEDUPLICATION.md](./KAFKA_DEDUPLICATION.md) for advanced strategies

## Next Steps

After setting up Kafka:

1. **Scale**: Add more consumers for parallel processing
2. **Monitor**: Set up alerts on consumer lag
3. **Deduplicate**: Implement database-backed deduplication for production
4. **Analyze**: Use Kafka Streams for real-time analytics
5. **Archive**: Set up archival to S3/object storage

## Resources

- **Kafka UI**: http://localhost:8082
- **Kafka Docs**: https://kafka.apache.org/documentation/
- **kafka-python**: https://kafka-python.readthedocs.io/
- **Deduplication Guide**: [KAFKA_DEDUPLICATION.md](./KAFKA_DEDUPLICATION.md)

