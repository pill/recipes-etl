#!/usr/bin/env python3
"""
Create and manage Temporal Schedule for Reddit recipe scraping.

This script creates a Temporal Schedule that runs the Reddit scraper
every 5 minutes (or custom interval).
"""

import asyncio
import sys
from datetime import timedelta
from pathlib import Path

# Add src to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from temporalio.client import Client, Schedule, ScheduleActionStartWorkflow, ScheduleSpec, ScheduleIntervalSpec
from recipes.workflows.reddit_scraper_workflow import RedditScraperWorkflow


async def create_schedule(
    schedule_id: str = "reddit-scraper-every-5min",
    subreddit: str = "recipes",
    limit: int = 25,
    interval_minutes: int = 5,
    use_kafka: bool = True,
    temporal_host: str = "localhost:7233"
):
    """
    Create a Temporal Schedule for the Reddit scraper.
    
    Args:
        schedule_id: Unique identifier for the schedule
        subreddit: Subreddit to scrape
        limit: Number of posts to check per run
        interval_minutes: Minutes between runs
        use_kafka: Whether to publish to Kafka
        temporal_host: Temporal server address
    """
    print(f"🔗 Connecting to Temporal at {temporal_host}...")
    client = await Client.connect(temporal_host)
    
    print(f"📅 Creating schedule: {schedule_id}")
    print(f"   - Subreddit: r/{subreddit}")
    print(f"   - Posts per run: {limit}")
    print(f"   - Interval: {interval_minutes} minutes")
    print(f"   - Use Kafka: {use_kafka}")
    
    try:
        # Create the schedule
        handle = await client.create_schedule(
            schedule_id,
            Schedule(
                action=ScheduleActionStartWorkflow(
                    RedditScraperWorkflow.run,
                    args=[subreddit, limit, use_kafka],
                    id=f"reddit-scraper-{schedule_id}",
                    task_queue="recipe-processing",  # Must match worker task queue
                ),
                spec=ScheduleSpec(
                    intervals=[
                        ScheduleIntervalSpec(
                            every=timedelta(minutes=interval_minutes)
                        )
                    ]
                ),
            ),
        )
        
        print(f"\n✅ Schedule created successfully!")
        print(f"   Schedule ID: {schedule_id}")
        print(f"   Next run: In {interval_minutes} minutes")
        print(f"\n📊 View in Temporal UI: http://localhost:8081/schedules/{schedule_id}")
        
        # Describe the schedule
        description = await handle.describe()
        print(f"\n📋 Schedule Details:")
        print(f"   State: {description.info.num_actions} actions taken")
        print(f"   Recent actions: {description.info.recent_actions}")
        
        return handle
        
    except Exception as e:
        if "already exists" in str(e):
            print(f"\n⚠️  Schedule '{schedule_id}' already exists")
            print(f"   Use --update to modify or --delete to remove it first")
        else:
            print(f"\n❌ Error creating schedule: {e}")
            raise


async def delete_schedule(
    schedule_id: str = "reddit-scraper-every-5min",
    temporal_host: str = "localhost:7233"
):
    """Delete a Temporal Schedule."""
    print(f"🔗 Connecting to Temporal at {temporal_host}...")
    client = await Client.connect(temporal_host)
    
    print(f"🗑️  Deleting schedule: {schedule_id}")
    
    try:
        handle = client.get_schedule_handle(schedule_id)
        await handle.delete()
        print(f"✅ Schedule deleted successfully!")
        
    except Exception as e:
        print(f"❌ Error deleting schedule: {e}")
        raise


async def pause_schedule(
    schedule_id: str = "reddit-scraper-every-5min",
    temporal_host: str = "localhost:7233"
):
    """Pause a Temporal Schedule."""
    print(f"🔗 Connecting to Temporal at {temporal_host}...")
    client = await Client.connect(temporal_host)
    
    print(f"⏸️  Pausing schedule: {schedule_id}")
    
    try:
        handle = client.get_schedule_handle(schedule_id)
        await handle.pause(note="Paused via CLI")
        print(f"✅ Schedule paused successfully!")
        
    except Exception as e:
        print(f"❌ Error pausing schedule: {e}")
        raise


