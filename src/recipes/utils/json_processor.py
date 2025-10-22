"""JSON processing utilities."""

import json
import os
from typing import Dict, Any, Optional
import aiofiles
from ..models.schemas import RecipeSchema


class JSONProcessor:
    """JSON processor for recipe data."""
    
    async def save_recipe_json(self, recipe_data: RecipeSchema, entry_number: int, subdirectory: Optional[str] = None) -> str:
        """Save recipe data to a JSON file, optionally in a subdirectory."""
        # Create output directory if it doesn't exist
        if subdirectory:
            output_dir = os.path.join("data/stage", subdirectory)
        else:
            output_dir = "data/stage"
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate output filename
        output_filename = f"entry_{entry_number}.json"
        output_path = os.path.join(output_dir, output_filename)
        
        # Convert to dict and save
        recipe_dict = recipe_data.model_dump()
        
        async with aiofiles.open(output_path, 'w', encoding='utf-8') as file:
            await file.write(json.dumps(recipe_dict, indent=2, ensure_ascii=False))
        
        return output_path
    
    async def load_recipe_json(self, json_file_path: str) -> Dict[str, Any]:
        """Load recipe data from a JSON file."""
        if not os.path.exists(json_file_path):
            raise FileNotFoundError(f"JSON file not found: {json_file_path}")
        
        try:
            async with aiofiles.open(json_file_path, 'r', encoding='utf-8') as file:
                content = await file.read()
                return json.loads(content)
        except Exception as e:
            raise Exception(f"Error loading JSON file: {str(e)}")
    
    async def validate_recipe_json(self, json_file_path: str) -> bool:
        """Validate that a JSON file contains valid recipe data."""
        try:
            recipe_data = await self.load_recipe_json(json_file_path)
            # Validate against schema
            RecipeSchema.model_validate(recipe_data)
            return True
        except Exception:
            return False
    
    async def get_all_json_files(self, directory: str) -> list[str]:
        """Get all JSON files in a directory."""
        if not os.path.exists(directory):
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        json_files = []
        for filename in os.listdir(directory):
            if filename.endswith('.json'):
                json_files.append(os.path.join(directory, filename))
        
        return sorted(json_files)
