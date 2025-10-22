"""Temporal workflows for recipe processing."""

import asyncio
from datetime import timedelta
from typing import List, Dict, Any
from temporalio import workflow
from temporalio.common import RetryPolicy
from .activities import (
    process_recipe_entry,
    process_recipe_entry_local,
    load_json_to_db
)


@workflow.defn
class ProcessRecipeBatchWorkflow:
    """Workflow to process a batch of recipe entries from a CSV file using AI."""
    
    @workflow.run
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process recipe batch workflow."""
        csv_file_path = input_data['csvFilePath']
        start_entry = input_data['startEntry']
        end_entry = input_data['endEntry']
        delay_between_activities_ms = input_data.get('delayBetweenActivitiesMs', 1000)
        
        print(f"[Workflow] Processing entries {start_entry} to {end_entry} from {csv_file_path}")
        print(f"[Workflow] Delay between activities: {delay_between_activities_ms}ms")
        
        results = {
            'totalProcessed': 0,
            'successful': 0,
            'skipped': 0,
            'failed': 0,
            'results': []
        }
        
        # Process each entry sequentially
        for entry_number in range(start_entry, end_entry + 1):
            print(f"[Workflow] Processing entry {entry_number}/{end_entry}")
            
            try:
                result = await workflow.execute_activity(
                    process_recipe_entry,
                    args=[csv_file_path, entry_number],
                    task_queue="recipe-processing",
                    start_to_close_timeout=timedelta(minutes=10),
                    retry_policy=RetryPolicy(
                        initial_interval=timedelta(seconds=5),
                        maximum_interval=timedelta(seconds=60),
                        maximum_attempts=3,
                        backoff_coefficient=2.0
                    )
                )
                
                results['totalProcessed'] += 1
                
                if result['success']:
                    if result.get('skipped'):
                        results['skipped'] += 1
                    else:
                        results['successful'] += 1
                else:
                    results['failed'] += 1
                
                results['results'].append({
                    'entryNumber': result['entryNumber'],
                    'success': result['success'],
                    'skipped': result.get('skipped'),
                    'outputFilePath': result.get('outputFilePath'),
                    'error': result.get('error')
                })
                
                # Add delay between activities to throttle API calls (except for last entry)
                if entry_number < end_entry and delay_between_activities_ms > 0:
                    print(f"[Workflow] Sleeping for {delay_between_activities_ms}ms...")
                    await workflow.sleep(delay_between_activities_ms / 1000)
                    
            except Exception as e:
                error_message = str(e)
                print(f"[Workflow] Error processing entry {entry_number}: {error_message}")
                
                results['totalProcessed'] += 1
                results['failed'] += 1
                results['results'].append({
                    'entryNumber': entry_number,
                    'success': False,
                    'error': error_message
                })
        
        print(f"[Workflow] Batch processing complete!")
        print(f"[Workflow] Total: {results['totalProcessed']}, Success: {results['successful']}, Skipped: {results['skipped']}, Failed: {results['failed']}")
        
        return results


@workflow.defn
class ProcessRecipeBatchLocalWorkflow:
    """Workflow to process a batch of recipe entries using LOCAL parsing (no AI)."""
    
    @workflow.run
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process recipe batch local workflow."""
        csv_file_path = input_data['csvFilePath']
        start_entry = input_data['startEntry']
        end_entry = input_data['endEntry']
        delay_between_activities_ms = input_data.get('delayBetweenActivitiesMs', 100)
        
        print(f"[Workflow Local] Processing entries {start_entry} to {end_entry} from {csv_file_path}")
        print(f"[Workflow Local] Using LOCAL parsing (no AI) - faster and free!")
        print(f"[Workflow Local] Delay between activities: {delay_between_activities_ms}ms")
        
        results = {
            'totalProcessed': 0,
            'successful': 0,
            'skipped': 0,
            'failed': 0,
            'results': []
        }
        
        # Process each entry sequentially
        for entry_number in range(start_entry, end_entry + 1):
            print(f"[Workflow Local] Processing entry {entry_number}/{end_entry}")
            
            try:
                result = await workflow.execute_activity(
                    process_recipe_entry_local,
                    args=[csv_file_path, entry_number],
                    task_queue="recipe-processing",
                    start_to_close_timeout=timedelta(minutes=2),
                    retry_policy=RetryPolicy(
                        initial_interval=timedelta(seconds=2),
                        maximum_interval=timedelta(seconds=30),
                        maximum_attempts=3,
                        backoff_coefficient=2.0
                    )
                )
                
                results['totalProcessed'] += 1
                
                if result['success']:
                    if result.get('skipped'):
                        print(f"[Workflow Local] Entry {entry_number} skipped (already exists)")
                        results['skipped'] += 1
                    else:
                        print(f"[Workflow Local] Entry {entry_number} processed successfully")
                        results['successful'] += 1
                else:
                    results['failed'] += 1
                
                results['results'].append({
                    'entryNumber': result['entryNumber'],
                    'success': result['success'],
                    'skipped': result.get('skipped'),
                    'outputFilePath': result.get('outputFilePath'),
                    'error': result.get('error')
                })
                
                # Add small delay between activities (local parsing is fast, so we can use shorter delays)
                if entry_number < end_entry and delay_between_activities_ms > 0:
                    print(f"[Workflow Local] Sleeping for {delay_between_activities_ms}ms...")
                    await workflow.sleep(delay_between_activities_ms / 1000)
                    
            except Exception as e:
                error_message = str(e)
                print(f"[Workflow Local] Error processing entry {entry_number}: {error_message}")
                
                results['totalProcessed'] += 1
                results['failed'] += 1
                results['results'].append({
                    'entryNumber': entry_number,
                    'success': False,
                    'error': error_message
                })
        
        print(f"[Workflow Local] Batch processing complete!")
        print(f"[Workflow Local] Total: {results['totalProcessed']}, Success: {results['successful']}, Skipped: {results['skipped']}, Failed: {results['failed']}")
        
        return results