async def unpause_schedule(
    schedule_id: str = "reddit-scraper-every-5min",
    temporal_host: str = "localhost:7233"
):
    """Unpause a Temporal Schedule."""
    print(f"🔗 Connecting to Temporal at {temporal_host}...")
    client = await Client.connect(temporal_host)
    
    print(f"▶️  Unpausing schedule: {schedule_id}")
    
    try:
        handle = client.get_schedule_handle(schedule_id)
        await handle.unpause(note="Unpaused via CLI")
        print(f"✅ Schedule unpaused successfully!")
        
    except Exception as e:
        print(f"❌ Error unpausing schedule: {e}")
        raise


async def trigger_schedule(
    schedule_id: str = "reddit-scraper-every-5min",
    temporal_host: str = "localhost:7233"
):
    """Trigger a Temporal Schedule immediately."""
    print(f"🔗 Connecting to Temporal at {temporal_host}...")
    client = await Client.connect(temporal_host)
    
    print(f"▶️  Triggering schedule immediately: {schedule_id}")
    
    try:
        handle = client.get_schedule_handle(schedule_id)
        await handle.trigger()
        print(f"✅ Schedule triggered successfully!")
        
    except Exception as e:
        print(f"❌ Error triggering schedule: {e}")
        raise


async def describe_schedule(
    schedule_id: str = "reddit-scraper-every-5min",
    temporal_host: str = "localhost:7233"
):
    """Describe a Temporal Schedule."""
    print(f"🔗 Connecting to Temporal at {temporal_host}...")
    client = await Client.connect(temporal_host)
    
    try:
        handle = client.get_schedule_handle(schedule_id)
        description = await handle.describe()
        
        print(f"\n📋 Schedule: {schedule_id}")
        print(f"{'='*60}")
        print(f"State: {'Paused' if description.schedule.state.paused else 'Active'}")
        print(f"Actions taken: {description.info.num_actions}")
        print(f"Recent actions: {len(description.info.recent_actions)}")
        
        if description.info.recent_actions:
            print(f"\nRecent runs:")
            for action in description.info.recent_actions[-5:]:
                if hasattr(action, 'start_workflow_action'):
                    print(f"  - {action.start_workflow_action.workflow_id}")
                else:
                    print(f"  - Action at {action.actual_time}")
        
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"❌ Error describing schedule: {e}")
        raise


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Manage Temporal Schedule for Reddit scraping'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Create schedule
    create_parser = subparsers.add_parser('create', help='Create a new schedule')
    create_parser.add_argument('--schedule-id', default='reddit-scraper-every-5min')
    create_parser.add_argument('--subreddit', default='recipes')
    create_parser.add_argument('--limit', type=int, default=25)
    create_parser.add_argument('--interval', type=int, default=5, help='Minutes between runs')
    create_parser.add_argument('--no-kafka', action='store_true', help='Disable Kafka (save to CSV)')
    
    # Delete schedule
    delete_parser = subparsers.add_parser('delete', help='Delete a schedule')
    delete_parser.add_argument('--schedule-id', default='reddit-scraper-every-5min')
    
    # Pause schedule
    pause_parser = subparsers.add_parser('pause', help='Pause a schedule')
    pause_parser.add_argument('--schedule-id', default='reddit-scraper-every-5min')
    
    # Unpause schedule
    unpause_parser = subparsers.add_parser('unpause', help='Unpause a schedule')
    unpause_parser.add_argument('--schedule-id', default='reddit-scraper-every-5min')
    
    # Trigger schedule
    trigger_parser = subparsers.add_parser('trigger', help='Trigger schedule immediately')
    trigger_parser.add_argument('--schedule-id', default='reddit-scraper-every-5min')
    
    # Describe schedule
    describe_parser = subparsers.add_parser('describe', help='Describe a schedule')
    describe_parser.add_argument('--schedule-id', default='reddit-scraper-every-5min')
    
    args = parser.parse_args()
    
    if args.command == 'create':
        await create_schedule(
            schedule_id=args.schedule_id,
            subreddit=args.subreddit,
            limit=args.limit,
            interval_minutes=args.interval,
            use_kafka=not args.no_kafka
        )
    elif args.command == 'delete':
        await delete_schedule(args.schedule_id)
    elif args.command == 'pause':
        await pause_schedule(args.schedule_id)
    elif args.command == 'unpause':
        await unpause_schedule(args.schedule_id)
    elif args.command == 'trigger':
        await trigger_schedule(args.schedule_id)
    elif args.command == 'describe':
        await describe_schedule(args.schedule_id)
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())

