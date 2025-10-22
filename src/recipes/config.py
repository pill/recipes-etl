"""Configuration management for the recipes application."""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DatabaseConfig:
    """Database configuration."""
    
    def __init__(self):
        self.user = os.getenv('DB_USER', 'postgres')
        self.host = os.getenv('DB_HOST', 'localhost')
        self.database = os.getenv('DB_NAME', 'recipes')
        self.password = os.getenv('DB_PASSWORD', 'postgres')
        self.port = int(os.getenv('DB_PORT', '5432'))


class AIConfig:
    """AI service configuration."""
    
    def __init__(self):
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
    
    def is_configured(self) -> bool:
        """Check if AI is properly configured."""
        return bool(self.anthropic_api_key and len(self.anthropic_api_key.strip()) > 0)


class TemporalConfig:
    """Temporal workflow configuration."""
    
    def __init__(self):
        self.host = os.getenv('TEMPORAL_HOST', 'localhost')
        self.port = int(os.getenv('TEMPORAL_PORT', '7233'))


class ElasticsearchConfig:
    """Elasticsearch configuration."""
    
    def __init__(self):
        self.host = os.getenv('ELASTICSEARCH_HOST', 'localhost')
        self.port = int(os.getenv('ELASTICSEARCH_PORT', '9200'))
        self.username = os.getenv('ELASTICSEARCH_USERNAME')
        self.password = os.getenv('ELASTICSEARCH_PASSWORD')
    
    @property
    def url(self) -> str:
        """Get Elasticsearch URL."""
        return f"http://{self.host}:{self.port}"


class AppConfig:
    """Application configuration."""
    
    def __init__(self):
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.debug = os.getenv('DEBUG', 'false').lower() == 'true'


# Global configuration instances
db_config = DatabaseConfig()
ai_config = AIConfig()
temporal_config = TemporalConfig()
elasticsearch_config = ElasticsearchConfig()
app_config = AppConfig()
