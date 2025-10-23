"""AI service for recipe data extraction."""

import json
from typing import Dict, Any, Optional, List, Literal
from anthropic import AsyncAnthropic
from pydantic import BaseModel

from ..config import ai_config
from ..models.schemas import RecipeSchema


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

Focus on:
- Accurate ingredient names and amounts
- Clear, step-by-step instructions with descriptive titles
- Proper timing information (prep time, cook time, chill time, etc.)
- Equipment requirements (pan sizes, etc.)
- Recipe metadata (difficulty, cuisine type, meal type, dietary tags)

For difficulty:
- 'easy' for simple recipes with few steps
- 'medium' for recipes requiring some skill or multiple steps
- 'hard' for complex recipes with advanced techniques

For cuisine:
- Identify the cuisine type (e.g., 'Italian', 'Mexican', 'Chinese', 'Thai', 'Indian', 'French', 'American', etc.)
- Use the most specific cuisine type when possible

For mealType:
- Choose from: 'breakfast', 'lunch', 'dinner', 'snack', 'dessert'
- Base on when the dish would typically be served

For dietaryTags:
- Include relevant tags: 'vegetarian', 'vegan', 'gluten-free', 'dairy-free', 'keto', 'paleo', etc.
- Only include tags that clearly apply based on ingredients

Extract all available information and structure it according to the provided schema."""
        
        return await self.extract_structured_data(
            text=reddit_post_text,
            schema=RecipeSchema,
            options={
                **options,
                'systemPrompt': system_prompt
            }
        )
    
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
