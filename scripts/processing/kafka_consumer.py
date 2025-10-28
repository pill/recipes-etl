#!/usr/bin/env python3
"""
Kafka consumer for processing scraped recipe events.

This script consumes recipe events from Kafka and processes them:
1. Saves to CSV (optional)
2. Processes through local parser or AI
3. Loads into database
"""

import asyncio
import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from recipes.services.kafka_service import get_kafka_service
from recipes.workflows.activities import load_json_to_db
from recipes.utils.local_parser import LocalRecipeParser
from recipes.utils.json_processor import JSONProcessor


class RecipeKafkaConsumer:
    """Consumer for processing recipe events from Kafka."""
    
    def __init__(
        self,
        save_to_csv: bool = False,
        csv_file: Optional[str] = None,
        process_recipes: bool = True,
        load_to_db: bool = True,
        use_ai: bool = False
    ):
        """
        Initialize the consumer.
        
        Args:
            save_to_csv: Whether to save recipes to CSV
            csv_file: CSV file path (default: data/raw/kafka_recipes.csv)
            process_recipes: Whether to process recipes
            load_to_db: Whether to load recipes to database
            use_ai: Whether to use AI for processing (default: local parser)
        
        Note: Duplicates are handled by the database layer (get_by_title check)
        """
        self.save_to_csv = save_to_csv
        self.process_recipes = process_recipes
        self.load_to_db = load_to_db
        self.use_ai = use_ai
        
        # Setup CSV file if needed
        if save_to_csv:
            if csv_file is None:
                csv_file = str(PROJECT_ROOT / "data" / "raw" / "kafka_recipes.csv")
            self.csv_file = Path(csv_file)
            self.csv_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Create file with headers if it doesn't exist
            if not self.csv_file.exists():
                with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(
                        f,
                        fieldnames=['date', 'num_comments', 'title', 'user', 'comment', 'n_char'],
                        quoting=csv.QUOTE_ALL
                    )
                    writer.writeheader()
        
        self.kafka_service = get_kafka_service()
        self.stats = {
            'received': 0,
            'saved_csv': 0,
            'processed': 0,
            'loaded_db': 0,
            'errors': 0
        }
    
    def save_to_csv_file(self, recipe_data: Dict[str, Any]):
        """Save recipe data to CSV file."""
        try:
            with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=['date', 'num_comments', 'title', 'user', 'comment', 'n_char'],
                    quoting=csv.QUOTE_ALL
                )
                writer.writerow({
                    'date': recipe_data.get('date'),
                    'num_comments': recipe_data.get('num_comments'),
                    'title': recipe_data.get('title'),
                    'user': recipe_data.get('user'),
                    'comment': recipe_data.get('comment'),
                    'n_char': recipe_data.get('n_char')
                })
            self.stats['saved_csv'] += 1
            print(f"💾 Saved to CSV: {self.csv_file}")
        except Exception as e:
            print(f"❌ Error saving to CSV: {e}")
            self.stats['errors'] += 1
    
    async def process_recipe_async(self, recipe_data: Dict[str, Any]):
        """Process recipe using local parser or AI."""
        try:
            print(f"⚙️  Processing recipe: '{recipe_data.get('title', 'Unknown')[:60]}...'")
            
            # Extract recipe text from Kafka message
            recipe_text = recipe_data.get('comment', '')
            
            if not recipe_text:
                print(f"⚠️  No recipe text found in message")
                self.stats['errors'] += 1
                return None
            
            # Parse the recipe text using local parser
            local_parser = LocalRecipeParser()
            parsed_recipe = await local_parser.extract_recipe_data(recipe_text)
            
            # Override title with the one from Kafka if available
            kafka_title = recipe_data.get('title', '').strip()
            if kafka_title:
                parsed_recipe.title = kafka_title
            
            # Save to JSON file
            processor = JSONProcessor()
            # Use a unique identifier for the filename
            entry_id = hash(f"{kafka_title}_{recipe_data.get('user', 'unknown')}")
            output_path = await processor.save_recipe_json(
                parsed_recipe,
                abs(entry_id),  # Use hash as entry number
                subdirectory="kafka_recipes"
            )
            
            self.stats['processed'] += 1
            print(f"✅ Processed and saved to: {output_path}")
            
            return output_path
            
        except Exception as e:
            print(f"❌ Error processing recipe: {e}")
            import traceback
            traceback.print_exc()
            self.stats['errors'] += 1
            return None
    
    async def load_to_database(self, json_file_path: Optional[str]):
        """Load recipe JSON to database."""
        if not json_file_path:
            return
            
        try:
            print(f"💾 Loading to database from: {json_file_path}")
            
            # Use the existing load_json_to_db activity
            result = await load_json_to_db(json_file_path)
            
            if result.get('success'):
                if result.get('alreadyExists'):
                    print(f"ℹ️  Recipe already in DB: {result.get('title')}")
                else:
                    print(f"✅ Loaded to DB: {result.get('title')}")
                self.stats['loaded_db'] += 1
            else:
                print(f"❌ Failed to load: {result.get('error')}")
                self.stats['errors'] += 1
            
        except Exception as e:
            print(f"❌ Error loading to database: {e}")
            import traceback
            traceback.print_exc()
            self.stats['errors'] += 1
    
    def handle_message(self, recipe_data: Dict[str, Any]):
        """
        Handle a single recipe message from Kafka.
        
        Note: Duplicates are handled at database layer (get_by_title in load_json_to_db)
        """
        self.stats['received'] += 1
        
        print(f"\n{'='*60}")
        print(f"📨 Message #{self.stats['received']}")
        print(f"📝 Title: {recipe_data.get('title', 'Unknown')}")
        print(f"👤 User: {recipe_data.get('user', 'Unknown')}")
        print(f"📅 Date: {recipe_data.get('date', 'Unknown')}")
        print(f"💬 Comments: {recipe_data.get('num_comments', 0)}")
        
        # Save to CSV if enabled
        if self.save_to_csv:
            self.save_to_csv_file(recipe_data)
        
        # Process and load asynchronously if enabled
        if self.process_recipes or self.load_to_db:
            # Create a new event loop for this message
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self._process_async(recipe_data))
                finally:
                    loop.close()
            except Exception as e:
                print(f"❌ Error in async processing: {e}")
                import traceback
                traceback.print_exc()
                self.stats['errors'] += 1
        
        print(f"{'='*60}\n")
    
    async def _process_async(self, recipe_data: Dict[str, Any]):
        """Async processing helper."""
        json_file_path = None
        
        if self.process_recipes:
            # Process recipe and get JSON file path
            json_file_path = await self.process_recipe_async(recipe_data)
        
        if self.load_to_db and json_file_path:
            # Load the JSON file to database
            await self.load_to_database(json_file_path)
    
    def start(self, max_messages: Optional[int] = None):
        """Start consuming messages from Kafka."""
        print(f"🚀 Starting Kafka consumer for recipes")
        print(f"📊 Configuration:")
        print(f"   - Save to CSV: {self.save_to_csv}")
        if self.save_to_csv:
            print(f"   - CSV file: {self.csv_file}")
        print(f"   - Process recipes: {self.process_recipes}")
        print(f"   - Load to DB: {self.load_to_db}")
        print(f"   - Use AI: {self.use_ai}")
        print(f"   - Deduplication: Database layer (get_by_title)")
        print()
        
        try:
            self.kafka_service.consume_recipes(
                callback=self.handle_message,
                max_messages=max_messages
            )
        finally:
            self.print_stats()
            self.kafka_service.close()
    
    def print_stats(self):
        """Print processing statistics."""
        print("\n" + "="*60)
        print("📊 STATISTICS")
        print("="*60)
        print(f"📨 Messages received: {self.stats['received']}")
        if self.save_to_csv:
            print(f"💾 Saved to CSV: {self.stats['saved_csv']}")
        if self.process_recipes:
            print(f"⚙️  Processed: {self.stats['processed']}")
        if self.load_to_db:
            print(f"💾 Loaded to DB: {self.stats['loaded_db']}")
        print(f"❌ Errors: {self.stats['errors']}")
        print(f"\nℹ️  Note: Database handles duplicates via get_by_title check")
        print("="*60)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Consume recipe events from Kafka'
    )
    parser.add_argument(
        '--save-csv',
        action='store_true',
        help='Save recipes to CSV file'
    )
    parser.add_argument(
        '--csv-file',
        help='CSV output file path (default: data/raw/kafka_recipes.csv)'
    )
    parser.add_argument(
        '--no-process',
        action='store_true',
        help='Disable recipe processing'
    )
    parser.add_argument(
        '--no-db',
        action='store_true',
        help='Disable database loading'
    )
    parser.add_argument(
        '--use-ai',
        action='store_true',
        help='Use AI for recipe processing (default: local parser)'
    )
    parser.add_argument(
        '--max-messages',
        type=int,
        help='Maximum number of messages to consume (default: infinite)'
    )
    
    args = parser.parse_args()
    
    # Create consumer
    consumer = RecipeKafkaConsumer(
        save_to_csv=args.save_csv,
        csv_file=args.csv_file,
        process_recipes=not args.no_process,
        load_to_db=not args.no_db,
        use_ai=args.use_ai
    )
    
    # Start consuming
    consumer.start(max_messages=args.max_messages)


if __name__ == "__main__":
    main()

