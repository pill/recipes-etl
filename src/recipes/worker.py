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
from .workflows.activities import (
    process_recipe_entry,
    process_recipe_entry_local,
    load_json_to_db
)

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
        "anthropic",
        "httpx",
        "urllib",
        "urllib.request",
        "urllib.parse",
        "urllib.error",
        "asyncpg",
        "pydantic",
        "pandas",
        "json",
        "aiofiles"
    )
    
    # Create worker with sandbox configuration
    worker = Worker(
        client,
        task_queue="recipe-processing",
        workflows=[
            ProcessRecipeBatchWorkflow,
            ProcessRecipeBatchLocalWorkflow,
            ProcessRecipeBatchLocalParallelWorkflow,
            LoadRecipesToDbWorkflow,
            LoadRecipesToDbParallelWorkflow
        ],
        activities=[
            process_recipe_entry,
            process_recipe_entry_local,
            load_json_to_db
        ],
        workflow_runner=SandboxedWorkflowRunner(restrictions=sandbox_restrictions)
    )
    
    logger.info("Starting Temporal worker...")
    
    # Run worker
    await worker.run()


if __name__ == '__main__':
    asyncio.run(main())
