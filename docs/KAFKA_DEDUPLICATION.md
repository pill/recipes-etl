# Kafka Deduplication Strategy

## The Problem

**Kafka does NOT automatically handle duplicates.** Kafka guarantees **at-least-once delivery**, which means:

- ✅ Messages are never lost
- ❌ Same message can be delivered multiple times
- ❌ No built-in deduplication

### Why Duplicates Happen

1. **Producer Retries**: Network issues cause message to be sent multiple times
2. **Consumer Restarts**: Crashes before committing offset, reprocesses messages
3. **Scraper Re-runs**: Same Reddit post scraped multiple times
4. **Partition Rebalancing**: Messages reprocessed during consumer group changes

## Our Solution: Database-Level Deduplication

We handle duplicates at the **database layer** where it matters most:

### 1. Database-Level Deduplication (Primary Method)

The database checks for existing recipes before inserting:

```python
# In load_json_to_db (workflows/activities.py)
existing = await RecipeService.get_by_title(recipe.title)
if existing:
    return {
        'success': True,
        'alreadyExists': True,
        'recipeId': existing.id,
        'title': recipe.title
    }
```

**How it works:**
- Checks database for existing recipe with same title
- If found, returns success without inserting
- If not found, inserts the new recipe

**Benefits:**
- ✅ Survives restarts
- ✅ Works across multiple consumers
- ✅ Permanent deduplication
- ✅ Single source of truth

**Limitations:**
- Requires database query (slight performance impact)
- Based on title matching only

### 2. Message Keys for Partitioning

Each message uses username as key:

```python
# Publish with user as key
success = self.kafka_service.publish_recipe(
    recipe_data,
    key=recipe_data['user']
)
```

**Benefits:**
- Messages from same user go to same partition (ordering)
- Consistent partitioning
- Better distribution across partitions

### 3. CSV Mode Deduplication (Scraper Only)

When using CSV output (not Kafka), the scraper tracks in-memory:

```python
# CSV mode only
if unique_id in self.processed_ids:
    continue  # Skip duplicate
self.processed_ids.add(unique_id)
```

**How it works:**
- Only active when using `--output` (CSV mode)
- Not used in Kafka mode (`--use-kafka`)
- Prevents duplicate CSV entries within a session

## Deduplication Strategies

### Strategy 1: Database-Backed (Current Implementation) ✅

Check database before inserting:

```python
# Check if recipe already exists in database
existing = await RecipeService.get_by_title(recipe.title)
if existing:
    print("Already in database, skipping...")
    return
```

**Pros:**
- ✅ Survives restarts
- ✅ Works across multiple consumers
- ✅ Permanent deduplication
- ✅ Single source of truth

**Cons:**
- ❌ Requires database query (slight overhead)
- ❌ Based on title matching

### Strategy 2: Kafka Exactly-Once Semantics

Use Kafka's transactional API:

```python
# Producer
producer = KafkaProducer(
    enable_idempotence=True,  # Prevents duplicate sends
    transactional_id='recipe-producer-1'
)

# Consumer
consumer = KafkaConsumer(
    isolation_level='read_committed'  # Only reads committed messages
)
```

**Pros:**
- ✅ Kafka-native solution
- ✅ True exactly-once within Kafka
- ✅ No application logic needed

**Cons:**
- ❌ Performance impact
- ❌ More complex setup
- ❌ Doesn't prevent business-level duplicates

## Current Implementation Details

### Producer (Scraper)

```python
# Location: scripts/processing/scrape_reddit_recipes.py

# Publish to Kafka with user as key
success = self.kafka_service.publish_recipe(
    recipe_data,
    key=recipe_data['user']  # Username for partitioning
)
```

### Consumer

```python
# Location: scripts/processing/kafka_consumer.py

# Processes all messages - database handles deduplication
def handle_message(self, recipe_data: Dict[str, Any]):
    # ... save to CSV (optional)
    # ... process recipe (optional)
    # ... load to database (handles duplicates)
```

### Database Layer

