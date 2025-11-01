"""Temporal worker for recipe processing workflows."""

import asyncio
import logging
from temporalio.client import Client
from temporalio.worker import Worker
from temporalio.worker.workflow_sandbox import SandboxedWorkflowRunner, SandboxRestrictions
from .config import temporal_config
from .workflows.workflows import (
    ProcessRecipeBatchWorkflow,
    ProcessRecipeBatchLocalWorkflow,
    ProcessRecipeBatchLocalParallelWorkflow,
    LoadRecipesToDbWorkflow,
    LoadRecipesToDbParallelWorkflow
)
from .workflows.reddit_scraper_workflow import RedditScraperWorkflow
from .workflows.search_sync_workflow import SearchSyncWorkflow
from .workflows.activities import (
    process_recipe_entry,
    process_recipe_entry_local,
    load_json_to_db
)
from .workflows.reddit_activities import scrape_reddit_recipes_activity
from .workflows.search_sync_activities import sync_search_activity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Run the Temporal worker."""
    # Connect to Temporal server
    client = await Client.connect(f"{temporal_config.host}:{temporal_config.port}")
    
    logger.info(f"Connected to Temporal server at {temporal_config.host}:{temporal_config.port}")
    
    # Configure sandbox to allow HTTP libraries used by activities
    # These modules are only used in activities (not workflows), so they're safe to pass through
    sandbox_restrictions = SandboxRestrictions.default.with_passthrough_modules(
        'anthropic',
        'httpx',
        'http',
        'http.client',
        'urllib',
        'urllib.request',
        'urllib.parse',
        'urllib.error',
        'urllib3',
        'asyncpg',
        'asyncpraw',
        'asyncprawcore',
        'pydantic',
        'pandas',
        'json',
        'aiofiles',
        'kafka',
        'kafka.errors',
        'dotenv',
        'pathlib',
        'csv',
        'hashlib',
        'io',
        'sys',
        'os',
        'elasticsearch',
        'elasticsearch.helpers'
    )
    
    # Create main worker with sandbox configuration
    worker = Worker(
        client,
        task_queue='recipe-processing',
        workflows=[
            ProcessRecipeBatchWorkflow,
            ProcessRecipeBatchLocalWorkflow,
            ProcessRecipeBatchLocalParallelWorkflow,
            LoadRecipesToDbWorkflow,
            LoadRecipesToDbParallelWorkflow,
            RedditScraperWorkflow,
            SearchSyncWorkflow
        ],
        activities=[
            process_recipe_entry,
            process_recipe_entry_local,
            load_json_to_db,
            scrape_reddit_recipes_activity,
            sync_search_activity
        ],
        workflow_runner=SandboxedWorkflowRunner(restrictions=sandbox_restrictions)
    )
    
    logger.info('Starting Temporal worker on task queue: recipe-processing')
    logger.info('Registered workflows: ProcessRecipeBatch*, LoadRecipesToDb*, RedditScraperWorkflow, SearchSyncWorkflow')
    logger.info('Worker ready to process scheduled workflows')
    
    # Run worker
    await worker.run()


if __name__ == '__main__':
    asyncio.run(main())
