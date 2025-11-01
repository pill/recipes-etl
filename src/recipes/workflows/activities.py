"""Temporal activities for recipe processing."""

import json
import os
from typing import Dict, Any, Optional, List
from temporalio import activity
from ..services.ai_service import get_ai_service
from ..services.recipe_service import RecipeService
from ..utils.csv_parser import CSVParser
from ..utils.json_processor import JSONProcessor
from ..utils.local_parser import LocalRecipeParser
from ..models.schemas import RecipeSchema, RecipeIngredientSchema, RecipeInstructionSchema


async def _parse_structured_recipe(entry_data: Dict[str, Any]) -> RecipeSchema:
    """Parse structured recipe data from Stromberg CSV format.
    
    Args:
        entry_data: Dictionary with 'ingredients' and 'directions' as JSON arrays
        
    Returns:
        RecipeSchema object
    """
    import ast
    
    # Parse ingredients from JSON array string
    ingredients_str = entry_data.get('ingredients', '[]')
    try:
        ingredients_list = ast.literal_eval(ingredients_str)
    except (ValueError, SyntaxError):
        ingredients_list = []
    
    # Parse directions from JSON array string  
    directions_str = entry_data.get('directions', '[]')
    try:
        directions_list = ast.literal_eval(directions_str)
    except (ValueError, SyntaxError):
        directions_list = []
    
    # Convert ingredients to RecipeIngredientSchema
    recipe_ingredients = []
    for ing_str in ingredients_list:
        if isinstance(ing_str, str) and ing_str.strip():
            # Parse ingredient string (e.g., "1 cup flour")
            parsed_ing = _parse_ingredient_string(ing_str.strip())
            recipe_ingredients.append(parsed_ing)
    
    # Convert directions to RecipeInstructionSchema
    recipe_instructions = []
    for i, dir_str in enumerate(directions_list, 1):
        if isinstance(dir_str, str) and dir_str.strip():
            recipe_instructions.append(RecipeInstructionSchema(
                step=i,
                title=f"Step {i}",
                description=dir_str.strip()
            ))
    
    # Extract metadata using local parser
    local_parser = LocalRecipeParser()
    title = entry_data.get('title', '').strip()
    
    # Create basic recipe
    recipe = RecipeSchema(
        title=title or "Untitled Recipe",
        description=None,
        ingredients=recipe_ingredients,
        instructions=recipe_instructions,
        prepTime=None,
        cookTime=None,
        difficulty=None,
        cuisine=None,
        mealType=None,
        dietaryTags=None
    )
    
    # Extract metadata from title and ingredients
    if title:
        # Create ingredients list for metadata extraction
        ingredients_list = [ing.item for ing in recipe_ingredients if ing.item]
        
        recipe.difficulty = local_parser._extract_difficulty("", title)
        recipe.cuisine = local_parser._extract_cuisine("", title, ingredients_list)
        recipe.mealType = local_parser._extract_meal_type("", title, ingredients_list)
        recipe.dietaryTags = local_parser._extract_dietary_tags("", title, ingredients_list)
    
    return recipe


