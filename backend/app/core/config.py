from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Database
    database_url: str = "postgresql://verse_user:verse_password@db:5432/verse_db"

    # AI Provider
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # Bible Provider
    bible_client_type: str = "sqlite"  # Options: "sqlite", "api"

    # AI Token Limits
    max_tokens_insights: int = Field(default=2000, ge=500, le=16000)
    max_tokens_definition: int = Field(default=1000, ge=500, le=16000)
    max_tokens_chat: int = Field(default=3000, ge=500, le=16000)

    # Application
    environment: str = "development"
    debug: bool = True
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    @property
    def cookie_secure(self) -> bool:
        """Cookies are secure in production, insecure in development."""
        return self.environment == "production"

    model_config = {"env_file": ".env", "case_sensitive": False}


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
