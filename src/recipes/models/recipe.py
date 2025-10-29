"""Recipe data models."""

from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class Ingredient(BaseModel):
    """Ingredient model."""
    
    id: Optional[int] = None
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Measurement(BaseModel):
    """Measurement model."""
    
    id: Optional[int] = None
    name: str
    abbreviation: Optional[str] = None
    unit_type: Optional[Literal['volume', 'weight', 'count', 'length', 'temperature', 'other']] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RecipeIngredient(BaseModel):
    """Recipe ingredient model with measurement and amount."""
    
    id: Optional[int] = None
    recipe_id: Optional[int] = None
    ingredient_id: Optional[int] = None  # Optional when creating, required for DB
    measurement_id: Optional[int] = None
    amount: Optional[float] = None
    notes: Optional[str] = None
    order_index: Optional[int] = None
    created_at: Optional[datetime] = None
    
    # Populated fields when joining with ingredients and measurements
    ingredient: Optional[Ingredient] = None
    measurement: Optional[Measurement] = None


class Recipe(BaseModel):
    """Recipe model."""
    
    id: Optional[int] = None
    uuid: Optional[str] = None  # Generated deterministically from title + source_url
    title: str
    description: Optional[str] = None
    ingredients: List[RecipeIngredient] = Field(default_factory=list)
    instructions: List[str] = Field(default_factory=list)
    prep_time_minutes: Optional[int] = None
    cook_time_minutes: Optional[int] = None
    total_time_minutes: Optional[int] = None
    servings: Optional[int] = None
    difficulty: Optional[Literal['easy', 'medium', 'hard']] = None
    cuisine_type: Optional[str] = None
    meal_type: Optional[Literal['breakfast', 'lunch', 'dinner', 'snack', 'dessert']] = None
    dietary_tags: Optional[List[str]] = None
    source_url: Optional[str] = None
    reddit_post_id: Optional[str] = None
    reddit_author: Optional[str] = None
    reddit_score: Optional[int] = None
    reddit_comments_count: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RecipeFilters(BaseModel):
    """Recipe filtering options."""
    
    cuisine_type: Optional[str] = None
    meal_type: Optional[str] = None
    difficulty: Optional[str] = None
    dietary_tags: Optional[List[str]] = None
    max_prep_time: Optional[int] = None
    max_cook_time: Optional[int] = None
    min_servings: Optional[int] = None