@workflow.defn
class ProcessRecipeBatchLocalParallelWorkflow:
    """PARALLELIZED Workflow to process a batch of recipe entries using LOCAL parsing (no AI)."""
    
    @workflow.run
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process recipe batch local parallel workflow."""
        csv_file_path = input_data['csvFilePath']
        start_entry = input_data['startEntry']
        end_entry = input_data['endEntry']
        batch_size = input_data.get('batchSize', 5)
        delay_between_batches_ms = input_data.get('delayBetweenBatchesMs', 0)
        
        print(f"[Workflow Local Parallel] Processing entries {start_entry} to {end_entry} from {csv_file_path}")
        print(f"[Workflow Local Parallel] Using LOCAL parsing (no AI) - faster and free!")
        print(f"[Workflow Local Parallel] Batch size: {batch_size}, Delay between batches: {delay_between_batches_ms}ms")
        
        results = {
            'totalProcessed': 0,
            'successful': 0,
            'skipped': 0,
            'failed': 0,
            'results': []
        }
        
        # Create batches of entries to process in parallel
        total_entries = end_entry - start_entry + 1
        batches = []
        
        for i in range(0, total_entries, batch_size):
            batch = []
            for j in range(batch_size):
                entry_number = start_entry + i + j
                if entry_number <= end_entry:
                    batch.append(entry_number)
            if batch:
                batches.append(batch)
        
        print(f"[Workflow Local Parallel] Created {len(batches)} batches")
        
        # Process each batch in parallel
        for batch_index, batch in enumerate(batches):
            print(f"[Workflow Local Parallel] Processing batch {batch_index + 1}/{len(batches)} (entries: {', '.join(map(str, batch))})")
            
            # Process all entries in this batch in parallel
            batch_promises = []
            for entry_number in batch:
                promise = workflow.execute_activity(
                    process_recipe_entry_local,
                    args=[csv_file_path, entry_number],
                    task_queue="recipe-processing",
                    start_to_close_timeout=timedelta(minutes=2),
                    retry_policy=RetryPolicy(
                        initial_interval=timedelta(seconds=2),
                        maximum_interval=timedelta(seconds=30),
                        maximum_attempts=3,
                        backoff_coefficient=2.0
                    )
                )
                batch_promises.append(promise)
            
            # Wait for all entries in this batch to complete
            batch_results = await asyncio.gather(*batch_promises, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(batch_results):
                entry_number = batch[i]
                
                if isinstance(result, Exception):
                    error_message = str(result)
                    print(f"[Workflow Local Parallel] Error processing entry {entry_number}: {error_message}")
                    
                    results['totalProcessed'] += 1
                    results['failed'] += 1
                    results['results'].append({
                        'entryNumber': entry_number,
                        'success': False,
                        'error': error_message
                    })
                else:
                    if result['success']:
                        if result.get('skipped'):
                            print(f"[Workflow Local Parallel] Entry {entry_number} skipped (already exists)")
                            results['skipped'] += 1
                        else:
                            print(f"[Workflow Local Parallel] Entry {entry_number} processed successfully")
                            results['successful'] += 1
                    else:
                        results['failed'] += 1
                    
                    results['totalProcessed'] += 1
                    results['results'].append({
                        'entryNumber': result['entryNumber'],
                        'success': result['success'],
                        'skipped': result.get('skipped'),
                        'outputFilePath': result.get('outputFilePath'),
                        'error': result.get('error')
                    })
            
            # Add delay between batches if specified (except for last batch)
            if batch_index < len(batches) - 1 and delay_between_batches_ms > 0:
                print(f"[Workflow Local Parallel] Sleeping for {delay_between_batches_ms}ms between batches...")
                await workflow.sleep(delay_between_batches_ms / 1000)
        
        print(f"[Workflow Local Parallel] Batch processing complete!")
        print(f"[Workflow Local Parallel] Total: {results['totalProcessed']}, Success: {results['successful']}, Skipped: {results['skipped']}, Failed: {results['failed']}")
        
        return results


@workflow.defn
class LoadRecipesToDbWorkflow:
    """Workflow to load multiple recipe JSON files into the database."""
    
    @workflow.run
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Load recipes to database workflow."""
        json_file_paths = input_data['jsonFilePaths']
        delay_between_activities_ms = input_data.get('delayBetweenActivitiesMs', 100)
        
        print(f"[Workflow] Loading {len(json_file_paths)} recipe files to database")
        print(f"[Workflow] Delay between activities: {delay_between_activities_ms}ms")
        
        results = {
            'totalProcessed': 0,
            'successful': 0,
            'alreadyExists': 0,
            'failed': 0,
            'results': []
        }
        
        # Process each JSON file sequentially
        for i, json_file_path in enumerate(json_file_paths):
            print(f"[Workflow] Processing file {i + 1}/{len(json_file_paths)}: {json_file_path}")
            
            try:
                result = await workflow.execute_activity(
                    load_json_to_db,
                    args=[json_file_path],
                    task_queue="recipe-processing",
                    start_to_close_timeout=timedelta(minutes=5),
                    retry_policy=RetryPolicy(
                        initial_interval=timedelta(seconds=2),
                        maximum_interval=timedelta(seconds=30),
                        maximum_attempts=3,
                        backoff_coefficient=2.0
                    )
                )
                
                results['totalProcessed'] += 1
                
                if result['success']:
                    if result.get('alreadyExists'):
                        results['alreadyExists'] += 1
                    else:
                        results['successful'] += 1
                else:
                    results['failed'] += 1
                
                results['results'].append({
                    'jsonFilePath': result['jsonFilePath'],
                    'success': result['success'],
                    'recipeId': result.get('recipeId'),
                    'title': result.get('title'),
                    'alreadyExists': result.get('alreadyExists'),
                    'error': result.get('error')
                })
                
                # Add delay between activities (except for last file)
                if i < len(json_file_paths) - 1 and delay_between_activities_ms > 0:
                    await workflow.sleep(delay_between_activities_ms / 1000)
                    
            except Exception as e:
                error_message = str(e)
                print(f"[Workflow] Error loading file {json_file_path}: {error_message}")
                
                results['totalProcessed'] += 1
                results['failed'] += 1
                results['results'].append({
                    'jsonFilePath': json_file_path,
                    'success': False,
                    'error': error_message
                })
        
        print(f"[Workflow] Database loading complete!")
        print(f"[Workflow] Total: {results['totalProcessed']}, Success: {results['successful']}, Already Exists: {results['alreadyExists']}, Failed: {results['failed']}")
        
        return results


