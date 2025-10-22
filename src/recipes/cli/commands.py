"""Command-line interface commands."""

import asyncio
import click
from typing import Optional
from ..database import test_connection
from ..services.ai_service import get_ai_service
from ..services.recipe_service import RecipeService
from ..services.elasticsearch_service import get_elasticsearch_service
from ..workflows.activities import process_recipe_entry, process_recipe_entry_local, load_json_to_db


@click.group()
def main():
    """Recipes Python CLI - AI-powered recipe data parser and analyzer."""
    pass


@main.command()
def test_db():
    """Test database connection."""
    asyncio.run(_test_db())


async def _test_db():
    """Test database connection."""
    success = await test_connection()
    if success:
        click.echo("✅ Database connection successful!")
    else:
        click.echo("❌ Database connection failed!")
        exit(1)


@main.command()
def test_ai():
    """Test AI service connection."""
    asyncio.run(_test_ai())


async def _test_ai():
    """Test AI service connection."""
    try:
        ai_service = get_ai_service()
        if ai_service.is_configured():
            click.echo("✅ AI service configured successfully!")
            
            # Test with a simple message
            response = await ai_service.send_message("Hello, how are you?")
            click.echo(f"🤖 AI Response: {response.content[:100]}...")
        else:
            click.echo("❌ AI service not configured!")
            exit(1)
    except Exception as e:
        click.echo(f"❌ AI service test failed: {str(e)}")
        exit(1)


@main.command()
@click.argument('csv_file_path')
@click.argument('entry_number', type=int)
@click.option('--use-ai', is_flag=True, help='Use AI extraction (default: local parsing)')
def process_recipe(csv_file_path: str, entry_number: int, use_ai: bool):
    """Process a single recipe entry from CSV."""
    asyncio.run(_process_recipe(csv_file_path, entry_number, use_ai))


async def _process_recipe(csv_file_path: str, entry_number: int, use_ai: bool):
    """Process a single recipe entry."""
    try:
        if use_ai:
            click.echo(f"🤖 Processing entry {entry_number} from {csv_file_path} using AI...")
            result = await process_recipe_entry(csv_file_path, entry_number)
        else:
            click.echo(f"⚡ Processing entry {entry_number} from {csv_file_path} using local parsing...")
            result = await process_recipe_entry_local(csv_file_path, entry_number)
        
        if result['success']:
            click.echo(f"✅ Successfully processed entry {entry_number}")
            click.echo(f"📁 Output file: {result.get('outputFilePath', 'N/A')}")
        else:
            click.echo(f"❌ Failed to process entry {entry_number}: {result.get('error', 'Unknown error')}")
            exit(1)
    except Exception as e:
        click.echo(f"❌ Error processing recipe: {str(e)}")
        exit(1)


@main.command()
@click.argument('json_file_path')
def load_recipe(json_file_path: str):
    """Load a recipe JSON file into the database."""
    asyncio.run(_load_recipe(json_file_path))


async def _load_recipe(json_file_path: str):
    """Load a recipe JSON file into the database."""
    try:
        click.echo(f"💾 Loading recipe from {json_file_path}...")
        result = await load_json_to_db(json_file_path)
        
        if result['success']:
            if result.get('alreadyExists'):
                click.echo(f"ℹ️  Recipe already exists: {result.get('title', 'N/A')}")
            else:
                click.echo(f"✅ Successfully loaded recipe: {result.get('title', 'N/A')}")
                click.echo(f"🆔 Recipe ID: {result.get('recipeId', 'N/A')}")
        else:
            click.echo(f"❌ Failed to load recipe: {result.get('error', 'Unknown error')}")
            exit(1)
    except Exception as e:
        click.echo(f"❌ Error loading recipe: {str(e)}")
        exit(1)


@main.command()
@click.option('--limit', default=10, help='Number of recipes to show')
def list_recipes(limit: int):
    """List recent recipes from the database."""
    asyncio.run(_list_recipes(limit))


async def _list_recipes(limit: int):
    """List recent recipes."""
    try:
        click.echo(f"📋 Fetching {limit} recent recipes...")
        recipes = await RecipeService.get_all(limit=limit)
        
        if not recipes:
            click.echo("📭 No recipes found in database")
            return
        
        for i, recipe in enumerate(recipes, 1):
            click.echo(f"{i}. {recipe.title}")
            if recipe.description:
                click.echo(f"   📝 {recipe.description[:100]}...")
            click.echo(f"   🕒 Prep: {recipe.prep_time_minutes or 'N/A'}min, Cook: {recipe.cook_time_minutes or 'N/A'}min")
            click.echo(f"   👥 Servings: {recipe.servings or 'N/A'}")
            click.echo()
    except Exception as e:
        click.echo(f"❌ Error listing recipes: {str(e)}")
        exit(1)


