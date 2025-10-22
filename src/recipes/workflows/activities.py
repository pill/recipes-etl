"""Temporal activities for recipe processing."""

import json
import os
from typing import Dict, Any, Optional
from temporalio import activity
from ..services.ai_service import get_ai_service
from ..services.recipe_service import RecipeService
from ..utils.csv_parser import CSVParser
from ..utils.json_processor import JSONProcessor
from ..utils.local_parser import LocalRecipeParser


@activity.defn
async def process_recipe_entry(csv_file_path: str, entry_number: int) -> Dict[str, Any]:
    """Process a single recipe entry using AI extraction."""
    try:
        # Parse CSV entry
        parser = CSVParser()
        entry_data = await parser.get_entry(csv_file_path, entry_number)
        
        if not entry_data:
            return {
                'success': False,
                'entryNumber': entry_number,
                'error': 'Entry not found'
            }
        
        # Get the text content - try 'comment' field first, then 'text'
        recipe_text = entry_data.get('comment') or entry_data.get('text') or ''
        
        if not recipe_text:
            return {
                'success': False,
                'entryNumber': entry_number,
                'error': 'No recipe text found in entry'
            }
        
        # Extract recipe data using AI
        ai_service = get_ai_service()
        recipe_data = await ai_service.extract_recipe_data(recipe_text)
        
        # Extract CSV filename for subdirectory organization
        import os
        csv_name = os.path.splitext(os.path.basename(csv_file_path))[0]
        
        # Save to JSON file in organized subdirectory
        processor = JSONProcessor()
        output_path = await processor.save_recipe_json(recipe_data, entry_number, subdirectory=csv_name)
        
        return {
            'success': True,
            'entryNumber': entry_number,
            'outputFilePath': output_path
        }
        
    except Exception as e:
        return {
            'success': False,
            'entryNumber': entry_number,
            'error': str(e)
        }


@activity.defn
async def process_recipe_entry_local(csv_file_path: str, entry_number: int) -> Dict[str, Any]:
    """Process a single recipe entry using local parsing (no AI)."""
    try:
        # Parse CSV entry
        parser = CSVParser()
        entry_data = await parser.get_entry(csv_file_path, entry_number)
        
        if not entry_data:
            return {
                'success': False,
                'entryNumber': entry_number,
                'error': 'Entry not found'
            }
        
        # Get the text content - try 'comment' field first, then 'text'
        recipe_text = entry_data.get('comment') or entry_data.get('text') or ''
        
        if not recipe_text:
            return {
                'success': False,
                'entryNumber': entry_number,
                'error': 'No recipe text found in entry'
            }
        
        # Extract recipe data using local parsing
        local_parser = LocalRecipeParser()
        recipe_data = await local_parser.extract_recipe_data(recipe_text)
        
        # Override title with CSV title if available
        csv_title = entry_data.get('title', '').strip()
        if csv_title and csv_title != recipe_data.title:
            recipe_data.title = csv_title
        
        # Use the first paragraph as description if we don't have one
        if not recipe_data.description and recipe_text:
            # Extract first paragraph (before the Ingredients section)
            first_para = recipe_text.split('\n\n')[0]
            if len(first_para) < 500 and 'ingredient' not in first_para.lower():
                recipe_data.description = first_para.strip()
        
        # Extract CSV filename for subdirectory organization
        import os
        csv_name = os.path.splitext(os.path.basename(csv_file_path))[0]
        
        # Save to JSON file in organized subdirectory
        processor = JSONProcessor()
        output_path = await processor.save_recipe_json(recipe_data, entry_number, subdirectory=csv_name)
        
        return {
            'success': True,
            'entryNumber': entry_number,
            'outputFilePath': output_path
        }
        
    except Exception as e:
        return {
            'success': False,
            'entryNumber': entry_number,
            'error': str(e)
        }


