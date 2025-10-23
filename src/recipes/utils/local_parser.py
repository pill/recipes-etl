"""Local recipe parsing utilities (no AI required)."""

import re
from typing import List, Dict, Any, Optional
from ..models.schemas import RecipeSchema, RecipeIngredientSchema, RecipeInstructionSchema


class LocalRecipeParser:
    """Local recipe parser using pattern matching (no AI)."""
    
    def __init__(self):
        """Initialize the local parser."""
        # Common ingredient patterns
        self.ingredient_patterns = [
            r'(\d+(?:\.\d+)?(?:\/\d+)?)\s*([a-zA-Z]+)\s+(.+)',  # "1 cup flour"
            r'(\d+(?:\.\d+)?(?:\/\d+)?)\s+(.+)',  # "2 eggs"
            r'([a-zA-Z]+)\s+(.+)',  # "salt to taste"
        ]
        
        # Common instruction patterns
        self.instruction_patterns = [
            r'(\d+)\.\s*(.+)',  # "1. Mix ingredients"
            r'Step\s+(\d+):\s*(.+)',  # "Step 1: Mix ingredients"
            r'(\d+)\)\s*(.+)',  # "1) Mix ingredients"
        ]
    
    async def extract_recipe_data(self, text: str) -> RecipeSchema:
        """Extract recipe data from text using pattern matching."""
        # Clean and normalize the text
        text = text.strip()
        
        # Try to fix common encoding/escape issues
        text = text.replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t').replace('\\*', '*')
        
        # Also try to split by various newline representations
        # Sometimes Reddit text has multiple spaces representing newlines
        if '\n' not in text and '  ' in text:
            # Try to detect paragraph breaks (multiple spaces)
            text = text.replace('  ', '\n')
        
        # Split into lines for line-based processing
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Extract title (look for title patterns or use first substantial line)
        title = self._extract_title(lines, text)
        
        # Extract description (look for description sections)
        description = self._extract_description(lines, text)
        
        # Extract ingredients - try multiple methods
        ingredients = self._extract_ingredients_robust(text, lines)
        
        # Extract instructions - try multiple methods  
        instructions = self._extract_instructions_robust(text, lines)
        
        # If we didn't get good ingredients/instructions, try lenient extraction
        if not ingredients or len(ingredients) == 0:
            ingredients = self._extract_ingredients_lenient(text, lines)
            
            if not ingredients:
                # Last resort: create a single placeholder
                ingredients = [RecipeIngredientSchema(
                    item="Ingredients listed in recipe text",
                    amount="See recipe",
                    notes=None
                )]
        
        if not instructions or len(instructions) == 0:
            instructions = self._extract_instructions_lenient(text, lines)
            
            if not instructions:
                # Last resort: create a single placeholder
                instructions = [RecipeInstructionSchema(
                    step=1,
                    title="Preparation",
                    description="See full recipe text for instructions"
                )]
        
        # Extract timing information
        prep_time = self._extract_prep_time(text)
        cook_time = self._extract_cook_time(text)
        chill_time = self._extract_chill_time(text)
        
        # Extract pan size information
        pan_size = self._extract_pan_size(text)
        
        # Extract additional metadata
        difficulty = self._extract_difficulty(text, title)
        cuisine = self._extract_cuisine(text, title, ingredients)
        meal_type = self._extract_meal_type(text, title, ingredients)
        dietary_tags = self._extract_dietary_tags(text, title, ingredients)
        
        return RecipeSchema(
            title=title,
            description=description,
            ingredients=ingredients,
            instructions=instructions,
            prepTime=prep_time,
            cookTime=cook_time,
            chillTime=chill_time,
            panSize=pan_size,
            difficulty=difficulty,
            cuisine=cuisine,
            mealType=meal_type,
            dietaryTags=dietary_tags
        )
    
    def _extract_title(self, lines: List[str], text: str) -> str:
        """Extract recipe title from lines."""
        # Look for common title patterns
        title_patterns = [
            r'(?:^|\n)([A-Z][^.!?\n]{10,100})(?:\n|$)',  # Capitalized line
            r'(?:Recipe:|Title:)\s*(.+?)(?:\n|$)',
            r'\*\*([^*]+)\*\*',  # Bold markdown
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                potential_title = match.group(1).strip()
                # Make sure it's not an ingredient or instruction
                if not self._is_ingredient_line(potential_title) and not self._is_instruction_line(potential_title):
                    return potential_title
        
        # Fallback: use first substantial line
        for line in lines[:5]:  # Check first 5 lines
            if len(line) > 10 and len(line) < 150:
                if not self._is_ingredient_line(line) and not self._is_instruction_line(line):
                    return line
        
        return "Untitled Recipe"
    
    def _extract_description(self, lines: List[str], text: str) -> Optional[str]:
        """Extract recipe description from lines."""
        # Look for description patterns
        desc_patterns = [
            r'(?:Description:|About:)\s*(.+?)(?:\n\n|Ingredient|Direction|Method|Step)',
            r'(?:^|\n)([^*\n]{50,200}?)(?:\n\n|\*\*Ingredient)',
        ]
        
        for pattern in desc_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                desc = match.group(1).strip()
                if len(desc) > 20:
                    return desc
        
        # Fallback: Look for a descriptive line
        for i, line in enumerate(lines[1:6]):  # Skip title, check next 5 lines
            if len(line) > 30 and len(line) < 300:
                if not self._is_ingredient_line(line) and not self._is_instruction_line(line):
                    # Make sure it doesn't look like a heading
                    if not line.isupper() and not line.startswith('**'):
                        return line
        
        return None
    
    def _extract_ingredients(self, text: str) -> List[RecipeIngredientSchema]:
        """Extract ingredients from text."""
        ingredients = []
        lines = text.split('\n')
        
        # Find the ingredients section
        in_ingredients_section = False
        
        for line in lines:
            line = line.strip()
            
            # Check if we're entering the ingredients section
            if any(keyword in line.lower() for keyword in ['ingredients', 'ingredient list', 'what you need']):
                in_ingredients_section = True
                continue
            
            # Check if we're leaving the ingredients section
            if in_ingredients_section and any(keyword in line.lower() for keyword in ['instructions', 'directions', 'steps', 'method']):
                break
            
            # Extract ingredient if we're in the ingredients section
            if in_ingredients_section and line:
                ingredient = self._parse_ingredient_line(line)
                if ingredient:
                    ingredients.append(ingredient)
        
        # If no ingredients section found, try to extract from the whole text
        if not ingredients:
            for line in lines:
                line = line.strip()
                if line and self._is_ingredient_line(line):
                    ingredient = self._parse_ingredient_line(line)
                    if ingredient:
                        ingredients.append(ingredient)
        
        return ingredients
    
    def _extract_instructions(self, text: str) -> List[RecipeInstructionSchema]:
        """Extract instructions from text."""
        instructions = []
        lines = text.split('\n')
        
        # Find the instructions section
        in_instructions_section = False
        step_number = 1
        
        for line in lines:
            line = line.strip()
            
            # Check if we're entering the instructions section
            if any(keyword in line.lower() for keyword in ['instructions', 'directions', 'steps', 'method']):
                in_instructions_section = True
                continue
            
            # Extract instruction if we're in the instructions section
            if in_instructions_section and line:
                instruction = self._parse_instruction_line(line, step_number)
                if instruction:
                    instructions.append(instruction)
                    step_number += 1
        
        # If no instructions section found, try to extract from the whole text
        if not instructions:
            step_number = 1
            for line in lines:
                line = line.strip()
                if line and self._is_instruction_line(line):
                    instruction = self._parse_instruction_line(line, step_number)
                    if instruction:
                        instructions.append(instruction)
                        step_number += 1
        
        return instructions
    
    def _extract_prep_time(self, text: str) -> Optional[str]:
        """Extract preparation time from text."""
        patterns = [
            r'prep[aration]*\s+time:?\s*(\d+(?:\.\d+)?\s*(?:minute|hour|min|hr)s?)',
            r'preparation:?\s*(\d+(?:\.\d+)?\s*(?:minute|hour|min|hr)s?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_cook_time(self, text: str) -> Optional[str]:
        """Extract cooking time from text."""
        patterns = [
            r'cook[ing]*\s+time:?\s*(\d+(?:\.\d+)?\s*(?:minute|hour|min|hr)s?)',
            r'cooking:?\s*(\d+(?:\.\d+)?\s*(?:minute|hour|min|hr)s?)',
            r'bake\s+(?:for\s+)?(\d+(?:\.\d+)?\s*(?:minute|hour|min|hr)s?)',
            r'total\s+cook\s+time:?\s*(\d+(?:\.\d+)?\s*(?:minute|hour|min|hr)s?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_chill_time(self, text: str) -> Optional[str]:
        """Extract chilling time from text."""
        patterns = [
            r'chill[ing]*\s+time:?\s*(\d+(?:\.\d+)?\s*(?:minute|hour|min|hr)s?)',
            r'refrigerate\s+for\s+(\d+(?:\.\d+)?\s*(?:minute|hour|min|hr)s?)',
            r'let\s+rest\s+for\s+(\d+(?:\.\d+)?\s*(?:minute|hour|min|hr)s?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_pan_size(self, text: str) -> Optional[str]:
        """Extract pan size from text."""
        patterns = [
            r'(\d+x\d+\s*(?:inch|in|cm))',
            r'(\d+\s*(?:inch|in|cm)\s+pan)',
            r'(\d+\s*(?:quart|qt|liter|l)\s+pot)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_difficulty(self, text: str, title: str) -> Optional[str]:
        """Extract difficulty level from text and title."""
        # Check for explicit difficulty mentions
        text_lower = text.lower()
        title_lower = title.lower()
        combined = f"{title_lower} {text_lower}"
        
        # Explicit difficulty mentions
        if any(word in combined for word in ['beginner', 'simple', 'quick', 'easy']):
            return 'easy'
        if any(word in combined for word in ['intermediate', 'medium']):
            return 'medium'
        if any(word in combined for word in ['advanced', 'difficult', 'hard', 'complex', 'challenging']):
            return 'hard'
        
        # Heuristic based on recipe complexity
        # Count steps/ingredients as complexity indicators
        ingredient_count = len(re.findall(r'(?:^|\n)\s*[-*•]', text))
        step_count = len(re.findall(r'(?:^|\n)\s*\d+[.)]', text))
        
        # Check for advanced techniques
        advanced_techniques = [
            'sous vide', 'tempering', 'emulsify', 'caramelize', 'braise',
            'confit', 'deglaze', 'flambe', 'reduce', 'blanch', 'score'
        ]
        has_advanced = any(tech in text_lower for tech in advanced_techniques)
        
        if has_advanced or ingredient_count > 15 or step_count > 10:
            return 'hard'
        elif ingredient_count > 8 or step_count > 5:
            return 'medium'
        elif ingredient_count > 0 or step_count > 0:
            return 'easy'
        
        return None
    
    def _extract_cuisine(self, text: str, title: str, ingredients: List) -> Optional[str]:
        """Extract cuisine type from text, title, and ingredients."""
        text_lower = text.lower()
        title_lower = title.lower()
        combined = f"{title_lower} {text_lower}"
        
        # Cuisine keywords mapping
        cuisine_keywords = {
            'Italian': ['italian', 'pasta', 'risotto', 'parmigiano', 'parmesan', 'mozzarella', 
                       'basil', 'marinara', 'carbonara', 'lasagna', 'tiramisu', 'bruschetta'],
            'Mexican': ['mexican', 'taco', 'burrito', 'enchilada', 'salsa', 'guacamole', 
                       'tortilla', 'cilantro', 'jalapeño', 'chipotle', 'fajita', 'quesadilla'],
            'Chinese': ['chinese', 'stir fry', 'wok', 'soy sauce', 'ginger', 'bok choy',
                       'szechuan', 'dim sum', 'dumpling', 'lo mein', 'chow mein'],
            'Japanese': ['japanese', 'sushi', 'ramen', 'miso', 'teriyaki', 'tempura',
                        'wasabi', 'udon', 'soba', 'sake', 'mirin', 'nori'],
            'Thai': ['thai', 'pad thai', 'curry paste', 'lemongrass', 'fish sauce',
                    'coconut milk', 'basil thai', 'galangal', 'kaffir lime'],
            'Indian': ['indian', 'curry', 'naan', 'tandoori', 'masala', 'tikka',
                      'cumin', 'turmeric', 'garam masala', 'cardamom', 'biryani'],
            'French': ['french', 'béarnaise', 'hollandaise', 'croissant', 'baguette',
                      'coq au vin', 'ratatouille', 'crème', 'bourguignon', 'soufflé'],
            'Greek': ['greek', 'feta', 'tzatziki', 'gyro', 'moussaka', 'baklava',
                     'oregano', 'kalamata', 'spanakopita', 'souvlaki'],
            'Korean': ['korean', 'kimchi', 'bibimbap', 'bulgogi', 'gochujang',
                      'ssamjang', 'korean bbq', 'banchan'],
            'Vietnamese': ['vietnamese', 'pho', 'banh mi', 'spring roll', 'nuoc mam'],
            'Spanish': ['spanish', 'paella', 'tapas', 'chorizo', 'gazpacho', 'sangria'],
            'American': ['bbq', 'barbecue', 'burger', 'hotdog', 'mac and cheese', 
                        'southern', 'cajun', 'creole', 'fried chicken'],
            'Middle Eastern': ['middle eastern', 'hummus', 'falafel', 'tahini', 'shawarma',
                             'pita', 'chickpea', 'couscous', 'kebab', 'baba ganoush'],
            'Mediterranean': ['mediterranean', 'olive oil', 'feta', 'olives', 'lemon'],
        }
        
        # Check for cuisine keywords
        for cuisine, keywords in cuisine_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in combined)
            if matches >= 2:  # Require at least 2 keyword matches
                return cuisine
            elif matches == 1 and any(keyword in title_lower for keyword in keywords):
                # Single match in title is enough
                return cuisine
        
        return None
    
    def _extract_meal_type(self, text: str, title: str, ingredients: List) -> Optional[str]:
        """Extract meal type from text, title, and ingredients."""
        text_lower = text.lower()
        title_lower = title.lower()
        combined = f"{title_lower} {text_lower}"
        
        # Meal type keywords
        meal_keywords = {
            'breakfast': ['breakfast', 'pancake', 'waffle', 'omelette', 'omelet', 'french toast',
                         'cereal', 'granola', 'muffin', 'bagel', 'croissant', 'eggs benedict',
                         'breakfast burrito', 'brunch', 'morning'],
            'lunch': ['lunch', 'sandwich', 'wrap', 'salad', 'soup and salad', 'midday'],
            'dinner': ['dinner', 'supper', 'main course', 'entrée', 'entree', 'evening meal'],
            'dessert': ['dessert', 'cake', 'cookie', 'brownie', 'pie', 'tart', 'pudding',
                       'ice cream', 'sorbet', 'mousse', 'truffle', 'candy', 'sweet', 'frosting',
                       'cheesecake', 'cupcake', 'macaron', 'tiramisu', 'parfait', 'fudge'],
            'snack': ['snack', 'appetizer', 'finger food', 'dip', 'chips', 'popcorn',
                     'energy ball', 'trail mix', 'tapas', 'mezze'],
        }
        
        # Check for explicit meal type mentions
        for meal_type, keywords in meal_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in combined)
            if matches >= 1:
                # Prioritize title matches
                if any(keyword in title_lower for keyword in keywords):
                    return meal_type
                # Otherwise use first match
                return meal_type
        
        # Heuristic: desserts usually have sugar/chocolate
        dessert_ingredients = ['sugar', 'chocolate', 'cocoa', 'honey', 'maple syrup', 'vanilla extract']
        if any(ing in text_lower for ing in dessert_ingredients):
            # Check if it's likely a dessert (not just a sweet sauce for dinner)
            if not any(savory in combined for savory in ['chicken', 'beef', 'pork', 'fish', 'meat', 'pasta']):
                return 'dessert'
        
        return None
    
    def _extract_dietary_tags(self, text: str, title: str, ingredients: List) -> Optional[List[str]]:
        """Extract dietary tags from text, title, and ingredients."""
        text_lower = text.lower()
        title_lower = title.lower()
        combined = f"{title_lower} {text_lower}"
        
        tags = []
        
        # Check for explicit dietary mentions
        if any(word in combined for word in ['vegetarian', 'veggie']):
            tags.append('vegetarian')
        if any(word in combined for word in ['vegan', 'plant-based', 'plant based']):
            tags.append('vegan')
        if any(word in combined for word in ['gluten-free', 'gluten free', 'gf ']):
            tags.append('gluten-free')
        if any(word in combined for word in ['dairy-free', 'dairy free', 'lactose-free']):
            tags.append('dairy-free')
        if any(word in combined for word in ['keto', 'ketogenic', 'low-carb', 'low carb']):
            tags.append('keto')
        if any(word in combined for word in ['paleo', 'paleolithic']):
            tags.append('paleo')
        if any(word in combined for word in ['whole30', 'whole 30']):
            tags.append('whole30')
        if any(word in combined for word in ['low-fat', 'low fat', 'fat-free']):
            tags.append('low-fat')
        if any(word in combined for word in ['sugar-free', 'sugar free', 'no sugar']):
            tags.append('sugar-free')
        if any(word in combined for word in ['nut-free', 'nut free']):
            tags.append('nut-free')
        if any(word in combined for word in ['soy-free', 'soy free']):
            tags.append('soy-free')
        if any(word in combined for word in ['kosher']):
            tags.append('kosher')
        if any(word in combined for word in ['halal']):
            tags.append('halal')
        
        # Heuristic: check for animal products to determine vegetarian/vegan
        if not tags:
            animal_products = ['chicken', 'beef', 'pork', 'fish', 'meat', 'bacon', 'sausage',
                             'turkey', 'lamb', 'duck', 'seafood', 'shrimp', 'salmon']
            has_meat = any(product in text_lower for product in animal_products)
            
            dairy_products = ['milk', 'cheese', 'butter', 'cream', 'yogurt', 'whey']
            has_dairy = any(product in text_lower for product in dairy_products)
            
            eggs_present = 'egg' in text_lower
            
            if not has_meat and not has_dairy and not eggs_present:
                tags.append('vegan')
                tags.append('vegetarian')
            elif not has_meat:
                tags.append('vegetarian')
        
        return tags if tags else None
    
    def _is_ingredient_line(self, line: str) -> bool:
        """Check if a line looks like an ingredient."""
        # Check for common ingredient patterns
        for pattern in self.ingredient_patterns:
            if re.search(pattern, line):
                return True
        
        # Check for common ingredient keywords
        ingredient_keywords = ['cup', 'tablespoon', 'teaspoon', 'pound', 'ounce', 'gram', 'kg', 'ml', 'liter']
        return any(keyword in line.lower() for keyword in ingredient_keywords)
    
    def _is_instruction_line(self, line: str) -> bool:
        """Check if a line looks like an instruction."""
        # Check for numbered instructions
        for pattern in self.instruction_patterns:
            if re.search(pattern, line):
                return True
        
        # Check for common instruction keywords
        instruction_keywords = ['mix', 'stir', 'cook', 'bake', 'fry', 'boil', 'heat', 'add', 'remove', 'serve']
        return any(keyword in line.lower() for keyword in instruction_keywords)
    
    def _parse_ingredient_line(self, line: str) -> Optional[RecipeIngredientSchema]:
        """Parse an ingredient line into structured data."""
        # Try different patterns
        for pattern in self.ingredient_patterns:
            match = re.search(pattern, line)
            if match:
                groups = match.groups()
                if len(groups) == 3:  # amount, unit, ingredient
                    return RecipeIngredientSchema(
                        item=groups[2].strip(),
                        amount=f"{groups[0]} {groups[1]}".strip()
                    )
                elif len(groups) == 2:  # amount, ingredient
                    return RecipeIngredientSchema(
                        item=groups[1].strip(),
                        amount=groups[0].strip()
                    )
        
        # If no pattern matches, treat the whole line as an ingredient
        return RecipeIngredientSchema(
            item=line.strip(),
            amount=""
        )
    
    def _parse_instruction_line(self, line: str, step_number: int) -> Optional[RecipeInstructionSchema]:
        """Parse an instruction line into structured data."""
        # Try different patterns
        for pattern in self.instruction_patterns:
            match = re.search(pattern, line)
            if match:
                groups = match.groups()
                parsed_step_number = int(groups[0])
                instruction_text = groups[1].strip()
                
                # Extract title and description
                if ':' in instruction_text:
                    title, description = instruction_text.split(':', 1)
                    title = title.strip()
                    description = description.strip()
                else:
                    title = f"Step {parsed_step_number}"
                    description = instruction_text
                
                return RecipeInstructionSchema(
                    step=parsed_step_number,
                    title=title,
                    description=description
                )
        
        # If no pattern matches, treat as a simple instruction
        return RecipeInstructionSchema(
            step=step_number,
            title=f"Step {step_number}",
            description=line.strip()
        )
    
    def _extract_ingredients_robust(self, text: str, lines: List[str]) -> List[RecipeIngredientSchema]:
        """Robust ingredient extraction that works with inline or multi-line text."""
        ingredients = []
        
        # First, try to find the ingredient section in the text
        # Look for patterns like "Ingredients:" or "**Ingredients**"
        ingredient_pattern = r'(?:\*\*)?Ingredients?(?:\*\*)?:?\s*(.*?)(?=(?:\*\*)?(?:Instructions?|Directions?|Method|Steps?|Preparation)(?:\*\*)?:|\Z)'
        match = re.search(ingredient_pattern, text, re.IGNORECASE | re.DOTALL)
        
        if match:
            ingredient_text = match.group(1).strip()
            
            # Split by numbered items (1. 2. 3.) or bullet points (* - •)
            # This works whether items are on separate lines or same line
            ingredient_items = re.split(r'\d+\.\s+|[\*\-•]\s+', ingredient_text)
            
            # Remove empty items and the first item if it's just whitespace/header
            ingredient_items = [item.strip() for item in ingredient_items if item.strip()]
            
            for item in ingredient_items:
                item = item.strip()
                if not item or len(item) < 3:
                    continue
                
                # Skip if it looks like a section header
                if item.lower() in ['ingredients', 'ingredient list', 'what you need']:
                    continue
                
                # Skip if it's weirdly short (probably parsing error)
                if len(item) < 5:
                    continue
                
                # Parse the ingredient
                ingredient = self._parse_ingredient_smart(item)
                if ingredient and len(ingredients) < 30:  # Cap at 30
                    ingredients.append(ingredient)
        
        # If we got some ingredients, return them
        if ingredients:
            return ingredients
        
        # Fall back to line-based extraction
        return self._extract_ingredients_improved(text, lines)
    
    def _extract_instructions_robust(self, text: str, lines: List[str]) -> List[RecipeInstructionSchema]:
        """Robust instruction extraction that works with inline or multi-line text."""
        instructions = []
        
        # First, try to find the instructions section in the text
        instruction_pattern = r'(?:\*\*)?(?:Instructions?|Directions?|Method|Steps?)(?:\*\*)?:?\s*(.*?)(?=\Z)'
        match = re.search(instruction_pattern, text, re.IGNORECASE | re.DOTALL)
        
        if match:
            instruction_text = match.group(1).strip()
            
            # Split by numbered items (1. 2. 3.) or bullet points (* - •)
            # This works whether items are on separate lines or same line
            instruction_items = re.split(r'\d+\.\s+|[\*\-•]\s+', instruction_text)
            
            # Remove empty items
            instruction_items = [item.strip() for item in instruction_items if item.strip()]
            
            step = 1
            for item in instruction_items:
                item = item.strip()
                if not item or len(item) < 15:  # Instructions should be substantial
                    continue
                
                # Skip section headers (usually short and end with colon or are in bold markers)
                if item.lower() in ['instructions', 'directions', 'method', 'steps']:
                    continue
                
                # Skip if it looks like a section header (ends with : and is short)
                if item.endswith(':') and len(item) < 40:
                    continue
                
                # Skip if it contains bold markers and is very short (likely a header)
                if '**' in item and len(item.replace('*', '')) < 50:
                    continue
                
                # Skip instructions that are just video links or references
                if item.lower().startswith(('video recipe is', '(video', 'recipe video')):
                    continue
                
                # Clean up the text
                clean_item = item.replace('**', '').strip()
                
                # Remove leading parentheses and video links
                clean_item = re.sub(r'^\([^)]*\):\s*', '', clean_item)
                
                # Create instruction if it's still substantial
                if step <= 30 and len(clean_item) >= 15:  # Cap at 30 steps
                    instructions.append(RecipeInstructionSchema(
                        step=step,
                        title=f"Step {step}",
                        description=clean_item
                    ))
                    step += 1
        
        # If we got some instructions, return them
        if instructions:
            return instructions
        
        # Fall back to line-based extraction
        return self._extract_instructions_improved(text, lines)
    
    def _parse_ingredient_smart(self, text: str) -> Optional[RecipeIngredientSchema]:
        """Smart ingredient parsing from a single text string."""
        if not text or len(text) > 200:
            return None
        
        # Better pattern: Look for amount at the start, followed by optional unit, then ingredient
        # Handles: "2 cups flour", "1/2 tsp salt", "About 1.5 packages worth of lady fingers"
        # Pattern breakdown:
        # - Optional leading words like "About"
        # - Number (integer, decimal, or fraction)
        # - Optional unit (c, cup, tbsp, packages, etc)
        # - The rest is the ingredient name
        
        # Try multiple patterns in order of specificity
        patterns = [
            # "Ground beef (1.8 lb / 800 g)" - extract amount from parentheses
            r'^(.+?)\s*\(([^)]+)\).*$',
            # "2 cups flour" or "1/2 tsp salt"
            r'^([\d/\-\.]+)\s+([a-zA-Z]+)\s+(.+)$',
            # "About 1.5 packages worth of..." 
            r'^(?:about|approx|approximately)?\s*([\d/\-\.]+)\s+([a-zA-Z]+)\s+(?:worth of\s+)?(.+)$',
            # Just number and ingredient: "2 eggs"
            r'^([\d/\-\.]+)\s+(.+)$'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                
                if len(groups) == 2:
                    # Check if this is the parentheses pattern: "item (amount)"
                    if '(' in text and ')' in text:
                        # Pattern 1: "Ground beef (1.8 lb / 800 g)"
                        item_str = groups[0].strip()
                        amount_str = groups[1].strip()
                    else:
                        # Pattern: "2 eggs" or "handful nuts"
                        first, second = groups
                        # Check if first looks like a number
                        if re.match(r'[\d/\-\.]+', first):
                            amount_str = first.strip()
                            item_str = second.strip()
                        else:
                            # It's unit+item like "handful nuts"
                            amount_str = first.strip()
                            item_str = second.strip()
                elif len(groups) == 3:
                    # Has amount, unit, and item: "2 cups flour"
                    amount, unit, item = groups
                    amount_str = f"{amount.strip()} {unit.strip()}"
                    item_str = item.strip()
                else:
                    continue
                
                if item_str and len(item_str) >= 2:
                    return RecipeIngredientSchema(
                        item=item_str,
                        amount=amount_str,
                        notes=None
                    )
        
        # Last resort - whole text is ingredient
        if len(text) >= 5:
            return RecipeIngredientSchema(
                item=text,
                amount="to taste",
                notes=None
            )
        
        return None
    
    def _extract_ingredients_improved(self, text: str, lines: List[str]) -> List[RecipeIngredientSchema]:
        """Improved ingredient extraction for Reddit-style posts."""
        ingredients = []
        
        # Look for ingredient section markers
        ingredient_section_start = -1
        ingredient_section_end = len(lines)
        
        for i, line in enumerate(lines):
            # Remove markdown bold markers for detection
            clean_line = line.replace('**', '').replace('*', '').strip().lower()
            
            # Check for ingredient section start
            if any(marker in clean_line for marker in ['ingredient', 'what you need', 'you will need', 'shopping list']):
                print(f"DEBUG: Found ingredient section at line {i}: {line[:50]}")
                ingredient_section_start = i
            # Check for section end (instructions start)
            elif ingredient_section_start > -1 and any(marker in clean_line for marker in ['instruction', 'direction', 'method', 'step', 'preparation']):
                print(f"DEBUG: Ingredient section ends at line {i}: {line[:50]}")
                ingredient_section_end = i
                break
        
        print(f"DEBUG: Ingredient section: lines {ingredient_section_start} to {ingredient_section_end}")
        
        # Extract ingredients from the identified section
        if ingredient_section_start > -1:
            for i in range(ingredient_section_start + 1, ingredient_section_end):
                if i >= len(lines):
                    break
                line = lines[i].strip()
                
                # Skip empty lines and section headers
                if not line or len(line) < 3:
                    continue
                
                # Skip lines that are just markdown markers or headers
                if line.startswith('**') and line.endswith('**'):
                    continue
                
                # Remove markdown bold markers
                line = line.replace('**', '')
                
                # Remove bullet points and list markers (including markdown *)
                line = re.sub(r'^[\*\-•]+\s*', '', line)
                line = re.sub(r'^\d+[\.)]\s*', '', line)
                
                # Skip if now empty
                if not line or len(line) < 3:
                    continue
                
                # Try to parse as ingredient
                ingredient = self._parse_ingredient_line_improved(line)
                if ingredient:
                    ingredients.append(ingredient)
        
        # If no ingredients found in section, try to find them in the whole text
        if not ingredients:
            # Look for lines that match ingredient patterns
            for line in lines:
                if self._is_ingredient_line(line):
                    line = re.sub(r'^[\*\-•]\s*', '', line)
                    line = re.sub(r'^\d+\.\s*', '', line)
                    ingredient = self._parse_ingredient_line_improved(line)
                    if ingredient:
                        ingredients.append(ingredient)
        
        return ingredients
    
    def _parse_ingredient_line_improved(self, line: str) -> Optional[RecipeIngredientSchema]:
        """Improved parsing of ingredient lines."""
        if not line or len(line) < 2:
            return None
        
        # VALIDATION: Only reject if EXTREMELY long (entire recipe text)
        if len(line) > 200:
            return None
        
        # VALIDATION: Reject lines with many sentences (paragraph text)
        if line.count('.') >= 3 or line.count('!') >= 3:
            return None
        
        # VALIDATION: Reject obvious paragraphs
        if '\n\n' in line:
            return None
        
        # Pattern to extract: amount + unit + ingredient
        # Examples: "2 cups flour", "1/2 tsp salt", "3-4 large eggs"
        pattern = r'^([\d\s\/\-\.]+)?\s*([a-zA-Z]+)?\s+(.+)$'
        match = re.match(pattern, line)
        
        if match:
            amount_str, unit_str, item_str = match.groups()
            
            # Clean up the parts
            amount = (amount_str or '').strip()
            unit = (unit_str or '').strip()
            item = item_str.strip()
            
            # VALIDATION: Item name shouldn't be EXTREMELY long
            if len(item) > 150:
                return None
            
            # If we have a unit that looks like it's part of the ingredient, merge them
            common_units = ['cup', 'cups', 'tbsp', 'tsp', 'tablespoon', 'teaspoon', 'oz', 'lb', 'g', 'kg', 'ml', 'l', 'pound', 'ounce']
            if unit and unit.lower() not in common_units and not amount:
                item = f"{unit} {item}"
                unit = ''
            
            # Combine amount and unit
            if amount and unit:
                amount_unit = f"{amount} {unit}"
            elif amount:
                amount_unit = amount
            elif unit:
                amount_unit = unit
            else:
                amount_unit = "to taste"
            
            return RecipeIngredientSchema(
                item=item,
                amount=amount_unit,
                notes=None
            )
        
        # Fallback validation: only use if line looks reasonable
        if len(line) <= 120 and line.count('\n') == 0:
            return RecipeIngredientSchema(
                item=line,
                amount="to taste",
                notes=None
            )
        
        # Reject if doesn't meet criteria
        return None
    
    def _extract_instructions_improved(self, text: str, lines: List[str]) -> List[RecipeInstructionSchema]:
        """Improved instruction extraction for Reddit-style posts."""
        instructions = []
        
        # Look for instruction section markers
        instruction_section_start = -1
        
        for i, line in enumerate(lines):
            # Remove markdown bold markers for detection
            clean_line = line.replace('**', '').replace('*', '').strip().lower()
            
            # Check for instruction section start
            if any(marker in clean_line for marker in ['instruction', 'direction', 'method', 'step', 'preparation', 'how to']):
                instruction_section_start = i
                break
        
        # Extract instructions from the identified section
        if instruction_section_start > -1:
            step_num = 1
            for i in range(instruction_section_start + 1, len(lines)):
                line = lines[i].strip()
                
                # Skip empty lines and very short lines
                if not line or len(line) < 10:
                    continue
                
                # Skip lines that are just markdown markers or headers
                if line.startswith('**') and line.endswith('**'):
                    continue
                
                # Remove markdown bold markers
                line = line.replace('**', '')
                
                # Skip if now too short
                if len(line) < 10:
                    continue
                
                # Check if this looks like an instruction
                if self._looks_like_instruction(line):
                    instruction = self._parse_instruction_line_improved(line, step_num)
                    if instruction:
                        instructions.append(instruction)
                        step_num += 1
        
        # If no instructions found in section, try to find numbered steps anywhere
        if not instructions:
            step_num = 1
            for line in lines:
                # Look for numbered steps
                if re.match(r'^\d+[\.)]\s+', line):
                    instruction = self._parse_instruction_line_improved(line, step_num)
                    if instruction:
                        instructions.append(instruction)
                        step_num += 1
        
        return instructions
    
    def _looks_like_instruction(self, line: str) -> bool:
        """Check if a line looks like an instruction."""
        # Check for instruction verbs
        instruction_verbs = ['mix', 'stir', 'cook', 'bake', 'fry', 'boil', 'heat', 'add', 'remove', 'serve', 
                            'combine', 'whisk', 'pour', 'place', 'put', 'cut', 'chop', 'dice', 'slice',
                            'preheat', 'prepare', 'spread', 'fold', 'blend', 'process']
        
        lower_line = line.lower()
        has_verb = any(verb in lower_line for verb in instruction_verbs)
        
        # Check if it's numbered or has instruction markers
        is_numbered = bool(re.match(r'^\d+[\.)]\s+', line))
        
        # Long enough and has instruction characteristics
        return (has_verb or is_numbered) and len(line) > 15
    
    def _parse_instruction_line_improved(self, line: str, step_num: int) -> Optional[RecipeInstructionSchema]:
        """Improved parsing of instruction lines."""
        # Remove bullet points and numbering (including markdown * bullets)
        clean_line = re.sub(r'^[\*\-•]+\s*', '', line)
        clean_line = re.sub(r'^\d+[\.)]\s*', '', clean_line)
        
        # Remove any remaining markdown bold markers
        clean_line = clean_line.replace('**', '')
        
        # Check if line has a title (usually bold or before a colon)
        title = f"Step {step_num}"
        description = clean_line
        
        # Look for colon-separated title
        if ':' in clean_line and clean_line.index(':') < 50:
            parts = clean_line.split(':', 1)
            potential_title = parts[0].strip()
            # Make sure title isn't too long
            if len(potential_title) < 50 and potential_title and not potential_title[0].islower():
                title = potential_title
                description = parts[1].strip()
        
        return RecipeInstructionSchema(
            step=step_num,
            title=title,
            description=description
        )
    
    def _extract_ingredients_lenient(self, text: str, lines: List[str]) -> List[RecipeIngredientSchema]:
        """Lenient ingredient extraction - tries harder to find ingredients."""
        ingredients = []
        
        # Look for ANY lines that might be ingredients
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # Remove markdown bold markers
            line = line.replace('**', '')
            
            # Remove bullets/numbers (including markdown * bullets)
            line = re.sub(r'^[\*\-•]+\s*', '', line)
            line = re.sub(r'^\d+[\.)]\s*', '', line)
            
            # Skip if it's obviously a header or instruction
            if line.lower().startswith(('ingredients:', 'instructions:', 'directions:', 'step', 'method')):
                continue
            
            # Look for measurement patterns - these are likely ingredients
            measurement_patterns = [
                r'\d+',  # Has numbers
                r'\bcup|tbsp|tsp|tablespoon|teaspoon|ounce|oz|pound|lb|gram|g|kg|ml|liter|l\b',  # Has units
            ]
            
            has_measurement = any(re.search(pattern, line, re.IGNORECASE) for pattern in measurement_patterns)
            
            # If it has measurements and isn't too long, it's probably an ingredient
            if has_measurement and len(line) < 120:
                ingredient = self._parse_ingredient_line_simple(line)
                if ingredient:
                    ingredients.append(ingredient)
        
        return ingredients[:20]  # Cap at 20 ingredients
    
    def _extract_instructions_lenient(self, text: str, lines: List[str]) -> List[RecipeInstructionSchema]:
        """Lenient instruction extraction - tries harder to find instructions."""
        instructions = []
        
        # Look for numbered lines or lines with cooking verbs
        cooking_verbs = ['mix', 'stir', 'cook', 'bake', 'fry', 'boil', 'heat', 'add', 'remove', 
                        'combine', 'whisk', 'prepare', 'place', 'serve', 'preheat', 'pour']
        
        step_num = 1
        for line in lines:
            line = line.strip()
            if not line or len(line) < 15:  # Instructions should be substantial
                continue
            
            # Remove markdown bold markers
            line = line.replace('**', '')
            
            # Skip headers
            if line.lower().startswith(('ingredients:', 'instructions:', 'directions:')):
                continue
            
            # Check if it's a numbered instruction
            is_numbered = bool(re.match(r'^\d+[\.)]\s+', line))
            
            # Check if it has cooking verbs
            has_verb = any(verb in line.lower() for verb in cooking_verbs)
            
            # If it looks like an instruction and isn't too long
            if (is_numbered or has_verb) and len(line) < 300:
                # Clean it up - remove numbering and bullets
                clean_line = re.sub(r'^\d+[\.)]\s*', '', line)
                clean_line = re.sub(r'^[\*\-•]+\s*', '', clean_line)
                
                instructions.append(RecipeInstructionSchema(
                    step=step_num,
                    title=f"Step {step_num}",
                    description=clean_line
                ))
                step_num += 1
                
                if step_num > 20:  # Cap at 20 instructions
                    break
        
        return instructions
    
    def _parse_ingredient_line_simple(self, line: str) -> Optional[RecipeIngredientSchema]:
        """Simple ingredient parsing for lenient mode."""
        if not line or len(line) > 120:
            return None
        
        # Try to split into amount and item
        # Look for pattern like "2 cups flour" or "1/2 tsp salt"
        pattern = r'^([\d\s\/\-\.]+(?:\s*[a-zA-Z]+)?)\s+(.+)$'
        match = re.match(pattern, line)
        
        if match:
            amount_str = match.group(1).strip()
            item_str = match.group(2).strip()
            
            return RecipeIngredientSchema(
                item=item_str,
                amount=amount_str,
                notes=None
            )
        
        # Fallback: whole line is ingredient
        return RecipeIngredientSchema(
            item=line,
            amount="to taste",
            notes=None
        )
