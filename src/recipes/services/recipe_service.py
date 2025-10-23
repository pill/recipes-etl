"""Recipe service for database operations."""

import json
from typing import List, Optional, Dict, Any
from ..database import get_pool
from ..models.recipe import Recipe, RecipeFilters, RecipeIngredient, Ingredient, Measurement
from .ingredient_service import IngredientService


class RecipeService:
    """Service for recipe database operations."""
    
    @staticmethod
    async def create(recipe: Recipe) -> Optional[Recipe]:
        """Create a new recipe."""
        pool = await get_pool()
        
        try:
            async with pool.acquire() as conn:
                async with conn.transaction():
                    # Insert the recipe
                    recipe_query = """
                        INSERT INTO recipes (
                            title, description, instructions, prep_time_minutes,
                            cook_time_minutes, total_time_minutes, servings, difficulty,
                            cuisine_type, meal_type, dietary_tags, source_url,
                            reddit_post_id, reddit_author, reddit_score, reddit_comments_count
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                        RETURNING *
                    """
                    
                    recipe_values = [
                        recipe.title,
                        recipe.description,
                        json.dumps(recipe.instructions),
                        recipe.prep_time_minutes,
                        recipe.cook_time_minutes,
                        recipe.total_time_minutes,
                        recipe.servings,
                        recipe.difficulty,
                        recipe.cuisine_type,
                        recipe.meal_type,
                        recipe.dietary_tags,
                        recipe.source_url,
                        recipe.reddit_post_id,
                        recipe.reddit_author,
                        recipe.reddit_score,
                        recipe.reddit_comments_count
                    ]
                    
                    recipe_row = await conn.fetchrow(recipe_query, *recipe_values)
                    
                    if not recipe_row:
                        print(f"Error: Failed to insert recipe '{recipe.title[:50]}'")
                        return None
                    
                    recipe_id = recipe_row['id']
                    
                    # Insert recipe ingredients
                    if recipe.ingredients:
                        try:
                            await RecipeService._insert_recipe_ingredients(conn, recipe_id, recipe.ingredients)
                        except Exception as ing_error:
                            print(f"Warning: Failed to insert some ingredients for recipe '{recipe.title[:50]}': {str(ing_error)}")
                            # Continue anyway - recipe is created, just missing some ingredients
            
            # Transaction is now committed - fetch the complete recipe with the same connection pool
            created_recipe = await RecipeService.get_by_id(recipe_id)
            if not created_recipe:
                print(f"Warning: Recipe {recipe_id} created but couldn't fetch it back")
                # Return a minimal recipe object with the ID
                recipe.id = recipe_id
                return recipe
            
            return created_recipe
        except Exception as e:
            print(f"Error creating recipe '{recipe.title[:50] if recipe.title else 'No title'}': {str(e)}")
            return None
    
    @staticmethod
    async def get_by_id(recipe_id: int) -> Optional[Recipe]:
        """Get recipe by ID."""
        pool = await get_pool()
        
        query = """
            SELECT 
                r.*,
                ri.id as recipe_ingredient_id,
                ri.ingredient_id,
                ri.measurement_id,
                ri.amount,
                ri.notes,
                ri.order_index,
                i.name as ingredient_name,
                i.category as ingredient_category,
                i.description as ingredient_description,
                m.name as measurement_name,
                m.abbreviation as measurement_abbreviation,
                m.unit_type as measurement_unit_type
            FROM recipes r
            LEFT JOIN recipe_ingredients ri ON r.id = ri.recipe_id
            LEFT JOIN ingredients i ON ri.ingredient_id = i.id
            LEFT JOIN measurements m ON ri.measurement_id = m.id
            WHERE r.id = $1
            ORDER BY ri.order_index ASC
        """
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, recipe_id)
            
            if not rows:
                return None
            
            return RecipeService._map_db_rows_to_recipe(rows)
    
    @staticmethod
    async def get_by_title(title: str) -> Optional[Recipe]:
        """Get recipe by title."""
        pool = await get_pool()
        
        query = """
            SELECT 
                r.*,
                ri.id as recipe_ingredient_id,
                ri.ingredient_id,
                ri.measurement_id,
                ri.amount,
                ri.notes,
                ri.order_index,
                i.name as ingredient_name,
                i.category as ingredient_category,
                i.description as ingredient_description,
                m.name as measurement_name,
                m.abbreviation as measurement_abbreviation,
                m.unit_type as measurement_unit_type
            FROM recipes r
            LEFT JOIN recipe_ingredients ri ON r.id = ri.recipe_id
            LEFT JOIN ingredients i ON ri.ingredient_id = i.id
            LEFT JOIN measurements m ON ri.measurement_id = m.id
            WHERE r.title = $1
            ORDER BY ri.order_index ASC
        """
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, title)
            
            if not rows:
                return None
            
            return RecipeService._map_db_rows_to_recipe(rows)
    
    @staticmethod
    async def get_all(filters: Optional[RecipeFilters] = None, limit: int = 50, offset: int = 0) -> List[Recipe]:
        """Get all recipes with optional filtering."""
        pool = await get_pool()
        
        base_query = 'SELECT DISTINCT r.id, r.created_at FROM recipes r WHERE 1=1'
        values = []
        param_count = 0
        
        if filters:
            if filters.cuisine_type:
                param_count += 1
                base_query += f' AND r.cuisine_type = ${param_count}'
                values.append(filters.cuisine_type)
            
            if filters.meal_type:
                param_count += 1
                base_query += f' AND r.meal_type = ${param_count}'
                values.append(filters.meal_type)
            
            if filters.difficulty:
                param_count += 1
                base_query += f' AND r.difficulty = ${param_count}'
                values.append(filters.difficulty)
            
            if filters.dietary_tags:
                param_count += 1
                base_query += f' AND r.dietary_tags && ${param_count}'
                values.append(filters.dietary_tags)
            
            if filters.max_prep_time:
                param_count += 1
                base_query += f' AND r.prep_time_minutes <= ${param_count}'
                values.append(filters.max_prep_time)
            
            if filters.max_cook_time:
                param_count += 1
                base_query += f' AND r.cook_time_minutes <= ${param_count}'
                values.append(filters.max_cook_time)
            
            if filters.min_servings:
                param_count += 1
                base_query += f' AND r.servings >= ${param_count}'
                values.append(filters.min_servings)
        
        base_query += f' ORDER BY r.created_at DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}'
        values.extend([limit, offset])
        
        # Get recipe IDs first
        async with pool.acquire() as conn:
            recipe_ids_result = await conn.fetch(base_query, *values)
            recipe_ids = [row['id'] for row in recipe_ids_result]
            
            if not recipe_ids:
                return []
            
            # Now fetch full recipes with ingredients
            query = """
                SELECT 
                    r.*,
                    ri.id as recipe_ingredient_id,
                    ri.ingredient_id,
                    ri.measurement_id,
                    ri.amount,
                    ri.notes,
                    ri.order_index,
                    i.name as ingredient_name,
                    i.category as ingredient_category,
                    i.description as ingredient_description,
                    m.name as measurement_name,
                    m.abbreviation as measurement_abbreviation,
                    m.unit_type as measurement_unit_type
                FROM recipes r
                LEFT JOIN recipe_ingredients ri ON r.id = ri.recipe_id
                LEFT JOIN ingredients i ON ri.ingredient_id = i.id
                LEFT JOIN measurements m ON ri.measurement_id = m.id
                WHERE r.id = ANY($1)
                ORDER BY r.created_at DESC, ri.order_index ASC
            """
            
            rows = await conn.fetch(query, recipe_ids)
            
            # Group results by recipe ID
            recipe_map = {}
            
            for row in rows:
                recipe_id = row['id']
                if recipe_id not in recipe_map:
                    recipe_map[recipe_id] = RecipeService._map_db_row_to_recipe(row)
                
                if row['recipe_ingredient_id']:
                    recipe = recipe_map[recipe_id]
                    recipe.ingredients.append(RecipeService._map_db_row_to_recipe_ingredient(row))
            
            return list(recipe_map.values())
    
    @staticmethod
    async def search(search_term: str, limit: int = 50) -> List[Recipe]:
        """Search recipes by text."""
        pool = await get_pool()
        
        # First get recipe IDs that match the search
        recipe_ids_query = """
            SELECT DISTINCT r.id FROM recipes r 
            WHERE to_tsvector('english', r.title || ' ' || COALESCE(r.description, '')) @@ plainto_tsquery('english', $1)
            ORDER BY ts_rank(to_tsvector('english', r.title || ' ' || COALESCE(r.description, '')), plainto_tsquery('english', $1)) DESC
            LIMIT $2
        """
        
        async with pool.acquire() as conn:
            recipe_ids_result = await conn.fetch(recipe_ids_query, search_term, limit)
            recipe_ids = [row['id'] for row in recipe_ids_result]
            
            if not recipe_ids:
                return []
            
            # Now fetch full recipes with ingredients
            query = """
                SELECT 
                    r.*,
                    ri.id as recipe_ingredient_id,
                    ri.ingredient_id,
                    ri.measurement_id,
                    ri.amount,
                    ri.notes,
                    ri.order_index,
                    i.name as ingredient_name,
                    i.category as ingredient_category,
                    i.description as ingredient_description,
                    m.name as measurement_name,
                    m.abbreviation as measurement_abbreviation,
                    m.unit_type as measurement_unit_type
                FROM recipes r
                LEFT JOIN recipe_ingredients ri ON r.id = ri.recipe_id
                LEFT JOIN ingredients i ON ri.ingredient_id = i.id
                LEFT JOIN measurements m ON ri.measurement_id = m.id
                WHERE r.id = ANY($1)
                ORDER BY ri.order_index ASC
            """
            
            rows = await conn.fetch(query, recipe_ids)
            
            # Group results by recipe ID
            recipe_map = {}
            
            for row in rows:
                recipe_id = row['id']
                if recipe_id not in recipe_map:
                    recipe_map[recipe_id] = RecipeService._map_db_row_to_recipe(row)
                
                if row['recipe_ingredient_id']:
                    recipe = recipe_map[recipe_id]
                    recipe.ingredients.append(RecipeService._map_db_row_to_recipe_ingredient(row))
            
            return list(recipe_map.values())
    
    @staticmethod
    async def update(recipe_id: int, updates: Dict[str, Any]) -> Optional[Recipe]:
        """Update recipe."""
        pool = await get_pool()
        
        async with pool.acquire() as conn:
            async with conn.transaction():
                fields = []
                values = []
                param_count = 0
                
                # Handle non-ingredient fields
                for key, value in updates.items():
                    if key not in ['id', 'ingredients'] and value is not None:
                        param_count += 1
                        fields.append(f'{key} = ${param_count}')
                        
                        # Handle JSON fields
                        if key == 'instructions':
                            values.append(json.dumps(value))
                        else:
                            values.append(value)
                
                if fields:
                    param_count += 1
                    values.append(recipe_id)
                    
                    query = f"""
                        UPDATE recipes 
                        SET {', '.join(fields)} 
                        WHERE id = ${param_count} 
                        RETURNING *
                    """
                    
                    await conn.fetchrow(query, *values)
                
                # Handle ingredients update
                if 'ingredients' in updates:
                    # Delete existing recipe ingredients
                    await conn.execute('DELETE FROM recipe_ingredients WHERE recipe_id = $1', recipe_id)
                    
                    # Insert new recipe ingredients
                    if updates['ingredients']:
                        await RecipeService._insert_recipe_ingredients(conn, recipe_id, updates['ingredients'])
                
                # Fetch the complete recipe with ingredients
                return await RecipeService.get_by_id(recipe_id)
    
    @staticmethod
    async def delete(recipe_id: int) -> bool:
        """Delete recipe."""
        pool = await get_pool()
        
        async with pool.acquire() as conn:
            result = await conn.execute('DELETE FROM recipes WHERE id = $1', recipe_id)
            return result != 'DELETE 0'
    
    @staticmethod
    async def get_stats() -> Dict[str, Any]:
        """Get recipe statistics."""
        pool = await get_pool()
        
        query = """
            SELECT 
                COUNT(*) as total_recipes,
                COUNT(DISTINCT cuisine_type) as unique_cuisines,
                COUNT(DISTINCT meal_type) as unique_meal_types,
                AVG(prep_time_minutes) as avg_prep_time,
                AVG(cook_time_minutes) as avg_cook_time,
                AVG(reddit_score) as avg_reddit_score
            FROM recipes
        """
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query)
            return dict(row)
    
    @staticmethod
    async def _insert_recipe_ingredients(conn, recipe_id: int, ingredients: List[RecipeIngredient]) -> None:
        """Helper method to insert recipe ingredients."""
        for i, ingredient in enumerate(ingredients):
            try:
                # Get ingredient name, skip if empty
                ingredient_name = ingredient.ingredient.name if ingredient.ingredient else None
                if not ingredient_name or not ingredient_name.strip():
                    continue  # Skip empty ingredients
                
                # Get or create ingredient (using same connection to avoid pool exhaustion)
                ingredient_record = await IngredientService.get_or_create_ingredient(
                    ingredient_name,
                    ingredient.ingredient.category if ingredient.ingredient else None,
                    ingredient.ingredient.description if ingredient.ingredient else None,
                    conn=conn  # Pass the existing connection
                )
                
                if not ingredient_record:
                    # Skip if ingredient creation failed
                    continue
                
                # Get or create measurement if provided (using same connection)
                measurement_id = None
                if ingredient.measurement and ingredient.measurement.name:
                    measurement_record = await IngredientService.get_or_create_measurement(
                        ingredient.measurement.name,
                        ingredient.measurement.abbreviation,
                        ingredient.measurement.unit_type,
                        conn=conn  # Pass the existing connection
                    )
                    if measurement_record:
                        measurement_id = measurement_record.id
                
                # Insert recipe ingredient
                query = """
                    INSERT INTO recipe_ingredients (recipe_id, ingredient_id, measurement_id, amount, notes, order_index)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """
                
                await conn.execute(
                    query,
                    recipe_id,
                    ingredient_record.id,
                    measurement_id,
                    ingredient.amount,
                    ingredient.notes,
                    ingredient.order_index or i + 1
                )
            except Exception as e:
                # Log error but continue with other ingredients
                print(f"Warning: Failed to insert ingredient {i+1}: {str(e)}")
                continue
    
    @staticmethod
    def _map_db_rows_to_recipe(rows: List[Any]) -> Recipe:
        """Helper method to map database rows to Recipe object (for joined queries)."""
        if not rows:
            raise ValueError('No rows provided to map_db_rows_to_recipe')
        
        first_row = rows[0]
        recipe = RecipeService._map_db_row_to_recipe(first_row)
        
        # Add ingredients
        for row in rows:
            if row['recipe_ingredient_id']:
                recipe.ingredients.append(RecipeService._map_db_row_to_recipe_ingredient(row))
        
        return recipe
    
    @staticmethod
    def _map_db_row_to_recipe_ingredient(row: Any) -> RecipeIngredient:
        """Helper method to map database row to RecipeIngredient object."""
        recipe_ingredient = RecipeIngredient(
            id=row['recipe_ingredient_id'],
            recipe_id=row['id'],
            ingredient_id=row['ingredient_id'],
            measurement_id=row['measurement_id'],
            amount=row['amount'],
            notes=row['notes'],
            order_index=row['order_index'],
            created_at=row.get('created_at')
        )
        
        # Add populated ingredient data if available
        if row['ingredient_name']:
            recipe_ingredient.ingredient = Ingredient(
                id=row['ingredient_id'],
                name=row['ingredient_name'],
                category=row['ingredient_category'],
                description=row['ingredient_description']
            )
        
        # Add populated measurement data if available
        if row['measurement_name']:
            recipe_ingredient.measurement = Measurement(
                id=row['measurement_id'],
                name=row['measurement_name'],
                abbreviation=row['measurement_abbreviation'],
                unit_type=row['measurement_unit_type']
            )
        
        return recipe_ingredient
    
    @staticmethod
    def _map_db_row_to_recipe(row: Any) -> Recipe:
        """Helper method to map database row to Recipe object (for single row queries)."""
        instructions = []
        if row['instructions']:
            try:
                instructions = json.loads(row['instructions'])
            except (json.JSONDecodeError, TypeError):
                instructions = []
        
        return Recipe(
            id=row['id'],
            title=row['title'],
            description=row['description'],
            ingredients=[],
            instructions=instructions,
            prep_time_minutes=row['prep_time_minutes'],
            cook_time_minutes=row['cook_time_minutes'],
            total_time_minutes=row['total_time_minutes'],
            servings=row['servings'],
            difficulty=row['difficulty'],
            cuisine_type=row['cuisine_type'],
            meal_type=row['meal_type'],
            dietary_tags=row['dietary_tags'],
            source_url=row['source_url'],
            reddit_post_id=row['reddit_post_id'],
            reddit_author=row['reddit_author'],
            reddit_score=row['reddit_score'],
            reddit_comments_count=row['reddit_comments_count'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