def _parse_ingredient_string(ing_str: str) -> RecipeIngredientSchema:
    """Parse ingredient string like '1 cup flour' into structured data."""
    import re
    
    # Common patterns for ingredients
    patterns = [
        r'^(\d+(?:\.\d+)?(?:\/\d+)?)\s*([a-zA-Z]+)\s+(.+)$',  # "1 cup flour"
        r'^(\d+(?:\.\d+)?(?:\/\d+)?)\s+(.+)$',  # "2 eggs"
        r'^(.+)$',  # "salt to taste"
    ]
    
    for pattern in patterns:
        match = re.match(pattern, ing_str.strip())
        if match:
            groups = match.groups()
            if len(groups) == 3:  # "1 cup flour"
                return RecipeIngredientSchema(
                    item=groups[2],  # ingredient name
                    amount=f"{groups[0]} {groups[1]}"  # "1 cup"
                )
            elif len(groups) == 2:  # "2 eggs"
                return RecipeIngredientSchema(
                    item=groups[1],  # ingredient name
                    amount=groups[0]  # "2"
                )
            else:  # "salt to taste"
                return RecipeIngredientSchema(
                    item=groups[0],  # ingredient name
                    amount="to taste"
                )
    
    # Fallback
    return RecipeIngredientSchema(
        item=ing_str,
        amount=""
    )


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
        
        # Handle different CSV formats
        # Stromberg format: has 'ingredients' and 'directions' as JSON arrays
        # Reddit format: has 'comment' or 'text' as unstructured text
        
        if 'ingredients' in entry_data and 'directions' in entry_data:
            # Stromberg format - structured data
            recipe_data = await _parse_structured_recipe(entry_data)
        else:
            # Reddit format - unstructured text
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
        # Only for Reddit format (unstructured text)
        if 'ingredients' not in entry_data and not recipe_data.description:
            recipe_text = entry_data.get('comment') or entry_data.get('text') or ''
            if recipe_text:
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
        import re
        
        # Clean up <UNKNOWN> and null values for optional fields
        # Schema expects either None or a valid string, not "<UNKNOWN>"
        for field in ['prepTime', 'cookTime', 'chillTime', 'panSize', 'difficulty', 'cuisine', 'mealType']:
            if field in recipe_json:
                value = recipe_json[field]
                # Handle various invalid/empty values
                if value == '<UNKNOWN>' or value == 'null' or value == '':
                    recipe_json[field] = None
                # Convert integers to strings for time fields
                elif field in ['prepTime', 'cookTime', 'chillTime'] and isinstance(value, (int, float)):
                    recipe_json[field] = f"{int(value)} minutes"
        
        # Handle difficulty specifically - normalize case and ensure it's a valid value or None
        if 'difficulty' in recipe_json and recipe_json['difficulty']:
            # Normalize to lowercase
            difficulty_value = str(recipe_json['difficulty']).lower().strip()
            valid_difficulty = {'easy', 'medium', 'hard'}
            if difficulty_value in valid_difficulty:
                recipe_json['difficulty'] = difficulty_value
            else:
                recipe_json['difficulty'] = None
        
        # Handle mealType specifically - normalize and ensure it's a valid value or None
        if 'mealType' in recipe_json and recipe_json['mealType']:
            # Normalize to lowercase
            meal_type_value = str(recipe_json['mealType']).lower().strip()
            valid_meal_types = {'breakfast', 'lunch', 'dinner', 'snack', 'dessert'}
            
            # Map common variations to valid values
            meal_type_mapping = {
                'side dish': 'snack',
                'side': 'snack',
                'soup': 'lunch',
                'appetizer': 'snack',
                'beverage': 'snack',
                'drink': 'snack'
            }
            
            # Check if it's already valid
            if meal_type_value in valid_meal_types:
                recipe_json['mealType'] = meal_type_value
            # Try mapping
            elif meal_type_value in meal_type_mapping:
                recipe_json['mealType'] = meal_type_mapping[meal_type_value]
            else:
                recipe_json['mealType'] = None
        
        # Parse as RecipeSchema
        recipe_schema = RecipeSchema.model_validate(recipe_json)
        
        # Convert instructions from objects to simple strings
        instructions = []
        for inst in recipe_schema.instructions:
            if inst.title and inst.title != f"Step {inst.step}":
                instructions.append(f"{inst.title}: {inst.description}")
            else:
                instructions.append(inst.description)
        
        # Pre-process ingredients to split multi-line blobs
        # Some Kafka recipes have entire ingredient lists in one item with embedded newlines
        expanded_ingredients = []
        for ing_schema in recipe_schema.ingredients:
            item = ing_schema.item
            
            # Check if this ingredient contains multiple lines or bullet points
            if '\n' in item or '・' in item:
                # Split on newlines and bullet points
                sub_items = item.split('\n')
                for sub in sub_items:
                    sub = sub.strip()
                    if not sub:
                        continue
                    # Further split on Japanese bullet points
                    if '・' in sub:
                        mini_items = sub.split('・')
                        for mini in mini_items:
                            mini = mini.strip()
                            if mini and len(mini) > 2:
                                from recipes.models.schemas import RecipeIngredientSchema
                                expanded_ingredients.append(RecipeIngredientSchema(
                                    item=mini,
                                    amount=ing_schema.amount,
                                    notes=ing_schema.notes
                                ))
                    else:
                        if len(sub) > 2:
                            from recipes.models.schemas import RecipeIngredientSchema
                            expanded_ingredients.append(RecipeIngredientSchema(
                                item=sub,
                                amount=ing_schema.amount,
                                notes=ing_schema.notes
                            ))
            else:
                # Normal ingredient, keep as is
                expanded_ingredients.append(ing_schema)
        
        # Convert ingredients using the parser
        parser = get_ingredient_parser()
        recipe_ingredients = []
        skipped_count = 0
        total_count = len(expanded_ingredients)
        
        for idx, ing_schema in enumerate(expanded_ingredients):
            # Skip malformed ingredients (entire recipe in one field)
            if len(ing_schema.item) > 500:
                print(f"Warning: Skipping malformed ingredient (too long: {len(ing_schema.item)} chars)")
                skipped_count += 1
                continue
            
            # Skip ingredients that are clearly not ingredients (contain instructions, formatting, etc.)
            item_lower = ing_schema.item.lower()
            skip_patterns = [
                # Instructions/directions
                'how to do it', 'directions*', 'instructions',
                
                # Cooking actions
                'preheat', 'in the meantime', 'cooking the', 'bake at', 'bake for',
                'blend everything', 'transfer to', 'mix the', 'place the', 'pour the', 
                'take the', 'add the', 'remove from', 'set aside', 'let sit',
                'let it rest', 'allow it to', 'continue cooking', 'reduce heat',
                'warm a', 'heat a', 'bring to a boil', 'fill a', 'fill the',
                
                # Serving and finishing
                'serve with', 'toss to', 'toss and serve', 'combine then serve',
                'garnish with', 'top and serve',
                
                # Common instruction starters (with space to avoid partial matches)
                'rinse ', 'drain ', 'clean and', 'top with', 'cover with', 'line a',
                'spread the', 'evenly spread', 'put crab', 'start by adding',
                'you can find', 'if you', 'grease baking', 'stretch the',
                'cook ', 'stir ',  # Added with space to avoid matching "cooked" or "stir-fry"
                
                # Section headers
                'for the ', 'for filling', 'for topping', 'for garnish', 'for sauce',
                'for dressing', 'for marinade', 'for glaze', 'for frosting',
                
                # Formatting/metadata
                '[video]', '**[', 'recipe*', '&amp;x200b', 'optional as topping',
                'check out my instagram', 'support from', 'if you make this',
                'if you like my recipes',
            ]
            
            if any(pattern in item_lower for pattern in skip_patterns):
                skipped_count += 1
                continue
            
            # Skip standalone notes (just "to taste", "optional", etc.)
            standalone_notes = ['to taste', 'optional', 'as needed', 'if desired', 'for garnish']
            if ing_schema.item.strip().lower() in standalone_notes:
                print(f"Warning: Skipping standalone note: '{ing_schema.item}'")
                skipped_count += 1
                continue
            
            # Skip if ingredient is just a single word and very short (likely noise)
            if len(ing_schema.item.strip()) < 3 and not ing_schema.item.strip().isdigit():
                skipped_count += 1
                continue
            
            # Skip if it looks like a complete sentence (ends with period and contains action verbs)
            if ing_schema.item.strip().endswith('.'):
                # Check if it has multiple words and action verbs (likely an instruction)
                words = ing_schema.item.split()
                action_verbs = ['fill', 'toss', 'serve', 'mix', 'stir', 'cook', 'bake', 'heat', 
                               'add', 'pour', 'place', 'combine', 'whisk', 'fold', 'cut', 'chop']
                if len(words) > 5 and any(verb in item_lower for verb in action_verbs):
                    print(f"Warning: Skipping instruction-like ingredient: '{ing_schema.item[:80]}'")
                    skipped_count += 1
                    continue
            
            # Skip ingredients with only formatting characters
            if not ing_schema.item.strip('*[]()- \n\t'):
                skipped_count += 1
                continue
            
            # Parse the amount string
            amount, measurement_name, unit_type = parser.parse_amount_string(ing_schema.amount)
            
            # Clean the ingredient name
            import html
            
            # Unescape HTML entities (e.g., &amp; -> &)
            ingredient_name = html.unescape(ing_schema.item) if ing_schema.item else ''
            
            # Remove extra whitespace and newlines
            ingredient_name = ' '.join(ingredient_name.split())
            
            # For structured data (like Stromberg), ing_schema.item is already clean
            # Only apply cleaning if it looks like it needs it (has numbers at start)
            if ingredient_name and re.match(r'^\d', ingredient_name):
                # Has leading numbers, try to clean
                cleaned = parser.parse_ingredient_item(ingredient_name)
                if cleaned and len(cleaned) > 2:  # Only use cleaned version if substantial
                    ingredient_name = cleaned
            
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
        
        # Parse time strings to minutes
        def parse_time_to_minutes(time_str: Optional[str]) -> Optional[int]:
            """Convert time string like '30 minutes' or '1 hour' to minutes."""
            if not time_str:
                return None
            
            time_str = time_str.lower().strip()
            
            # Extract numbers
            import re
            numbers = re.findall(r'(\d+(?:\.\d+)?)', time_str)
            if not numbers:
                return None
            
            value = float(numbers[0])
            
            # Check if it's hours
            if 'hour' in time_str or 'hr' in time_str:
                return int(value * 60)
            # Otherwise assume minutes
            else:
                return int(value)
        
        prep_time = parse_time_to_minutes(recipe_schema.prepTime)
        cook_time = parse_time_to_minutes(recipe_schema.cookTime)
        total_time = None
        if prep_time and cook_time:
            total_time = prep_time + cook_time
        elif prep_time:
            total_time = prep_time
        elif cook_time:
            total_time = cook_time
        
        # Log filtering statistics
        if skipped_count > 0:
            print(f"Filtered ingredients for '{recipe_schema.title[:50]}': {len(recipe_ingredients)} valid, {skipped_count} skipped out of {total_count} total")
        
        # Validate we have enough ingredients after filtering
        if len(recipe_ingredients) < 2:
            return {
                'success': False,
                'jsonFilePath': json_file_path,
                'error': f"Recipe has too few valid ingredients after filtering ({len(recipe_ingredients)} valid, {skipped_count} skipped out of {total_count} total). Most ingredients were instructions or malformed data."
            }
        
        # Check if UUID already exists in JSON (generated at JSON creation time)
        existing_uuid = recipe_json.get('uuid')
        
        # Create recipe (with truncation for database constraints)
        # Note: UUID is now based on title only, not ingredients
        recipe = Recipe(
            uuid=existing_uuid,  # Use UUID from JSON if available
            title=recipe_schema.title[:500] if recipe_schema.title else "Untitled Recipe",
            description=recipe_schema.description[:1000] if recipe_schema.description else None,
            instructions=instructions,
            ingredients=recipe_ingredients,
            prep_time_minutes=prep_time,
            cook_time_minutes=cook_time,
            total_time_minutes=total_time,
            servings=None,
            difficulty=recipe_schema.difficulty,
            cuisine_type=recipe_schema.cuisine,
            meal_type=recipe_schema.mealType,
            dietary_tags=recipe_schema.dietaryTags,
            source_url=None  # No source URL for staged recipes
        )
        
        # Validate recipe data before attempting to create
        if not recipe.title or not recipe.title.strip():
            return {
                'success': False,
                'jsonFilePath': json_file_path,
                'error': 'Recipe title is empty or invalid'
            }
        
        if not recipe.ingredients:
            print(f"Warning: Recipe '{recipe.title[:50]}' has no ingredients")
        
        if not recipe.instructions:
            print(f"Warning: Recipe '{recipe.title[:50]}' has no instructions")
        
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
            'uuid': str(created_recipe.uuid),
            'title': recipe.title,
            'alreadyExists': False
        }
        
    except Exception as e:
        return {
            'success': False,
            'jsonFilePath': json_file_path,
            'error': str(e)
        }
