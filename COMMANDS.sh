#!/bin/bash
# Quick command shortcuts for recipes-etl project
# 
# Usage: ./COMMANDS.sh <command>
#
# Examples:
#   ./COMMANDS.sh help
#   ./COMMANDS.sh start
#   ./COMMANDS.sh worker
#   ./COMMANDS.sh test

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
        docker-compose -f "$PROJECT_ROOT/docker-compose.python.yml" up -d
        ;;
    stop)
        docker-compose -f "$PROJECT_ROOT/docker-compose.python.yml" down
        ;;
    restart)
        docker-compose -f "$PROJECT_ROOT/docker-compose.python.yml" restart
        ;;
    logs)
        docker-compose -f "$PROJECT_ROOT/docker-compose.python.yml" logs -f
        ;;
    ps)
        docker-compose -f "$PROJECT_ROOT/docker-compose.python.yml" ps
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
    process)
        shift
        cd "$PROJECT_ROOT" && source activate.sh && python3 scripts/processing/process_and_load.py "$@"
        ;;
    search)
        shift
        cd "$PROJECT_ROOT" && source activate.sh && python -m recipes.cli search-recipes "$@"
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
    help|"")
        echo "╔══════════════════════════════════════════════════╗"
        echo "║         Recipe ETL Command Shortcuts            ║"
        echo "╚══════════════════════════════════════════════════╝"
        echo ""
        echo "📦 Setup:"
        echo "  ./COMMANDS.sh install       - Install dependencies"
        echo "  ./COMMANDS.sh test          - Test Python setup"
        echo "  ./COMMANDS.sh check-db      - Check database connection"
        echo ""
        echo "🐳 Docker Services:"
        echo "  ./COMMANDS.sh start         - Start all services"
        echo "  ./COMMANDS.sh stop          - Stop all services"
        echo "  ./COMMANDS.sh restart       - Restart services"
        echo "  ./COMMANDS.sh logs          - Show service logs"
        echo "  ./COMMANDS.sh ps            - Show running services"
        echo ""
        echo "⚙️  Processing:"
        echo "  ./COMMANDS.sh worker        - Start Temporal worker"
        echo "  ./COMMANDS.sh client <args> - Run Temporal client"
        echo "  ./COMMANDS.sh load          - Load recipes to database"
        echo "  ./COMMANDS.sh process <args> - Process and load recipes"
        echo ""
        echo "🔍 Search & Query:"
        echo "  ./COMMANDS.sh search <term> - Search recipes"
        echo "  ./COMMANDS.sh list          - List recent recipes"
        echo "  ./COMMANDS.sh stats         - Show statistics"
        echo "  ./COMMANDS.sh cli <command> - Run any CLI command"
        echo ""
        echo "💡 Examples:"
        echo "  ./COMMANDS.sh start"
        echo "  ./COMMANDS.sh worker"
        echo "  ./COMMANDS.sh client batch-parallel data/raw/recipes.csv 1 100 20"
        echo "  ./COMMANDS.sh search 'chicken pasta'"
        echo ""
        echo "📚 For detailed documentation, see: docs/COMMANDS.md"
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo ""
        echo "Run './COMMANDS.sh help' to see available commands"
        exit 1
        ;;
esac

