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
