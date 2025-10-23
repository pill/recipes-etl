"""Pydantic schemas for AI data extraction."""

from typing import List, Optional
from pydantic import BaseModel, Field


class RecipeIngredientSchema(BaseModel):
    """Schema for recipe ingredients based on sample JSON."""
    
    item: str = Field(..., description="The ingredient name")
    amount: str = Field(..., description="The amount of the ingredient (e.g., '1 C', '2-3 Tbsp')")
    notes: Optional[str] = Field(None, description="Additional notes or preparation instructions for the ingredient")


class RecipeInstructionSchema(BaseModel):
    """Schema for recipe instructions based on sample JSON."""
    
    step: int = Field(..., description="The step number")
    title: str = Field(..., description="The title or brief description of the step")
    description: str = Field(..., description="Detailed description of what to do in this step")


class RecipeSchema(BaseModel):
    """Main recipe schema based on sample JSON structure."""
    
    title: str = Field(..., description="The recipe title")
    description: Optional[str] = Field(None, description="Brief description of the recipe")
    ingredients: List[RecipeIngredientSchema] = Field(..., min_length=1, description="List of ingredients with amounts and notes")
    instructions: List[RecipeInstructionSchema] = Field(..., min_length=1, description="Step-by-step cooking instructions with titles and descriptions")
    prepTime: Optional[str] = Field(None, description="Preparation time (e.g., '30 minutes')")
    cookTime: Optional[str] = Field(None, description="Cooking time (e.g., '45 minutes')")
    chillTime: Optional[str] = Field(None, description="Chilling/resting time (e.g., 'at least 6 hours')")
    panSize: Optional[str] = Field(None, description="Required pan or dish size (e.g., '8x5 in')")
    difficulty: Optional[str] = Field(None, description="Difficulty level (easy, medium, hard)")
    cuisine: Optional[str] = Field(None, description="Cuisine type (e.g., 'Italian', 'Thai', 'American')")
    mealType: Optional[str] = Field(None, description="Meal type (breakfast, lunch, dinner, snack, dessert)")
    dietaryTags: Optional[List[str]] = Field(None, description="Dietary tags (e.g., 'vegetarian', 'gluten-free', 'dairy-free')")
