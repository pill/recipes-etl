"""AI service for recipe data extraction."""

import json
import re
from typing import Dict, Any, Optional, List, Literal
from anthropic import AsyncAnthropic
from pydantic import BaseModel

from ..config import ai_config
from ..models.schemas import RecipeSchema, RecipeIngredientSchema


class AIMessage(BaseModel):
    """AI message model."""
    
    role: Literal['user', 'assistant']
    content: str


class AIResponse(BaseModel):
    """AI response model."""
    
    content: str
    usage: Optional[Dict[str, int]] = None


class AIService:
    """AI service for recipe data extraction using Anthropic Claude."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the AI service."""
        self.api_key = api_key or ai_config.anthropic_api_key
        if not self.api_key:
            raise ValueError('ANTHROPIC_API_KEY environment variable is not set. If using local parsing, this is optional.')
        
        # More aggressive trimming to handle any whitespace issues
        clean_key = self.api_key.replace(' ', '').strip()
        if not clean_key or len(clean_key) < 10:
            raise ValueError('ANTHROPIC_API_KEY appears to be invalid or empty')
        
        self.client = AsyncAnthropic(api_key=clean_key)
    
    async def send_message(
        self,
        message: str,
        options: Optional[Dict[str, Any]] = None
    ) -> AIResponse:
        """Send a single message to Claude and get a response."""
        options = options or {}
        model = options.get('model', 'claude-3-haiku-20240307')
        max_tokens = options.get('maxTokens', 1000)
        system_prompt = options.get('systemPrompt')
        
        messages = [{"role": "user", "content": message}]
        
        request_body = {
            'model': model,
            'max_tokens': max_tokens,
            'messages': messages
        }
        
        if system_prompt:
            request_body['system'] = system_prompt
        
        try:
            response = await self.client.messages.create(**request_body)
            
            return AIResponse(
                content=response.content[0].text,
                usage={
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.usage.output_tokens
                } if response.usage else None
            )
        except Exception as e:
            print(f'AI Service Error: {e}')
            raise Exception(f'Failed to get AI response: {str(e)}')
    
    async def send_conversation(
        self,
        messages: List[AIMessage],
        options: Optional[Dict[str, Any]] = None
    ) -> AIResponse:
        """Send a conversation (multiple messages) to Claude."""
        options = options or {}
        model = options.get('model', 'claude-3-haiku-20240307')
        max_tokens = options.get('maxTokens', 1000)
        system_prompt = options.get('systemPrompt')
        
        message_dicts = [{"role": msg.role, "content": msg.content} for msg in messages]
        
        request_body = {
            'model': model,
            'max_tokens': max_tokens,
            'messages': message_dicts
        }
        
        if system_prompt:
            request_body['system'] = system_prompt
        
        try:
            response = await self.client.messages.create(**request_body)
            
            return AIResponse(
                content=response.content[0].text,
                usage={
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.usage.output_tokens
                } if response.usage else None
            )
        except Exception as e:
            print(f'AI Service Error: {e}')
            raise Exception(f'Failed to get AI response: {str(e)}')
    
    async def extract_data(
        self,
        text: str,
        schema: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Extract structured data from text using AI (legacy method)."""
        options = options or {}
        prompt = f"""Please extract the following information from the text and return it as valid JSON matching this schema: {schema}

Text to analyze:
{text}

Return only the JSON object, no additional text."""
        
        response = await self.send_message(prompt, options)
        
        try:
            return json.loads(response.content)
        except json.JSONDecodeError as e:
            raise Exception(f'Failed to parse AI response as JSON: {str(e)}')
    
    async def extract_structured_data(
        self,
        text: str,
        schema: BaseModel,
        options: Optional[Dict[str, Any]] = None
    ) -> BaseModel:
        """Extract structured data from text using generateObject (recommended)."""
        options = options or {}
        model = options.get('model', 'claude-3-haiku-20240307')
        max_tokens = options.get('maxTokens', 1000)
        system_prompt = options.get('systemPrompt')
        
        prompt = f"Extract the following information from the text:\n\n{text}"
        
        system = system_prompt or "You are an expert at extracting structured data from text. Return only the requested information in the exact format specified."
        
        response = await self.send_message(prompt, {
            'model': model,
            'maxTokens': max_tokens,
            'systemPrompt': system
        })
        
        try:
            data = json.loads(response.content)
            return schema.model_validate(data)
        except (json.JSONDecodeError, ValueError) as e:
            raise Exception(f'Failed to extract structured data: {str(e)}')
    
    async def extract_recipe_data(
        self,
        reddit_post_text: str,
        options: Optional[Dict[str, Any]] = None
    ) -> RecipeSchema:
        """Extract recipe data from Reddit post text using the standardized recipe schema."""
        options = options or {}
        
        system_prompt = """You are an expert at extracting detailed recipe information from Reddit posts. 

CRITICAL INGREDIENT PARSING RULES:
- The 'item' field should ONLY contain the ingredient name (e.g., "beef stock", "pancetta", "shallots")
- The 'amount' field should ONLY contain the quantity and measurement (e.g., "1 1/2 cups", "4 oz", "3 cloves")
- NEVER put amounts like "1/2 cups beef stock" or "4oz pancetta" in the item field
- NEVER include cooking instructions in the ingredients list
- If you see text that starts with action verbs (Cook, Deglaze, Add, Fix, etc.), it's an INSTRUCTION, not an ingredient
- Stop parsing ingredients when you encounter section headers like "**Preparation**", "**Instructions**", or "**Method**"
- Do not include markdown formatting artifacts (**, *, #) in any field

Focus on:
- Accurate ingredient names and amounts with proper field separation
- Clear, step-by-step instructions with descriptive titles
- Proper timing information (prep time, cook time, chill time, etc.)
- Equipment requirements (pan sizes, etc.)
- Recipe metadata (difficulty, cuisine type, meal type, dietary tags)

For difficulty:
- 'easy' for simple recipes with few steps
- 'medium' for recipes requiring some skill or multiple steps
- 'hard' for complex recipes with advanced techniques

For cuisine:
- Identify the cuisine type (e.g., 'Italian', 'Mexican', 'Chinese', 'Thai', 'Indian', 'French', 'Korean', 'American', 'German', etc.)
- If the cuisine name appears in the title (e.g., "Korean Beef Bowl"), use that cuisine type
- Use the most specific cuisine type when possible
- Consider ingredients as secondary signals (e.g., gochujang suggests Korean, fish sauce suggests Thai, bratwurst suggests German)

For mealType:
- Choose from: 'breakfast', 'lunch', 'dinner', 'snack', 'dessert'
- Base on when the dish would typically be served
- Main courses with meat, pasta, or substantial proteins are usually 'dinner'
- Sweet baked goods, candies, and treats are 'dessert'
- Light foods like sandwiches, salads, wraps are 'lunch'
- Morning foods like pancakes, eggs, breakfast burritos are 'breakfast'

For dietaryTags:
- Include relevant tags: 'vegetarian', 'vegan', 'gluten-free', 'dairy-free', 'keto', 'paleo', etc.
- Only include tags that clearly apply based on ingredients
- If meat is present, do NOT tag as vegetarian or vegan

Extract all available information and structure it according to the provided schema."""
        
        recipe = await self.extract_structured_data(
            text=reddit_post_text,
            schema=RecipeSchema,
            options={
                **options,
                'systemPrompt': system_prompt
            }
        )
        
        # Post-process and validate the recipe
        return self._validate_and_cleanup_recipe(recipe)
    
    def _validate_and_cleanup_recipe(self, recipe: RecipeSchema) -> RecipeSchema:
        """Validate and clean up recipe data to fix common parsing issues."""
        
        # Clean up ingredients
        cleaned_ingredients = []
        instruction_verbs = ['cook', 'add', 'mix', 'stir', 'deglaze', 'fix', 'serve', 'place', 
                            'heat', 'pour', 'bring', 'reduce', 'simmer', 'bake', 'remove',
                            'set', 'cover', 'wait', 'let', 'transfer', 'combine']
        
        for ing in recipe.ingredients:
            item = ing.item.strip()
            amount = ing.amount.strip() if ing.amount else ""
            
            # Skip if item looks like an instruction (starts with action verb)
            first_word = item.split()[0].lower() if item.split() else ""
            if first_word in instruction_verbs:
                continue
            
            # Skip if item contains section headers or markdown
            if any(header in item.lower() for header in ['**preparation', '**instructions', '**method', '**steps']):
                continue
            
            # Check if amount and item are swapped (amount contains ingredient name)
            # Pattern: "1/2 cups beef stock" or "4oz pancetta" or "1/3rd cup cream" in item field
            if re.match(r'^\d+', item) or item.startswith('around'):
                # Item field starts with a number - likely swapped
                # Try to parse it (handle fractions with "rd", "st", "nd", "th" suffixes)
                match = re.match(r'^(\d+(?:/\d+)?(?:st|nd|rd|th)?\s*(?:cups?|tbsp?|tsp?|oz|g|kg|ml|l|cloves?|pieces?)?)\s+(.+)$', item, re.IGNORECASE)
                if match:
                    # Swap them
                    amount = match.group(1).strip()
                    item = match.group(2).strip()
            
            # Clean up markdown and formatting
            item = re.sub(r'\*+', '', item)
            item = re.sub(r'\n+', ' ', item)
            item = ' '.join(item.split())
            
            if len(item) > 2:  # Only keep valid ingredients
                cleaned_ingredients.append(RecipeIngredientSchema(
                    item=item,
                    amount=amount or "to taste",
                    notes=ing.notes
                ))
        
        recipe.ingredients = cleaned_ingredients
        
        # Validate meal type - common mistakes
        title_lower = recipe.title.lower()
        
        # Check for obvious main course dishes marked as dessert
        main_course_indicators = ['brat', 'sausage', 'chicken', 'beef', 'pork', 'fish', 
                                  'pasta', 'steak', 'chops', 'roast', 'burger', 'gravy']
        dessert_indicators = ['cake', 'cookie', 'brownie', 'pie', 'ice cream', 'chocolate',
                             'frosting', 'icing', 'candy', 'fudge', 'tart', 'pudding']
        
        if recipe.mealType == 'dessert':
            # Check if this is actually a main course
            has_main_course = any(indicator in title_lower for indicator in main_course_indicators)
            has_dessert = any(indicator in title_lower for indicator in dessert_indicators)
            
            if has_main_course and not has_dessert:
                recipe.mealType = 'dinner'
        
        return recipe
    
    async def summarize(
        self,
        text: str,
        max_length: int = 200,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """Summarize text content."""
        prompt = f"Please summarize the following text in approximately {max_length} characters or less:\n\n{text}"
        
        response = await self.send_message(prompt, options)
        return response.content
    
    async def translate(
        self,
        text: str,
        target_language: str,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """Translate text to another language."""
        prompt = f"Please translate the following text to {target_language}:\n\n{text}"
        
        response = await self.send_message(prompt, options)
        return response.content
    
    def is_configured(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)


# Singleton instance
_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """Get the AI service instance."""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service
