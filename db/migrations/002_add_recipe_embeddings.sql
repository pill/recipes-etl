-- Migration: Add vector embeddings column to recipes table
-- Date: 2025-01-XX
-- Description: Add vector embedding column for semantic search based on title and ingredients

-- Enable pgvector extension for vector storage
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding column to recipes table
-- Using vector(384) for sentence-transformers all-MiniLM-L6-v2 model (384 dimensions)
ALTER TABLE recipes 
ADD COLUMN IF NOT EXISTS embedding vector(384);

-- Create index for vector similarity search (using HNSW for fast approximate nearest neighbor search)
CREATE INDEX IF NOT EXISTS idx_recipes_embedding ON recipes 
USING hnsw (embedding vector_cosine_ops);

-- Add comment to document the field
COMMENT ON COLUMN recipes.embedding IS 'Vector embedding generated from recipe title and ingredients for semantic search';

