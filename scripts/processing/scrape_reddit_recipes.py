#!/usr/bin/env python3
"""
Scrape recipes from Reddit periodically and save to CSV.
Matches the format of Reddit_Recipes.csv: date, num_comments, title, user, comment, n_char
"""

import asyncio
import csv
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Set
import asyncpraw
from asyncpraw.models import MoreComments
from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

# Load environment variables
load_dotenv()


class RedditRecipeScraper:
    """Scrape recipes from Reddit subreddits."""
    
    def __init__(
        self,
        subreddit_name: str = "recipes",
        output_file: Optional[str] = None,
        check_interval: int = 300  # 5 minutes default
    ):
        """
        Initialize the scraper.
        
        Args:
            subreddit_name: Name of the subreddit to scrape (default: "recipes")
            output_file: Path to CSV output file (default: data/raw/Reddit_Recipes_New.csv)
            check_interval: Seconds between checks (default: 300)
        """
        self.subreddit_name = subreddit_name
        self.check_interval = check_interval
        
        # Setup output file
        if output_file is None:
            output_file = PROJECT_ROOT / "data" / "raw" / f"Reddit_{subreddit_name}_scraped.csv"
        self.output_file = Path(output_file)
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Track processed post IDs to avoid duplicates
        self.processed_ids: Set[str] = set()
        self._load_processed_ids()
        
        # Initialize Reddit client
        self.reddit = asyncpraw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            password=os.getenv('REDDIT_PASSWORD'),
            user_agent=f"python:{os.getenv('REDDIT_APP_NAME')}:1.2.0 (by u/{os.getenv('REDDIT_USERNAME')})",
            username=os.getenv('REDDIT_USERNAME'),
        )
    
    def _load_processed_ids(self):
        """Load already-processed post IDs from the CSV file."""
        if self.output_file.exists():
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Use title + user as a unique identifier
                        unique_id = f"{row.get('title', '')}_{row.get('user', '')}"
                        self.processed_ids.add(unique_id)
                print(f"📋 Loaded {len(self.processed_ids)} already-processed posts")
            except Exception as e:
                print(f"⚠️  Warning: Could not load processed IDs: {e}")
    
    async def extract_recipe_from_submission(self, submission) -> Optional[dict]:
        """
        Extract recipe data from a Reddit submission.
        
        Returns dict with: date, num_comments, title, user, comment, n_char
        """
        try:
            await submission.load()
            
            # Get basic submission info
            op_name = submission.author.name if submission.author else None
            if not op_name:
                return None
            
            # Create unique ID for this post
            unique_id = f"{submission.title}_{op_name}"
            
            # Skip if already processed
            if unique_id in self.processed_ids:
                return None
            
            # Look for recipe in OP's comments
            recipe_text = None
            
            # First check if the recipe is in the selftext
            if submission.is_self and submission.selftext:
                text_lower = submission.selftext.lower()
                if any(keyword in text_lower for keyword in [
                    "ingredients", "instructions", "preparation", 
                    "prep time", "cook time", "servings"
                ]):
                    recipe_text = submission.selftext
            
            # If not in selftext, check OP's comments
            if not recipe_text:
                all_comments = await submission.comments.list()
                
                for comment in all_comments:
                    if isinstance(comment, MoreComments):
                        continue
                    
                    # Check if comment is from OP
                    if comment.author and comment.author.name == op_name:
                        body_lower = comment.body.lower()
                        
                        # Look for recipe indicators
                        if any(keyword in body_lower for keyword in [
                            "ingredients", "instructions", "preparation",
                            "prep time", "cook time", "total time", "servings"
                        ]):
                            recipe_text = comment.body
                            break
            
            # If we found recipe text, return the data
            if recipe_text:
                # Convert UTC timestamp to date
                created_date = datetime.fromtimestamp(submission.created_utc).strftime('%Y-%m-%d')
                
                return {
                    'date': created_date,
                    'num_comments': submission.num_comments,
                    'title': submission.title,
                    'user': op_name,
                    'comment': recipe_text,
                    'n_char': len(recipe_text)
                }
            
            return None
            
        except Exception as e:
            print(f"⚠️  Error processing submission {submission.id}: {e}")
            return None
    
    async def scrape_new_posts(self, limit: int = 25) -> int:
        """
        Scrape new posts from the subreddit.
        
        Args:
            limit: Number of recent posts to check
            
        Returns:
            Number of new recipes found
        """
        print(f"\n🔍 Checking r/{self.subreddit_name} for new recipes...")
        
        new_recipes = 0
        
        try:
            subreddit = await self.reddit.subreddit(self.subreddit_name)
            
            # Check if CSV exists, if not create with headers
            file_exists = self.output_file.exists()
            
            with open(self.output_file, 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['date', 'num_comments', 'title', 'user', 'comment', 'n_char']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
                
                # Write header if new file
                if not file_exists:
                    writer.writeheader()
                    print(f"📝 Created new CSV file: {self.output_file}")
                
                # Iterate through new posts
                async for submission in subreddit.new(limit=limit):
                    recipe_data = await self.extract_recipe_from_submission(submission)
                    
                    if recipe_data:
                        # Write to CSV
                        writer.writerow(recipe_data)
                        csvfile.flush()  # Ensure data is written immediately
                        
                        # Add to processed set
                        unique_id = f"{recipe_data['title']}_{recipe_data['user']}"
                        self.processed_ids.add(unique_id)
                        
                        new_recipes += 1
                        print(f"✅ Saved: '{recipe_data['title'][:60]}...' by u/{recipe_data['user']}")
            
            if new_recipes > 0:
                print(f"\n🎉 Found and saved {new_recipes} new recipe(s)")
            else:
                print(f"ℹ️  No new recipes found")
            
            return new_recipes
            
        except Exception as e:
            print(f"❌ Error scraping posts: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    async def run_once(self, limit: int = 25):
        """Run the scraper once and exit."""
        try:
            me = await self.reddit.user.me()
            print(f"✅ Logged in as: u/{me}")
            
            await self.scrape_new_posts(limit=limit)
            
        finally:
            await self.reddit.close()
    
    async def run_continuous(self, limit: int = 25):
        """Run the scraper continuously on a schedule."""
        try:
            me = await self.reddit.user.me()
            print(f"✅ Logged in as: u/{me}")
            print(f"🔄 Monitoring r/{self.subreddit_name} every {self.check_interval} seconds")
            print(f"💾 Saving to: {self.output_file}")
            print(f"\n Press Ctrl+C to stop\n")
            
            while True:
                await self.scrape_new_posts(limit=limit)
                
                # Wait before next check
                print(f"\n⏳ Next check in {self.check_interval} seconds...\n")
                await asyncio.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            print("\n\n⛔ Stopping scraper...")
        finally:
            await self.reddit.close()
            print("✅ Closed Reddit connection")


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Scrape recipes from Reddit and save to CSV'
    )
    parser.add_argument(
        '--subreddit',
        default='recipes',
        help='Subreddit to scrape (default: recipes)'
    )
    parser.add_argument(
        '--output',
        help='Output CSV file path (default: data/raw/Reddit_{subreddit}_scraped.csv)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=300,
        help='Check interval in seconds for continuous mode (default: 300)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=25,
        help='Number of recent posts to check per run (default: 25)'
    )
    parser.add_argument(
        '--continuous',
        action='store_true',
        help='Run continuously (default: run once and exit)'
    )
    
    args = parser.parse_args()
    
    # Create scraper
    scraper = RedditRecipeScraper(
        subreddit_name=args.subreddit,
        output_file=args.output,
        check_interval=args.interval
    )
    
    # Run
    if args.continuous:
        await scraper.run_continuous(limit=args.limit)
    else:
        await scraper.run_once(limit=args.limit)


if __name__ == "__main__":
    asyncio.run(main())

