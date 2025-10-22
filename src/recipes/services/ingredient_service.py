"""Ingredient service for database operations."""

from typing import Optional
from ..database import get_pool
from ..models.recipe import Ingredient, Measurement


class IngredientService:
    """Service for ingredient and measurement database operations."""
    
    @staticmethod
    async def get_or_create_ingredient(
        name: str,
        category: Optional[str] = None,
        description: Optional[str] = None,
        conn = None
    ) -> Optional[Ingredient]:
        """Get or create an ingredient. If conn is provided, uses that connection."""
        if not name or not name.strip():
            return None
        
        # Use provided connection or get new one
        if conn:
            return await IngredientService._get_or_create_ingredient_with_conn(conn, name, category, description)
        
        pool = await get_pool()
        try:
            async with pool.acquire() as conn:
                return await IngredientService._get_or_create_ingredient_with_conn(conn, name, category, description)
        except Exception as e:
            print(f"Error creating ingredient '{name}': {str(e)}")
            return None
    
    @staticmethod
    async def _get_or_create_ingredient_with_conn(conn, name: str, category: Optional[str], description: Optional[str]) -> Optional[Ingredient]:
        """Internal method to get or create ingredient with a specific connection."""
        try:
            # First try to find existing ingredient
            query = "SELECT * FROM ingredients WHERE name = $1"
            row = await conn.fetchrow(query, name)
            
            if row:
                return Ingredient(
                    id=row['id'],
                    name=row['name'],
                    category=row['category'],
                    description=row['description'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
            
            # Create new ingredient
            query = """
                INSERT INTO ingredients (name, category, description)
                VALUES ($1, $2, $3)
                ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                RETURNING *
            """
            
            row = await conn.fetchrow(query, name, category, description)
            
            if not row:
                return None
            
            return Ingredient(
                id=row['id'],
                name=row['name'],
                category=row['category'],
                description=row['description'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
        except Exception as e:
            print(f"Error in _get_or_create_ingredient_with_conn '{name}': {str(e)}")
            return None
    
    @staticmethod
    async def get_or_create_measurement(
        name: str,
        abbreviation: Optional[str] = None,
        unit_type: Optional[str] = None,
        conn = None
    ) -> Optional[Measurement]:
        """Get or create a measurement. If conn is provided, uses that connection."""
        if not name or not name.strip():
            return None
        
        # Use provided connection or get new one
        if conn:
            return await IngredientService._get_or_create_measurement_with_conn(conn, name, abbreviation, unit_type)
        
        pool = await get_pool()
        try:
            async with pool.acquire() as conn:
                return await IngredientService._get_or_create_measurement_with_conn(conn, name, abbreviation, unit_type)
        except Exception as e:
            print(f"Error creating measurement '{name}': {str(e)}")
            return None
    
    @staticmethod
    async def _get_or_create_measurement_with_conn(conn, name: str, abbreviation: Optional[str], unit_type: Optional[str]) -> Optional[Measurement]:
        """Internal method to get or create measurement with a specific connection."""
        try:
            # First try to find existing measurement
            query = "SELECT * FROM measurements WHERE name = $1"
            row = await conn.fetchrow(query, name)
            
            if row:
                return Measurement(
                    id=row['id'],
                    name=row['name'],
                    abbreviation=row['abbreviation'],
                    unit_type=row['unit_type'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
            
            # Create new measurement
            query = """
                INSERT INTO measurements (name, abbreviation, unit_type)
                VALUES ($1, $2, $3)
                ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                RETURNING *
            """
            
            row = await conn.fetchrow(query, name, abbreviation, unit_type)
            
            if not row:
                return None
            
            return Measurement(
                id=row['id'],
                name=row['name'],
                abbreviation=row['abbreviation'],
                unit_type=row['unit_type'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
        except Exception as e:
            print(f"Error in _get_or_create_measurement_with_conn '{name}': {str(e)}")
            return None
