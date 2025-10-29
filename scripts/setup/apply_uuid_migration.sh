#!/bin/bash
# Apply UUID migration to recipes database
# This script adds a UUID column to the recipes table for tracking through pipeline stages

set -e

echo "🔄 Applying UUID migration to recipes database..."

# Check if PGPASSWORD is set, otherwise use default
export PGPASSWORD="${PGPASSWORD:-postgres}"

# Database connection details
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-recipes}"
DB_USER="${DB_USER:-postgres}"

echo "📊 Database: $DB_NAME"
echo "🖥️  Host: $DB_HOST:$DB_PORT"
echo "👤 User: $DB_USER"
echo ""

# Apply the migration
echo "⚙️  Applying migration..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "db/migrations/001_add_recipe_uuid.sql"

echo ""
echo "✅ Migration applied successfully!"
echo ""
echo "📋 Next steps:"
echo "   1. Verify UUIDs were generated for existing recipes:"
echo "      psql -U $DB_USER -d $DB_NAME -c 'SELECT id, uuid, title FROM recipes LIMIT 5;'"
echo ""
echo "   2. Recreate Elasticsearch index with UUID field:"
echo "      python -m recipes.cli sync-search --recreate-index"
echo ""

