"""Temporal workflow for scheduled Elasticsearch search sync."""

from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

# Import with TYPE_CHECKING to avoid circular imports
with workflow.unsafe.imports_passed_through():
    from ..workflows.search_sync_activities import sync_search_activity


@workflow.defn
class SearchSyncWorkflow:
    """Workflow for syncing recipes to Elasticsearch on a schedule."""
    
    @workflow.run
    async def run(
        self,
        batch_size: int = 1000,
        recreate_index: bool = False
    ) -> dict:
        """
        Run the search sync workflow.
        
        Args:
            batch_size: Number of recipes to process per batch
            recreate_index: Whether to delete and recreate the index
            
        Returns:
            Dictionary with sync results
        """
        workflow.logger.info(
            f'Starting search sync workflow, '
            f'batch_size={batch_size}, recreate_index={recreate_index}'
        )
        
        # Execute the search sync activity with retry policy
        result = await workflow.execute_activity(
            sync_search_activity,
            args=[batch_size, recreate_index],
            start_to_close_timeout=timedelta(minutes=30),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=10),
                maximum_interval=timedelta(minutes=5),
                maximum_attempts=3,
                backoff_coefficient=2.0,
            ),
        )
        
        workflow.logger.info(
            f'Search sync complete: {result.get("synced", 0)} recipes synced'
        )
        
        return result