@workflow.defn
class LoadRecipesToDbParallelWorkflow:
    """PARALLELIZED Workflow to load multiple recipe JSON files into the database."""
    
    @workflow.run
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Load recipes to database parallel workflow."""
        json_file_paths = input_data['jsonFilePaths']
        batch_size = input_data.get('batchSize', 10)
        delay_between_batches_ms = input_data.get('delayBetweenBatchesMs', 0)
        
        print(f"[Workflow Parallel] Loading {len(json_file_paths)} recipe files to database")
        print(f"[Workflow Parallel] Batch size: {batch_size}, Delay between batches: {delay_between_batches_ms}ms")
        
        results = {
            'totalProcessed': 0,
            'successful': 0,
            'alreadyExists': 0,
            'failed': 0,
            'results': []
        }
        
        # Create batches of files to process in parallel
        batches = []
        for i in range(0, len(json_file_paths), batch_size):
            batch = json_file_paths[i:i + batch_size]
            batches.append(batch)
        
        print(f"[Workflow Parallel] Created {len(batches)} batches")
        
        # Process each batch in parallel
        for batch_index, batch in enumerate(batches):
            print(f"[Workflow Parallel] Processing batch {batch_index + 1}/{len(batches)} ({len(batch)} files)")
            
            # Process all files in this batch in parallel
            batch_promises = []
            for json_file_path in batch:
                promise = workflow.execute_activity(
                    load_json_to_db,
                    args=[json_file_path],
                    task_queue="recipe-processing",
                    start_to_close_timeout=timedelta(minutes=5),
                    retry_policy=RetryPolicy(
                        initial_interval=timedelta(seconds=2),
                        maximum_interval=timedelta(seconds=30),
                        maximum_attempts=3,
                        backoff_coefficient=2.0
                    )
                )
                batch_promises.append(promise)
            
            # Wait for all files in this batch to complete
            batch_results = await asyncio.gather(*batch_promises, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(batch_results):
                json_file_path = batch[i]
                
                if isinstance(result, Exception):
                    error_message = str(result)
                    print(f"[Workflow Parallel] Error loading file {json_file_path}: {error_message}")
                    
                    results['totalProcessed'] += 1
                    results['failed'] += 1
                    results['results'].append({
                        'jsonFilePath': json_file_path,
                        'success': False,
                        'error': error_message
                    })
                else:
                    results['totalProcessed'] += 1
                    
                    if result['success']:
                        if result.get('alreadyExists'):
                            results['alreadyExists'] += 1
                        else:
                            results['successful'] += 1
                    else:
                        results['failed'] += 1
                    
                    results['results'].append({
                        'jsonFilePath': result['jsonFilePath'],
                        'success': result['success'],
                        'recipeId': result.get('recipeId'),
                        'title': result.get('title'),
                        'alreadyExists': result.get('alreadyExists'),
                        'error': result.get('error')
                    })
            
            # Add delay between batches if specified (except for last batch)
            if batch_index < len(batches) - 1 and delay_between_batches_ms > 0:
                print(f"[Workflow Parallel] Sleeping for {delay_between_batches_ms}ms between batches...")
                await workflow.sleep(delay_between_batches_ms / 1000)
        
        print(f"[Workflow Parallel] Database loading complete!")
        print(f"[Workflow Parallel] Total: {results['totalProcessed']}, Success: {results['successful']}, Already Exists: {results['alreadyExists']}, Failed: {results['failed']}")
        
        return results


# Convenience functions for backward compatibility
async def process_recipe_batch(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process a batch of recipe entries from a CSV file using AI."""
    workflow_instance = ProcessRecipeBatchWorkflow()
    return await workflow_instance.run(input_data)


async def process_recipe_batch_local(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process a batch of recipe entries using LOCAL parsing (no AI)."""
    workflow_instance = ProcessRecipeBatchLocalWorkflow()
    return await workflow_instance.run(input_data)


async def process_recipe_batch_local_parallel(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process a batch of recipe entries using LOCAL parsing in parallel."""
    workflow_instance = ProcessRecipeBatchLocalParallelWorkflow()
    return await workflow_instance.run(input_data)


async def load_recipes_to_db(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Load multiple recipe JSON files into the database."""
    workflow_instance = LoadRecipesToDbWorkflow()
    return await workflow_instance.run(input_data)


async def load_recipes_to_db_parallel(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Load multiple recipe JSON files into the database in parallel."""
    workflow_instance = LoadRecipesToDbParallelWorkflow()
    return await workflow_instance.run(input_data)
