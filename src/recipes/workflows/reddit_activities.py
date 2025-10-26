"""Temporal activities for Reddit scraping."""

import asyncio
from temporalio import activity
from typing import Dict, Any


@activity.defn
async def scrape_reddit_recipes_activity(
    subreddit: str = "recipes",
    limit: int = 25,
    use_kafka: bool = True
) -> Dict[str, Any]:
    """
    Activity to scrape Reddit recipes.
    
    Args:
        subreddit: Subreddit to scrape
        limit: Number of posts to check
        use_kafka: Whether to publish to Kafka
        
    Returns:
        Dictionary with scraping results
    """
    activity.logger.info(f"Scraping r/{subreddit} with limit={limit}, kafka={use_kafka}")
    
    # Import here to avoid issues at module level
    import sys
    from pathlib import Path
    
    # Add scripts to path
    PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(PROJECT_ROOT / 'scripts' / 'processing'))
    
    from scrape_reddit_recipes import RedditRecipeScraper
    
    # Create scraper
    scraper = RedditRecipeScraper(
        subreddit_name=subreddit,
        use_kafka=use_kafka
    )
    
    # Run the scraper once
    await scraper.run_once(limit=limit)
    
    return {
        'success': True,
        'subreddit': subreddit,
        'limit': limit,
        'use_kafka': use_kafka,
        'recipes_found': 'unknown'  # Would need to track this in scraper
    }

