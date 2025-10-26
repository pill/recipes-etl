# Reddit Recipe Scraper Guide

A script to periodically scrape recipes from Reddit and save them in CSV format, matching the structure of `Reddit_Recipes.csv`.

## Features

- ✅ Scrapes recipes from any Reddit subreddit
- ✅ Extracts recipe text from OP's comments or self-text
- ✅ Saves in CSV format matching existing Reddit_Recipes data
- ✅ Tracks processed posts to avoid duplicates
- ✅ Runs once or continuously on a schedule
- ✅ Configurable check interval and post limit

## CSV Format

The scraper saves data in the following format:

| Field | Description |
|-------|-------------|
| `date` | Post creation date (YYYY-MM-DD) |
| `num_comments` | Number of comments on the post |
| `title` | Recipe title (post title) |
| `user` | Reddit username of the post author |
| `comment` | Recipe text (from OP's comment or self-text) |
| `n_char` | Character count of the recipe text |

## Prerequisites

1. **Reddit API Credentials** - Add to your `.env` file:
   ```bash
   REDDIT_APP_NAME=your_app_name
   REDDIT_CLIENT_ID=your_client_id
   REDDIT_CLIENT_SECRET=your_client_secret
   REDDIT_USERNAME=your_reddit_username
   REDDIT_PASSWORD=your_reddit_password
   ```

2. **Python Dependencies** - Already included in `requirements.txt`:
   - `asyncpraw` - Async Reddit API wrapper
   - `python-dotenv` - Environment variable management

## Usage

### Run Once (Default)

Scrape recent posts once and exit:

```bash
# Scrape r/recipes (default)
python scripts/processing/scrape_reddit_recipes.py

# Scrape a different subreddit
python scripts/processing/scrape_reddit_recipes.py --subreddit cooking

# Check more posts
python scripts/processing/scrape_reddit_recipes.py --limit 50
```

### Run Continuously

Monitor the subreddit on a schedule:

```bash
# Check every 5 minutes (default)
python scripts/processing/scrape_reddit_recipes.py --continuous

# Check every 30 minutes (1800 seconds)
python scripts/processing/scrape_reddit_recipes.py --continuous --interval 1800

# Monitor r/cooking instead of r/recipes
python scripts/processing/scrape_reddit_recipes.py --continuous --subreddit cooking
```

### Custom Output File

Specify a custom output CSV file:

```bash
python scripts/processing/scrape_reddit_recipes.py --output data/raw/my_recipes.csv
```

## Command-Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--subreddit` | `recipes` | Subreddit to scrape |
| `--output` | `data/raw/Reddit_{subreddit}_scraped.csv` | Output CSV file path |
| `--interval` | `300` | Check interval in seconds (continuous mode) |
| `--limit` | `25` | Number of recent posts to check per run |
| `--continuous` | `false` | Run continuously (default: run once) |

## How It Works

1. **Authentication**: Connects to Reddit API using credentials from `.env`

2. **Fetch Posts**: Gets recent posts from the specified subreddit

3. **Extract Recipe**: For each post:
   - Checks if recipe is in the post's self-text
   - If not, searches OP's comments for recipe text
   - Looks for keywords: "ingredients", "instructions", "prep time", etc.

4. **Save Data**: Appends new recipes to CSV file

5. **Track Processed**: Maintains a set of processed posts to avoid duplicates

6. **Repeat** (if continuous): Waits for the specified interval and repeats

## Recipe Detection

The scraper looks for recipe indicators in OP's comments or self-text:

- `ingredients`
- `instructions`
- `preparation`
- `prep time`
- `cook time`
- `total time`
- `servings`

If any of these keywords are found in OP's content, it's saved as a recipe.

## Examples

### Example 1: Daily Scrape (Cron Job)

Add to your crontab to run daily at 8 AM:

```bash
0 8 * * * cd /path/to/recipes-etl && python scripts/processing/scrape_reddit_recipes.py --limit 100
```

### Example 2: Monitor Multiple Subreddits

Create a shell script to monitor multiple subreddits:

```bash
#!/bin/bash
python scripts/processing/scrape_reddit_recipes.py --subreddit recipes --limit 50 &
python scripts/processing/scrape_reddit_recipes.py --subreddit cooking --limit 50 &
python scripts/processing/scrape_reddit_recipes.py --subreddit slowcooking --limit 50 &
wait
```

### Example 3: Continuous Monitoring

Run as a background service:

```bash
# Start
nohup python scripts/processing/scrape_reddit_recipes.py --continuous --interval 600 > scraper.log 2>&1 &

# Check status
tail -f scraper.log

# Stop
pkill -f scrape_reddit_recipes.py
```

## Output Example

Sample CSV output:

```csv
"date","num_comments","title","user","comment","n_char"
"2025-10-26",45,"Korean Beef Bulgogi","recipe_lover","## Ingredients\n- 1 lb beef\n- 2 tbsp soy sauce\n...",856
"2025-10-26",23,"Easy Pasta Carbonara","chef_mario","Ingredients:\n1. 400g spaghetti\n2. 200g pancetta\n...",643
```

## Integration with Pipeline

After scraping, you can process the CSV files through the existing ETL pipeline:

```bash
# 1. Scrape recipes
python scripts/processing/scrape_reddit_recipes.py --limit 100

# 2. Process the CSV file (extract recipe data)
python -m recipes.cli process-recipe data/raw/Reddit_recipes_scraped.csv 1

# 3. Load to database
python scripts/processing/process_and_load.py
```

## Troubleshooting

### Error: "No module named 'asyncpraw'"

Install dependencies:
```bash
pip install -r requirements.txt
```

### Error: "Missing Reddit credentials"

Add your Reddit API credentials to `.env` file. See `env.example` for template.

### Warning: Rate Limiting

Reddit API has rate limits. If you're hitting limits:
- Increase the `--interval` (wait longer between checks)
- Decrease the `--limit` (check fewer posts per run)

### No Recipes Found

The scraper only saves posts where the OP has posted recipe text with specific keywords. Not all posts in r/recipes contain actual recipes in the expected format.

## Tips

1. **Start Small**: Test with `--limit 5` first to verify it's working
2. **Check Output**: Monitor the CSV file to ensure data quality
3. **Avoid Spam**: Don't set interval too low (respect Reddit's API limits)
4. **Multiple Subreddits**: Run separate instances for different subreddits
5. **Backup Data**: Periodically backup your CSV files

## Next Steps

After scraping, you can:

1. **Process recipes** using local parser or AI extraction
2. **Load to database** for storage and querying
3. **Index in Elasticsearch** for advanced search
4. **Analyze data** to find trends and popular recipes