```python
# Location: workflows/activities.py (load_json_to_db)

# Check if recipe already exists
existing = await RecipeService.get_by_title(recipe.title)
if existing:
    return {
        'success': True,
        'alreadyExists': True,
        'recipeId': existing.id
    }

# Create new recipe
created_recipe = await RecipeService.create(recipe)
```

## Statistics Tracking

The consumer reports processing stats:

```
📊 STATISTICS
============================================================
📨 Messages received: 100
💾 Saved to CSV: 100
⚙️  Processed: 100
💾 Loaded to DB: 85 (15 were duplicates, handled by DB)
❌ Errors: 0

ℹ️  Note: Database handles duplicates via get_by_title check
============================================================
```

## Testing Deduplication

### Test 1: Publish Same Recipe Twice

```bash
# Terminal 1: Start consumer
./COMMANDS.sh kafka-consumer

# Terminal 2: Scrape same posts twice
./COMMANDS.sh scrape-kafka --limit 5
./COMMANDS.sh scrape-kafka --limit 5  # Same posts again

# Result: Second run publishes 0 recipes (already processed)
```

### Test 2: Database Deduplication

```python
# Manually publish duplicate message
from recipes.services.kafka_service import get_kafka_service

kafka = get_kafka_service()
recipe = {
    'title': 'Test Recipe',
    'user': 'test_user',
    'date': '2025-10-26',
    'comment': 'Test content',
    'num_comments': 0,
    'n_char': 12
}

# Publish same message twice
kafka.publish_recipe(recipe)
kafka.publish_recipe(recipe)

# Consumer processes both, but database only inserts first one
# Second one returns: alreadyExists: True
```

### Test 3: Check Database

```bash
# After consuming, check if duplicates were prevented
./COMMANDS.sh list

# Or query database directly
python -m recipes.cli search "Test Recipe"
```

## Production Recommendations

For production use, combine multiple strategies:

### 1. Idempotent Producer
```python
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    enable_idempotence=True,
    acks='all',
    max_in_flight_requests_per_connection=5
)
```

### 2. Database-Level Deduplication
```python
# Before saving to database
existing = await RecipeService.get_by_title(recipe.title)
if existing:
    return {'success': True, 'alreadyExists': True}
```

### 3. Distributed State (Redis/Memcached)
```python
import redis

redis_client = redis.Redis(host='localhost', port=6379)

# Check if processed
if redis_client.sismember('processed_recipes', unique_id):
    return  # Skip duplicate

# Mark as processed
redis_client.sadd('processed_recipes', unique_id)
```

### 4. Kafka Streams with State Store
```python
# For advanced use cases
from kafka_streams import KafkaStreams, StreamsBuilder

builder = StreamsBuilder()
stream = builder.stream('reddit-recipes')

# Deduplicate using key-based state store
deduplicated = stream.transform(
    lambda key, value, state_store: 
        None if state_store.get(key) else value
)
```

## Trade-offs

| Strategy | Speed | Durability | Scalability | Complexity | Status |
|----------|-------|------------|-------------|------------|--------|
| Database | ⚡⚡ | ✅ | ✅ | ✅ Simple | **✅ Current** |
| Redis | ⚡⚡⚡ | ✅ | ✅ | ⚡ Medium | Optional |
| Kafka Exactly-Once | ⚡⚡ | ✅ | ✅ | ⚡⚡ Complex | Advanced |

## Summary

**Current Implementation:**
- ✅ **Database-level deduplication** (primary method)
- ✅ Checks `get_by_title` before inserting
- ✅ Works across all consumers and restarts
- ✅ Single source of truth
- ✅ CSV mode: In-memory deduplication (scraper only)

**Benefits:**
- Simple and reliable
- No external dependencies (beyond PostgreSQL)
- Works out of the box
- Handles all edge cases

**Upgrade Path:**
1. ✅ Database checks (already implemented)
2. Add Redis for faster duplicate checks (optional)
3. Enable Kafka idempotent producer (optional)
4. Implement Kafka exactly-once semantics (advanced)

**Best Practice:**
Database-level deduplication provides the best balance of simplicity, reliability, and correctness for most use cases.

