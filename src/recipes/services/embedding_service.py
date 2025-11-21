"""Embedding service for generating vector embeddings from recipe data."""

from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

from ..models.recipe import Recipe


class EmbeddingService:
    """Service for generating vector embeddings from recipes."""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the embedding service.
        
        Args:
            model_name: Name of the sentence transformer model to use.
                      Default is 'all-MiniLM-L6-v2' (384 dimensions, fast and efficient).
        """
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
    
    def _load_model(self):
        """Lazy load the model to avoid loading on import."""
        if self.model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(self.model_name)
            except ImportError:
                raise ImportError(
                    "sentence-transformers is required for embedding generation. "
                    "Install it with: pip install sentence-transformers"
                )
        return self.model
    
    def build_embedding_text(self, recipe: Recipe) -> str:
        """
        Build text representation from recipe title and ingredients for embedding.
        
        Args:
            recipe: Recipe object with title and ingredients
            
        Returns:
            Combined text string suitable for embedding
        """
        # Start with title
        text_parts = [recipe.title]
        
        # Add ingredient names
        if recipe.ingredients:
            ingredient_names = []
            for ingredient in recipe.ingredients:
                if ingredient.ingredient and ingredient.ingredient.name:
                    ingredient_names.append(ingredient.ingredient.name)
            
            if ingredient_names:
                # Join ingredients with commas and add to text
                text_parts.append(', '.join(ingredient_names))
        
        return '. '.join(text_parts)
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate vector embedding from text.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            List of floats representing the embedding vector
        """
        model = self._load_model()
        embedding = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
        return embedding.tolist()
    
    def generate_recipe_embedding(self, recipe: Recipe) -> List[float]:
        """
        Generate vector embedding for a recipe based on title and ingredients.
        
        Args:
            recipe: Recipe object
            
        Returns:
            List of floats representing the embedding vector
        """
        text = self.build_embedding_text(recipe)
        return self.generate_embedding(text)
    
    def generate_batch_embeddings(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.
        
        Args:
            texts: List of texts to generate embeddings for
            batch_size: Batch size for processing
            
        Returns:
            List of embedding vectors
        """
        model = self._load_model()
        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        return embeddings.tolist()


# Singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get the embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service

