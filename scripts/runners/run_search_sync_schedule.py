import asyncio
import sys
from datetime import timedelta
from pathlib import Path

# Add src to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from temporalio.client import Client, Schedule, ScheduleActionStartWorkflow, ScheduleSpec, ScheduleIntervalSpec
from recipes.workflows.search_sync_workflow import SearchSyncWorkflow


async def create_schedule(
    schedule_id: str = 'search-sync-every-hour',
    batch_size: int = 1000,
    interval_minutes: int = 60,
    temporal_host: str = 'localhost:7233'
):
    """
    Create a Temporal Schedule for the search sync.
    
    Args:
        schedule_id: Unique identifier for the schedule
        batch_size: Number of recipes to process per batch
        interval_minutes: Minutes between runs
        temporal_host: Temporal server address
    """
    print(f'🔗 Connecting to Temporal at {temporal_host}...')
    client = await Client.connect(temporal_host)
    
    print(f'📅 Creating schedule: {schedule_id}')
    print(f'   Batch size: {batch_size}')
    print(f'   Interval: {interval_minutes} minutes')

    try:
        # Create the schedule
        handle = await client.create_schedule(
            schedule_id,
            Schedule(
                action=ScheduleActionStartWorkflow(
                    SearchSyncWorkflow.run,
                    args=[batch_size, False],  # batch_size, recreate_index
                    id=f'search-sync-{schedule_id}',
                    task_queue='recipe-processing',  # Must match worker task queue
                ),
                spec=ScheduleSpec(
                    intervals=[
                        ScheduleIntervalSpec(
                            every=timedelta(minutes=interval_minutes)
                        )
                    ]
                ),
            )
        )

        print(f'\n✅ Schedule created successfully!')
        print(f'   Schedule ID: {schedule_id}')
        print(f'   Batch size: {batch_size}')
        print(f'   Next run: In {interval_minutes} minutes')
        print(f'\n📊 View in Temporal UI: http://localhost:8081/schedules/{schedule_id}')

        return handle

    except Exception as e:
        if 'already exists' in str(e):
            print(f'\n⚠️  Schedule \'{schedule_id}\' already exists')
            print(f'   Use delete command to remove it first')
        else:
            print(f'\n❌ Error creating schedule: {e}')
        raise


async def delete_schedule(
    schedule_id: str = 'search-sync-every-hour',
    temporal_host: str = 'localhost:7233'
):
    """Delete a Temporal Schedule."""
    print(f'🔗 Connecting to Temporal at {temporal_host}...')
    client = await Client.connect(temporal_host)
    
    print(f'🗑️  Deleting schedule: {schedule_id}')
    
    try:
        handle = client.get_schedule_handle(schedule_id)
        await handle.delete()
        print(f'✅ Schedule deleted successfully!')
        
    except Exception as e:
        print(f'❌ Error deleting schedule: {e}')
        raise


async def pause_schedule(
    schedule_id: str = 'search-sync-every-hour',
    temporal_host: str = 'localhost:7233'
):
    """Pause a Temporal Schedule."""
    print(f'🔗 Connecting to Temporal at {temporal_host}...')
    client = await Client.connect(temporal_host)
    
    print(f'⏸️  Pausing schedule: {schedule_id}')
    
    try:
        handle = client.get_schedule_handle(schedule_id)
        await handle.pause(note='Paused via CLI')
        print(f'✅ Schedule paused successfully!')
        
    except Exception as e:
        print(f'❌ Error pausing schedule: {e}')
        raise


async def unpause_schedule(
    schedule_id: str = 'search-sync-every-hour',
    temporal_host: str = 'localhost:7233'
):
    """Unpause a Temporal Schedule."""
    print(f'🔗 Connecting to Temporal at {temporal_host}...')
    client = await Client.connect(temporal_host)
    
    print(f'▶️  Unpausing schedule: {schedule_id}')
    
    try:
        handle = client.get_schedule_handle(schedule_id)
        await handle.unpause(note='Unpaused via CLI')
        print(f'✅ Schedule unpaused successfully!')
        
    except Exception as e:
        print(f'❌ Error unpausing schedule: {e}')
        raise


async def trigger_schedule(
    schedule_id: str = 'search-sync-every-hour',
    temporal_host: str = 'localhost:7233'
):
    """Trigger a Temporal Schedule immediately."""
    print(f'🔗 Connecting to Temporal at {temporal_host}...')
    client = await Client.connect(temporal_host)
    
    print(f'🚀 Triggering schedule: {schedule_id}')
    
    try:
        handle = client.get_schedule_handle(schedule_id)
        await handle.trigger()
        print(f'✅ Schedule triggered successfully!')
        
    except Exception as e:
        print(f'❌ Error triggering schedule: {e}')
        raise


async def describe_schedule(
    schedule_id: str = 'search-sync-every-hour',
    temporal_host: str = 'localhost:7233'
):
    """Describe a Temporal Schedule."""
    print(f'🔗 Connecting to Temporal at {temporal_host}...')
    client = await Client.connect(temporal_host)
    
    print(f'📋 Describing schedule: {schedule_id}\n')
    
    try:
        handle = client.get_schedule_handle(schedule_id)
        description = await handle.describe()
        
        print(f'Schedule: {schedule_id}')
        print(f'State: {description.schedule.state}')
        print(f'Paused: {description.schedule.state.paused}')
        if description.schedule.state.notes:
            print(f'Notes: {description.schedule.state.notes}')
        print(f'\nActions taken: {description.info.num_actions}')
        
        if description.info.recent_actions:
            print(f'\nRecent actions:')
            for action in description.info.recent_actions[:5]:
                print(f'  - {action.actual_time}: Workflow started')
        
        print(f'\nNext {len(description.info.future_action_times)} upcoming runs:')
        for i, future_time in enumerate(description.info.future_action_times[:5], 1):
            print(f'  {i}. {future_time}')
        
    except Exception as e:
        print(f'❌ Error describing schedule: {e}')
        raise


def main():
    """Main entry point for schedule management."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Manage Temporal Schedule for Elasticsearch Search Sync'
    )
    parser.add_argument(
        'action',
        choices=['create', 'delete', 'pause', 'unpause', 'trigger', 'describe'],
        help='Action to perform'
    )
    parser.add_argument(
        '--schedule-id',
        default='search-sync-every-hour',
        help='Schedule ID (default: search-sync-every-hour)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=1000,
        help='Batch size for syncing (default: 1000)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Interval in minutes (default: 60)'
    )
    parser.add_argument(
        '--host',
        default='localhost:7233',
        help='Temporal server host (default: localhost:7233)'
    )
    
    args = parser.parse_args()
    
    if args.action == 'create':
        asyncio.run(create_schedule(
            schedule_id=args.schedule_id,
            batch_size=args.batch_size,
            interval_minutes=args.interval,
            temporal_host=args.host
        ))
    elif args.action == 'delete':
        asyncio.run(delete_schedule(
            schedule_id=args.schedule_id,
            temporal_host=args.host
        ))
    elif args.action == 'pause':
        asyncio.run(pause_schedule(
            schedule_id=args.schedule_id,
            temporal_host=args.host
        ))
    elif args.action == 'unpause':
        asyncio.run(unpause_schedule(
            schedule_id=args.schedule_id,
            temporal_host=args.host
        ))
    elif args.action == 'trigger':
        asyncio.run(trigger_schedule(
            schedule_id=args.schedule_id,
            temporal_host=args.host
        ))
    elif args.action == 'describe':
        asyncio.run(describe_schedule(
            schedule_id=args.schedule_id,
            temporal_host=args.host
        ))


if __name__ == '__main__':
    main()