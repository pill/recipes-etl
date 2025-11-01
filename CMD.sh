#!/bin/bash
# Quick command shortcuts for recipes-etl project
# 
# Usage: ./CMD.sh <command>
#
# Examples:
#   ./CMD.sh help
#   ./CMD.sh start
#   ./CMD.sh worker
#   ./CMD.sh test

# Project root
if [ -n "${BASH_SOURCE[0]}" ]; then
    PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
    PROJECT_ROOT="$(pwd)"
fi

# Main command execution
case "$1" in
    activate)
        echo "Run: source activate.sh"
        source "$PROJECT_ROOT/activate.sh"
        ;;
    install)
        python3 "$PROJECT_ROOT/scripts/setup/install.py"
        ;;
    test)
        python3 "$PROJECT_ROOT/scripts/setup/test_setup.py"
        ;;
    check-db)
        python3 "$PROJECT_ROOT/scripts/setup/check-db.py"
        ;;
    start)
        docker-compose -f "$PROJECT_ROOT/docker-compose.yml" up -d
        ;;
    stop)
        docker-compose -f "$PROJECT_ROOT/docker-compose.yml" down
        ;;
    restart)
        docker-compose -f "$PROJECT_ROOT/docker-compose.yml" restart
        ;;
    logs)
        docker-compose -f "$PROJECT_ROOT/docker-compose.yml" logs -f
        ;;
    ps)
        docker-compose -f "$PROJECT_ROOT/docker-compose.yml" ps
        ;;
    worker)
        cd "$PROJECT_ROOT" && source activate.sh && python3 scripts/runners/run_worker.py
        ;;
    client)
        shift
        cd "$PROJECT_ROOT" && source activate.sh && python -m recipes.client "$@"
        ;;
    load)
        cd "$PROJECT_ROOT" && source activate.sh && python3 scripts/processing/load_to_db.py
        ;;
    load-folder)
        shift
        cd "$PROJECT_ROOT" && source activate.sh && python3 scripts/processing/load_folder_to_db.py "$@"
        ;;
    process)
        shift
        cd "$PROJECT_ROOT" && source activate.sh && python3 scripts/processing/process_and_load.py "$@"
        ;;
    search)
        shift
        cd "$PROJECT_ROOT" && source activate.sh && python -m recipes.cli search-recipes "$@"
        ;;
    get-by-uuid)
        shift
        cd "$PROJECT_ROOT" && source activate.sh && python -m recipes.cli get-by-uuid "$@"
        ;;
    reload-recipe)
        shift
        cd "$PROJECT_ROOT" && source activate.sh && python -m recipes.cli reload-recipe "$@"
        ;;
    list)
        cd "$PROJECT_ROOT" && source activate.sh && python -m recipes.cli list-recipes
        ;;
    stats)
        cd "$PROJECT_ROOT" && source activate.sh && python -m recipes.cli stats
        ;;
    cli)
        shift
        cd "$PROJECT_ROOT" && source activate.sh && python -m recipes.cli "$@"
        ;;
    scrape)
        shift
        cd "$PROJECT_ROOT" && source activate.sh && python3 scripts/processing/scrape_reddit_recipes.py "$@"
        ;;
    scrape-continuous)
        shift
        cd "$PROJECT_ROOT" && source activate.sh && python3 scripts/processing/scrape_reddit_recipes.py --continuous "$@"
        ;;
    scrape-kafka)
        shift
        cd "$PROJECT_ROOT" && source activate.sh && python3 scripts/processing/scrape_reddit_recipes.py --use-kafka "$@"
        ;;
    kafka-consumer)
        shift
        cd "$PROJECT_ROOT" && source activate.sh && python3 scripts/processing/kafka_consumer.py "$@"
        ;;
    reddit-schedule)
        shift
        cd "$PROJECT_ROOT" && source activate.sh && python3 scripts/runners/run_reddit_schedule.py "$@"
        ;;
    search-sync-schedule)
        shift
        ACTION="$1"
        shift
        cd "$PROJECT_ROOT" && source activate.sh && python3 scripts/runners/run_search_sync_schedule.py "$ACTION" "$@"
        ;;
    help|"")
        echo "╔══════════════════════════════════════════════════╗"
        echo "║         Recipe ETL Command Shortcuts             ║"
        echo "╚══════════════════════════════════════════════════╝"
        echo ""
        echo "📦 Setup:"
        echo "  ./CMD.sh install       - Install dependencies"
        echo "  ./CMD.sh test          - Test Python setup"
        echo "  ./CMD.sh check-db      - Check database connection"
        echo ""
        echo "🐳 Docker Services:"
        echo "  ./CMD.sh start         - Start all services"
        echo "  ./CMD.sh stop          - Stop all services"
        echo "  ./CMD.sh restart       - Restart services"
        echo "  ./CMD.sh logs          - Show service logs"
        echo "  ./CMD.sh ps            - Show running services"
        echo ""
        echo "⚙️  Processing:"
        echo "  ./CMD.sh worker        - Start Temporal worker"
        echo "  ./CMD.sh client <args> - Run Temporal client"
        echo "  ./CMD.sh load          - Load recipes to database"
        echo "  ./CMD.sh load-folder <folder> - Load JSON files from folder to database"
        echo "  ./CMD.sh process <args> - Process and load recipes"
        echo ""
        echo "📡 Reddit Scraping:"
        echo "  ./CMD.sh scrape [--subreddit recipes] [--limit 25]"
        echo "                              - Scrape Reddit once and save to CSV"
        echo "  ./CMD.sh scrape-continuous [--interval 300]"
        echo "                              - Monitor Reddit continuously (CSV)"
        echo "  ./CMD.sh scrape-kafka [--continuous] [--limit 25]"
        echo "                              - Scrape and publish to Kafka"
        echo "  ./CMD.sh kafka-consumer [--save-csv] [--no-db]"
        echo "                              - Consume recipe events from Kafka"
        echo ""
        echo "⏰ Temporal Schedules:"
        echo "  ./CMD.sh reddit-schedule create [--interval 5]"
        echo "                              - Create Reddit scraper schedule (every 5 min default)"
        echo "  ./CMD.sh reddit-schedule pause|unpause|trigger|describe|delete"
        echo "                              - Manage the Reddit scraper schedule"
        echo "  ./CMD.sh search-sync-schedule create [--interval 60] [--batch-size 1000]"
        echo "                              - Create search sync schedule (every 60 min default)"
        echo "  ./CMD.sh search-sync-schedule pause|unpause|trigger|describe|delete"
        echo "                              - Manage the search sync schedule"
        echo ""
        echo "🔍 Search & Query:"
        echo "  ./CMD.sh search <term>       - Search recipes by text"
        echo "  ./CMD.sh get-by-uuid <uuid>  - Get recipe by UUID"
        echo "  ./CMD.sh list                - List recent recipes"
        echo "  ./CMD.sh stats               - Show statistics"
        echo "  ./CMD.sh cli <command>       - Run any CLI command"
        echo ""
        echo "🔄 Recipe Management:"
        echo "  ./CMD.sh reload-recipe <uuid> [--json-dir data/stage]"
        echo "                                    - Reload recipe from JSON → DB → Elasticsearch"
        echo ""
        echo "💡 Examples:"
        echo "  ./CMD.sh start                      # Start all services"
        echo "  ./CMD.sh worker                     # Start Temporal worker"
        echo "  ./CMD.sh load-folder data/stage/Reddit_Recipes  # Load folder to DB"
        echo "  ./CMD.sh reddit-schedule create --interval 5  # Schedule Reddit scraper"
        echo "  ./CMD.sh reddit-schedule describe   # Check schedule status"
        echo "  ./CMD.sh search-sync-schedule create --interval 60  # Schedule search sync"
        echo "  ./CMD.sh search-sync-schedule describe  # Check search sync status"
        echo "  ./CMD.sh kafka-consumer --save-csv  # Consume from Kafka"
        echo "  ./CMD.sh search 'chicken pasta'     # Search recipes"
        echo "  ./CMD.sh get-by-uuid 8faa4a5f-4f52-56db-92aa-fa574ed6b62c  # Get recipe by UUID"
        echo "  ./CMD.sh reload-recipe 8faa4a5f-4f52-56db-92aa-fa574ed6b62c  # Reload recipe to DB & Elastic"
        echo ""
        echo "📚 For detailed documentation, see: docs/COMMANDS.md"
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo ""
        echo "Run './CMD.sh help' to see available commands"
        exit 1
        ;;
esac

