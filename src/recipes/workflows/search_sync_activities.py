"""Temporal activities for Elasticsearch search sync."""

from typing import Dict, Any
from temporalio import activity


@activity.defn
async def sync_search_activity(
    batch_size: int = 1000,
    recreate_index: bool = False
) -> Dict[str, Any]:
    """
    Activity to sync recipes from PostgreSQL to Elasticsearch.
    
    Args:
        batch_size: Number of recipes to process per batch
        recreate_index: Whether to delete and recreate the index
        
    Returns:
        Dictionary with sync results
    """
    from ..services.elasticsearch_service import get_elasticsearch_service
    
    activity.logger.info(
        f'Starting search sync activity (batch_size={batch_size}, '
        f'recreate_index={recreate_index})'
    )
    
    es_service = None
    try:
        # Create Elasticsearch service
        es_service = await get_elasticsearch_service()
        
        # Health check
        activity.logger.info('Checking Elasticsearch health...')
        if not await es_service.health_check():
            error_msg = 'Elasticsearch is not healthy or not running!'
            activity.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'total': 0,
                'synced': 0,
                'failed': 0
            }
        
        activity.logger.info('Elasticsearch is healthy')
        
        # Recreate index if requested
        if recreate_index:
            activity.logger.info('Deleting existing index...')
            await es_service.delete_index()
        
        # Create index
        activity.logger.info('Creating/verifying index...')
        await es_service.create_index()
        
        # Sync all recipes
        activity.logger.info(f'Syncing recipes (batch size: {batch_size})...')
        result = await es_service.sync_all_from_database(batch_size=batch_size)
        
        activity.logger.info(
            f'Search sync complete: {result["success"]} synced, '
            f'{result["failed"]} failed'
        )
        
        return {
            'success': True,
            'total': result.get('total', 0),
            'synced': result.get('success', 0),
            'failed': result.get('failed', 0),
            'skipped': result.get('skipped', 0)
        }
        
    except Exception as e:
        error_msg = str(e)
        activity.logger.error(f'Error during search sync: {error_msg}')
        return {
            'success': False,
            'error': error_msg,
            'total': 0,
            'synced': 0,
            'failed': 0
        }
    finally:
        if es_service:
            await es_service.close()

