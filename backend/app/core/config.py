from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_url: str = "postgresql://verse_user:verse_password@db:5432/verse_db"
    
    # AI Provider
    anthropic_api_key: str = ""
    
    # Application
    environment: str = "development"
    debug: bool = True
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # Cookie Settings
    cookie_secure: bool = False  # Set to True in production with HTTPS
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
