# Database Migrations

This directory contains database migration scripts for the recipes ETL project.

## Running Migrations

To run a migration:

```bash
psql -U postgres -d recipes -f db/migrations/001_add_recipe_uuid.sql
```

Or using the connection string:

```bash
psql postgresql://postgres:postgres@localhost:5432/recipes -f db/migrations/001_add_recipe_uuid.sql
```

## Migration Files

- `001_add_recipe_uuid.sql` - Adds UUID column to recipes table for tracking through pipeline stages

## Best Practices

1. Always use `IF NOT EXISTS` or `IF EXISTS` clauses to make migrations idempotent
2. Create backups before running migrations on production
3. Test migrations on a copy of production data first
4. Number migrations sequentially (001, 002, 003, etc.)
5. Include rollback scripts when possible

