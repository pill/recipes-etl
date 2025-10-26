"""Temporal workflow for scheduled Reddit recipe scraping."""

from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

# Import with TYPE_CHECKING to avoid circular imports
with workflow.unsafe.imports_passed_through():
    from ..workflows.reddit_activities import scrape_reddit_recipes_activity


@workflow.defn
class RedditScraperWorkflow:
    """Workflow for scraping Reddit recipes on a schedule."""
    
    @workflow.run
    async def run(
        self,
        subreddit: str = "recipes",
        limit: int = 25,
        use_kafka: bool = True
    ) -> dict:
        """
        Run the Reddit scraper workflow.
        
        Args:
            subreddit: Subreddit to scrape
            limit: Number of posts to check
            use_kafka: Whether to publish to Kafka
            
        Returns:
            Dictionary with scraping results
        """
        workflow.logger.info(
            f"Starting Reddit scraper for r/{subreddit}, "
            f"limit={limit}, use_kafka={use_kafka}"
        )
        
        # Execute the scraping activity with retry policy
        result = await workflow.execute_activity(
            scrape_reddit_recipes_activity,
            args=[subreddit, limit, use_kafka],
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=10),
                maximum_interval=timedelta(minutes=1),
                maximum_attempts=3,
                backoff_coefficient=2.0,
            ),
        )
        
        workflow.logger.info(
            f"Scraping complete: {result.get('recipes_found', 0)} recipes found"
        )
        
        return result