@activity.defn
async def load_json_to_db(json_file_path: str) -> Dict[str, Any]:
    """Load a recipe JSON file into the database."""
    try:
        # Load and parse JSON
        processor = JSONProcessor()
        recipe_json = await processor.load_recipe_json(json_file_path)
        
        # Convert RecipeSchema format to database Recipe format
        from ..models.recipe import Recipe, RecipeIngredient, Ingredient, Measurement
        from ..models.schemas import RecipeSchema
        from ..utils.ingredient_parser import get_ingredient_parser
        
        # Handle old format (with entryNumber, metadata, recipeData wrapper)
        if 'recipeData' in recipe_json:
            recipe_json = recipe_json['recipeData']
        
        # Convert old ingredient format to new format if needed
        if 'ingredients' in recipe_json and recipe_json['ingredients']:
            converted_ingredients = []
            for ing in recipe_json['ingredients']:
                if 'name' in ing and 'item' not in ing:
                    # Old format: {name, quantity, unit, notes}
                    # New format: {item, amount, notes}
                    quantity = ing.get('quantity', '')
                    unit = ing.get('unit', '')
                    amount_str = f"{quantity} {unit}".strip() if quantity or unit else "to taste"
                    
                    converted_ingredients.append({
                        'item': ing.get('name', ''),
                        'amount': amount_str,
                        'notes': ing.get('notes')
                    })
                else:
                    # Already in new format
                    converted_ingredients.append(ing)
            recipe_json['ingredients'] = converted_ingredients
        
        # Convert old instruction format if needed (already strings in old format)
        if 'instructions' in recipe_json and recipe_json['instructions']:
            if isinstance(recipe_json['instructions'][0], str):
                # Old format: list of strings - convert to new format
                converted_instructions = []
                for idx, inst_str in enumerate(recipe_json['instructions'], 1):
                    # Try to extract title from instruction string
                    if ':' in inst_str and inst_str.index(':') < 50:
                        parts = inst_str.split(':', 1)
                        title = parts[0].strip()
                        description = parts[1].strip()
                    else:
                        title = f"Step {idx}"
                        description = inst_str
                    
                    converted_instructions.append({
                        'step': idx,
                        'title': title,
                        'description': description
                    })
                recipe_json['instructions'] = converted_instructions
        
        # Parse as RecipeSchema
        recipe_schema = RecipeSchema.model_validate(recipe_json)
        
        # Convert instructions from objects to simple strings
        instructions = []
        for inst in recipe_schema.instructions:
            if inst.title and inst.title != f"Step {inst.step}":
                instructions.append(f"{inst.title}: {inst.description}")
            else:
                instructions.append(inst.description)
        
        # Convert ingredients using the parser
        parser = get_ingredient_parser()
        recipe_ingredients = []
        
        for idx, ing_schema in enumerate(recipe_schema.ingredients):
            # Skip malformed ingredients (entire recipe in one field)
            if len(ing_schema.item) > 500:
                print(f"Warning: Skipping malformed ingredient (too long: {len(ing_schema.item)} chars)")
                continue
            
            # Parse the amount string
            amount, measurement_name, unit_type = parser.parse_amount_string(ing_schema.amount)
            
            # Clean the ingredient name
            ingredient_name = parser.parse_ingredient_item(ing_schema.item)
            if not ingredient_name:
                ingredient_name = ing_schema.item  # Fallback to original
            
            # Truncate to fit database constraints (VARCHAR(200))
            ingredient_name = ingredient_name[:200] if ingredient_name else "Unknown"
            if measurement_name:
                measurement_name = measurement_name[:100]
            
            # Truncate notes if needed
            notes = ing_schema.notes[:500] if ing_schema.notes else None
            
            # Create RecipeIngredient object
            recipe_ingredient = RecipeIngredient(
                ingredient=Ingredient(name=ingredient_name),
                measurement=Measurement(
                    name=measurement_name,
                    abbreviation=None,
                    unit_type=unit_type
                ) if measurement_name else None,
                amount=amount,
                notes=notes,
                order_index=idx + 1
            )
            
            recipe_ingredients.append(recipe_ingredient)
        
        # Create recipe (with truncation for database constraints)
        recipe = Recipe(
            title=recipe_schema.title[:500] if recipe_schema.title else "Untitled Recipe",
            description=recipe_schema.description[:1000] if recipe_schema.description else None,
            instructions=instructions,
            ingredients=recipe_ingredients,
            prep_time_minutes=None,  # TODO: Parse time strings
            cook_time_minutes=None,
            servings=None
        )
        
        # Check if recipe already exists
        existing = await RecipeService.get_by_title(recipe.title)
        if existing:
            return {
                'success': True,
                'jsonFilePath': json_file_path,
                'recipeId': existing.id,
                'title': recipe.title,
                'alreadyExists': True
            }
        
        # Create new recipe with ingredients
        created_recipe = await RecipeService.create(recipe)
        
        if not created_recipe:
            return {
                'success': False,
                'jsonFilePath': json_file_path,
                'error': f"Failed to create recipe: RecipeService.create returned None for '{recipe.title[:50] if recipe.title else 'No title'}'"
            }
        
        return {
            'success': True,
            'jsonFilePath': json_file_path,
            'recipeId': created_recipe.id,
            'title': recipe.title,
            'alreadyExists': False
        }
        
    except Exception as e:
        return {
            'success': False,
            'jsonFilePath': json_file_path,
            'error': str(e)
        }
