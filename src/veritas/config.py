"""Configuration settings for Veritas."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False

    # CDP API Keys (required for agent functionality)
    CDP_API_KEY_ID: str = ""
    CDP_API_KEY_SECRET: str = ""

    # MiniMax API Key for LLM
    MINIMAX_API_KEY: str = ""

    # Network Configuration
    NETWORK: str = "base-sepolia"
    ENABLE_MAINNET: bool = False

    # Database Configuration
    DATABASE_URL: str = "sqlite+aiosqlite:///./veritas.db"

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"

    # EAS Configuration
    EAS_CONTRACT_ADDRESS: str = "0xC2679fBD37d54388Ce493F1DB75320D236e1815e"
    SCHEMA_UID: str = ""

    # Security
    SECRET_KEY: str = "change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
