"""UUID utilities for recipe tracking."""

import uuid
from typing import Optional


# Namespace for recipe UUIDs (using DNS namespace as base)
RECIPE_UUID_NAMESPACE = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')


def generate_recipe_uuid(title: str, source_url: Optional[str] = None) -> str:
    """
    Generate a deterministic UUID for a recipe based on title and source URL.
    
    This ensures that:
    - Same recipe from same source always gets the same UUID
    - Can deduplicate recipes across different pipeline stages
    - UUIDs are consistent across system restarts and reprocessing
    
    Args:
        title: Recipe title (required)
        source_url: Source URL of the recipe (optional, but recommended)
    
    Returns:
        String representation of UUID
        
    Example:
        >>> generate_recipe_uuid("Chocolate Chip Cookies", "https://example.com/recipe1")
        '550e8400-e29b-41d4-a716-446655440000'
        
        >>> generate_recipe_uuid("Chocolate Chip Cookies", "https://example.com/recipe1")
        '550e8400-e29b-41d4-a716-446655440000'  # Same UUID!
    """
    # Normalize title (lowercase, strip whitespace)
    normalized_title = title.strip().lower()
    
    # Normalize source_url
    normalized_source = source_url.strip().lower() if source_url else ''
    
    # Create content string for UUID generation
    content = f"{normalized_title}:{normalized_source}"
    
    # Generate deterministic UUID using uuid5
    return str(uuid.uuid5(RECIPE_UUID_NAMESPACE, content))


def generate_reddit_recipe_uuid(title: str, reddit_post_id: str) -> str:
    """
    Generate a deterministic UUID for a Reddit recipe.
    
    For Reddit recipes, we use the post ID as the source identifier since
    it's unique and unchanging.
    
    Args:
        title: Recipe title
        reddit_post_id: Reddit post ID (e.g., 't3_abc123')
    
    Returns:
        String representation of UUID
    """
    # For Reddit, construct a source URL format
    source_url = f"reddit:{reddit_post_id}"
    return generate_recipe_uuid(title, source_url)

