"""Application settings loaded from environment variables.

This module defines the Settings class using Pydantic Settings to load
configuration from environment variables with validation.
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        app_name: Application name
        app_version: Application version
        debug: Debug mode flag
        config_dir: Directory containing configuration YAML files
        chains_config_file: Path to chains.yaml configuration file
        providers_config_file: Path to providers.yaml configuration file
        database_url: PostgreSQL database connection URL
        secret_key: Secret key for JWT token generation
        algorithm: Algorithm for JWT encoding
        access_token_expire_minutes: JWT token expiration time
        api_v1_prefix: API version 1 URL prefix
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application settings
    app_name: str = Field(default="Aurora", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")

    # Configuration file paths
    config_dir: Path = Field(default=Path("config"), description="Config directory")
    chains_config_file: str = Field(
        default="chains.yaml", description="Chains configuration filename"
    )
    providers_config_file: str = Field(
        default="providers.yaml", description="Providers configuration filename"
    )

    # Database settings
    database_url: str = Field(
        default="postgresql+asyncpg://aurora:aurora@localhost:5432/aurora",
        description="Database connection URL",
    )

    # Security settings
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT",
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30, ge=1, description="Token expiration minutes"
    )

    # API settings
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 URL prefix")

    @property
    def chains_config_path(self) -> Path:
        """Get full path to chains configuration file."""
        return self.config_dir / self.chains_config_file

    @property
    def providers_config_path(self) -> Path:
        """Get full path to providers configuration file."""
        return self.config_dir / self.providers_config_file


# Global settings instance
settings = Settings()
