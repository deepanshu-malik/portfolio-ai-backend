"""
Application configuration using Pydantic Settings.
Environment variables are loaded from .env file or system environment.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Portfolio AI Backend"
    app_version: str = "1.0.0"
    app_env: str = "development"
    debug: bool = False

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    # CORS
    allowed_origins: str = "http://localhost:3000,https://deepanshu-malik.github.io"

    # ChromaDB
    chroma_persist_directory: str = "./chromadb"
    chroma_collection_name: str = "portfolio"

    # Rate Limiting
    rate_limit_requests: int = 10
    rate_limit_window: int = 60

    # Memory Optimization (for Koyeb free tier - 512MB RAM)
    max_concurrent_requests: int = 3  # Limit concurrent processing
    request_timeout: int = 30  # Request timeout in seconds
    max_history_length: int = 5  # Conversation history length (reduced from 10)

    # Response Caching
    cache_ttl: int = 1800  # Cache TTL in seconds (30 minutes)
    cache_max_size: int = 100  # Maximum cached responses
    cache_enabled: bool = True  # Enable/disable caching

    # Token Usage Optimization (reduced for free tier cost savings)
    max_tokens_context: int = 2000  # Context tokens (reduced from 3000)
    max_tokens_history: int = 500   # History tokens (reduced from 1000)
    max_tokens_response: int = 600  # Response tokens (reduced from 800)
    max_retrieval_docs: int = 3     # Retrieved documents (reduced from 5)

    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env.lower() == "production"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
