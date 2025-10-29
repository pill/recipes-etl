-- Migration: Add UUID column to recipes table
-- Date: 2025-10-28
-- Description: Add a UUID field for tracking recipes through pipeline stages
-- Updated: 2025-10-28 - Changed to deterministic UUIDs based on title + source_url

-- Add uuid column with UUID type (no default since we generate deterministically)
ALTER TABLE recipes 
ADD COLUMN IF NOT EXISTS uuid UUID UNIQUE;

-- Create index on uuid for faster lookups
CREATE INDEX IF NOT EXISTS idx_recipes_uuid ON recipes(uuid);

-- Create function to generate deterministic UUIDs
CREATE OR REPLACE FUNCTION generate_recipe_uuid(p_title TEXT, p_source_url TEXT) 
RETURNS UUID AS $$
DECLARE
    v_namespace UUID := '6ba7b810-9dad-11d1-80b4-00c04fd430c8'; -- DNS namespace
    v_content TEXT;
BEGIN
    -- Normalize title and source_url
    v_content := LOWER(TRIM(p_title)) || ':' || COALESCE(LOWER(TRIM(p_source_url)), '');
    
    -- Generate deterministic UUID using uuid5
    RETURN uuid_generate_v5(v_namespace, v_content);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Ensure uuid-ossp extension is enabled (needed for uuid_generate_v5)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Backfill deterministic UUIDs for existing recipes
UPDATE recipes 
SET uuid = CASE
    -- For Reddit recipes, use reddit post ID as source
    WHEN reddit_post_id IS NOT NULL THEN 
        generate_recipe_uuid(title, 'reddit:' || reddit_post_id)
    -- For other recipes with source_url
    WHEN source_url IS NOT NULL THEN 
        generate_recipe_uuid(title, source_url)
    -- For recipes without source, use just title
    ELSE 
        generate_recipe_uuid(title, '')
END
WHERE uuid IS NULL;

-- Make uuid NOT NULL after backfill
ALTER TABLE recipes 
ALTER COLUMN uuid SET NOT NULL;

-- Add comment to document the field
COMMENT ON COLUMN recipes.uuid IS 'Deterministic UUID generated from title + source_url for deduplication and tracking through pipeline stages';

-- Show sample of regenerated UUIDs
DO $$
BEGIN
    RAISE NOTICE '✅ Sample of regenerated UUIDs:';
END $$;

SELECT id, uuid, title, 
       CASE 
           WHEN reddit_post_id IS NOT NULL THEN 'reddit:' || reddit_post_id
           ELSE source_url 
       END as source
FROM recipes 
ORDER BY id 
LIMIT 5;

