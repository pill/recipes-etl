"""Temporal client for running recipe processing workflows."""

import asyncio
import logging
from datetime import timedelta
from temporalio.client import Client
from .config import temporal_config
from .workflows.workflows import (
    ProcessRecipeBatchWorkflow,
    ProcessRecipeBatchLocalWorkflow,
    ProcessRecipeBatchLocalParallelWorkflow,
    LoadRecipesToDbWorkflow,
    LoadRecipesToDbParallelWorkflow
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_recipe_batch_workflow(
    csv_file_path: str,
    start_entry: int,
    end_entry: int,
    delay_between_activities_ms: int = 1000,
    use_ai: bool = False
) -> dict:
    """Run a recipe batch processing workflow."""
    client = await Client.connect(f"{temporal_config.host}:{temporal_config.port}")
    
    workflow_class = ProcessRecipeBatchWorkflow if use_ai else ProcessRecipeBatchLocalWorkflow
    
    input_data = {
        'csvFilePath': csv_file_path,
        'startEntry': start_entry,
        'endEntry': end_entry,
        'delayBetweenActivitiesMs': delay_between_activities_ms
    }
    
    logger.info(f"Starting workflow: {workflow_class.__name__}")
    logger.info(f"Processing entries {start_entry} to {end_entry} from {csv_file_path}")
    
    handle = await client.start_workflow(
        workflow_class.run,
        input_data,
        id=f"recipe-batch-{start_entry}-{end_entry}",
        task_queue="recipe-processing",
        execution_timeout=timedelta(hours=1)  # 1 hour for the entire workflow
    )
    
    result = await handle.result()
    logger.info("Workflow completed successfully")
    
    return result


async def run_recipe_batch_parallel_workflow(
    csv_file_path: str,
    start_entry: int,
    end_entry: int,
    batch_size: int = 5,
    delay_between_batches_ms: int = 0
) -> dict:
    """Run a parallel recipe batch processing workflow."""
    client = await Client.connect(f"{temporal_config.host}:{temporal_config.port}")
    
    input_data = {
        'csvFilePath': csv_file_path,
        'startEntry': start_entry,
        'endEntry': end_entry,
        'batchSize': batch_size,
        'delayBetweenBatchesMs': delay_between_batches_ms
    }
    
    logger.info(f"Starting parallel workflow: ProcessRecipeBatchLocalParallelWorkflow")
    logger.info(f"Processing entries {start_entry} to {end_entry} from {csv_file_path}")
    logger.info(f"Batch size: {batch_size}, Delay between batches: {delay_between_batches_ms}ms")
    
    handle = await client.start_workflow(
        ProcessRecipeBatchLocalParallelWorkflow.run,
        input_data,
        id=f"recipe-batch-parallel-{start_entry}-{end_entry}",
        task_queue="recipe-processing",
        execution_timeout=timedelta(hours=1)  # 1 hour for the entire workflow
    )
    
    result = await handle.result()
    logger.info("Parallel workflow completed successfully")
    
    return result


async def run_load_recipes_workflow(
    json_file_paths: list[str],
    delay_between_activities_ms: int = 100,
    parallel: bool = False,
    batch_size: int = 10,
    delay_between_batches_ms: int = 0
) -> dict:
    """Run a load recipes to database workflow."""
    client = await Client.connect(f"{temporal_config.host}:{temporal_config.port}")
    
    input_data = {
        'jsonFilePaths': json_file_paths
    }
    
    if parallel:
        workflow_class = LoadRecipesToDbParallelWorkflow
        input_data.update({
            'batchSize': batch_size,
            'delayBetweenBatchesMs': delay_between_batches_ms
        })
        logger.info(f"Starting parallel load workflow: LoadRecipesToDbParallelWorkflow")
        logger.info(f"Batch size: {batch_size}, Delay between batches: {delay_between_batches_ms}ms")
    else:
        workflow_class = LoadRecipesToDbWorkflow
        input_data['delayBetweenActivitiesMs'] = delay_between_activities_ms
        logger.info(f"Starting load workflow: LoadRecipesToDbWorkflow")
        logger.info(f"Delay between activities: {delay_between_activities_ms}ms")
    
    logger.info(f"Loading {len(json_file_paths)} recipe files to database")
    
    handle = await client.start_workflow(
        workflow_class.run,
        input_data,
        id=f"load-recipes-{len(json_file_paths)}-files",
        task_queue="recipe-processing",
        execution_timeout=timedelta(hours=1)  # 1 hour for the entire workflow
    )
    
    result = await handle.result()
    logger.info("Load workflow completed successfully")
    
    return result


async def main():
    """Example usage of the Temporal client."""
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python -m recipes.client <workflow_type> <csv_file_path> <start_entry> <end_entry> [options]")
        print("Workflow types: batch, batch-local, batch-parallel, load")
        sys.exit(1)
    
    workflow_type = sys.argv[1]
    csv_file_path = sys.argv[2]
    start_entry = int(sys.argv[3])
    end_entry = int(sys.argv[4])
    
    if workflow_type == "batch-ai":
        result = await run_recipe_batch_workflow(csv_file_path, start_entry, end_entry, use_ai=True)
    elif workflow_type == "batch-local":
        result = await run_recipe_batch_workflow(csv_file_path, start_entry, end_entry, use_ai=False)
    elif workflow_type == "batch-parallel":
        batch_size = int(sys.argv[5]) if len(sys.argv) > 5 else 5
        result = await run_recipe_batch_parallel_workflow(csv_file_path, start_entry, end_entry, batch_size)
    else:
        print(f"Unknown workflow type: {workflow_type}")
        sys.exit(1)
    
    print(f"Workflow completed: {result}")


if __name__ == '__main__':
    asyncio.run(main())