@main.command()
@click.argument('search_term')
@click.option('--limit', default=10, help='Number of results to show')
def search_recipes(search_term: str, limit: int):
    """Search recipes by text."""
    asyncio.run(_search_recipes(search_term, limit))


async def _search_recipes(search_term: str, limit: int):
    """Search recipes."""
    try:
        click.echo(f"🔍 Searching for: '{search_term}'...")
        recipes = await RecipeService.search(search_term, limit=limit)
        
        if not recipes:
            click.echo("📭 No recipes found matching your search")
            return
        
        click.echo(f"📋 Found {len(recipes)} recipes:")
        for i, recipe in enumerate(recipes, 1):
            click.echo(f"{i}. {recipe.title}")
            if recipe.description:
                click.echo(f"   📝 {recipe.description[:100]}...")
            click.echo()
    except Exception as e:
        click.echo(f"❌ Error searching recipes: {str(e)}")
        exit(1)


@main.command()
def stats():
    """Show database statistics."""
    asyncio.run(_stats())


async def _stats():
    """Show database statistics."""
    try:
        click.echo("📊 Database Statistics:")
        stats_data = await RecipeService.get_stats()
        
        click.echo(f"📝 Total recipes: {stats_data.get('total_recipes', 0)}")
        click.echo(f"🌍 Unique cuisines: {stats_data.get('unique_cuisines', 0)}")
        click.echo(f"🍽️  Unique meal types: {stats_data.get('unique_meal_types', 0)}")
        click.echo(f"⏱️  Average prep time: {stats_data.get('avg_prep_time', 0):.1f} minutes")
        click.echo(f"🔥 Average cook time: {stats_data.get('avg_cook_time', 0):.1f} minutes")
        click.echo(f"⭐ Average Reddit score: {stats_data.get('avg_reddit_score', 0):.1f}")
    except Exception as e:
        click.echo(f"❌ Error getting statistics: {str(e)}")
        exit(1)


@main.command('sync-search')
@click.option('--batch-size', default=1000, help='Batch size for syncing (default: 1000)')
@click.option('--recreate-index', is_flag=True, help='Delete and recreate the index before syncing')
def sync_search(batch_size: int, recreate_index: bool):
    """Sync all recipes from database to Elasticsearch."""
    asyncio.run(_sync_search(batch_size, recreate_index))


async def _sync_search(batch_size: int, recreate_index: bool):
    """Sync recipes to Elasticsearch."""
    es_service = None
    try:
        click.echo("🔍 Starting Elasticsearch sync...")
        
        # Create Elasticsearch service
        es_service = await get_elasticsearch_service()
        
        # Health check
        click.echo("🏥 Checking Elasticsearch health...")
        if not await es_service.health_check():
            click.echo("❌ Elasticsearch is not healthy or not running!")
            click.echo("💡 Start Elasticsearch with: docker-compose -f docker-compose.python.yml up -d elasticsearch")
            exit(1)
        
        click.echo("✅ Elasticsearch is healthy")
        
        # Recreate index if requested
        if recreate_index:
            click.echo("🗑️  Deleting existing index...")
            await es_service.delete_index()
        
        # Create index
        click.echo("📝 Creating/verifying index...")
        await es_service.create_index()
        
        # Sync all recipes
        click.echo(f"🔄 Syncing recipes (batch size: {batch_size})...")
        result = await es_service.sync_all_from_database(batch_size=batch_size)
        
        if result['failed'] > 0:
            click.echo(f"⚠️  Some recipes failed to sync. Check logs for details.")
        else:
            click.echo(f"🎉 All recipes synced successfully!")
        
        click.echo(f"\n🔍 Elasticsearch is now ready for searches!")
        click.echo(f"   - Kibana: http://localhost:5601")
        click.echo(f"   - Elasticsearch: http://localhost:9200")
        
    except Exception as e:
        click.echo(f"❌ Error syncing to Elasticsearch: {str(e)}")
        exit(1)
    finally:
        if es_service:
            await es_service.close()


if __name__ == '__main__':
    main()
