#!/usr/bin/env python3
"""Quick test to verify schedule works."""

import asyncio
from temporalio.client import Client

async def main():
    print("🔗 Connecting to Temporal...")
    client = await Client.connect("localhost:7233")
    
    print("✅ Connected")
    
    # List schedules
    print("\n📋 Listing all schedules...")
    schedules = await client.list_schedules()
    async for schedule_info in schedules:
        print(f"  - {schedule_info.id}")
    
    # Check if our schedule exists
    print("\n🔍 Checking reddit-scraper schedule...")
    try:
        handle = client.get_schedule_handle("reddit-scraper-every-5min")
        desc = await handle.describe()
        
        print(f"  Schedule ID: {desc.id}")
        print(f"  State: {'Paused' if desc.schedule.state.paused else 'Active'}")
        print(f"  Actions taken: {desc.info.num_actions}")
        print(f"  Task Queue: {desc.schedule.action.start_workflow.task_queue}")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    print("\n✅ Test complete")
    print("\n💡 If schedule exists but no workflows run:")
    print("   1. Check worker is running: ps aux | grep run_worker")
    print("   2. Check task queue matches: recipe-processing")
    print("   3. View Temporal UI: http://localhost:8081")

if __name__ == "__main__":
    asyncio.run(main())

