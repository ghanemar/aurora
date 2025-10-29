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
        database_pool_size: Database connection pool size
        database_max_overflow: Database max overflow connections
        database_echo: Echo SQL queries to console
        redis_url: Redis connection URL
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
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

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
        default="postgresql+asyncpg://aurora:aurora_dev@localhost:5433/aurora",
        description="Database connection URL",
    )
    database_pool_size: int = Field(
        default=10, ge=1, le=100, description="Database connection pool size"
    )
    database_max_overflow: int = Field(
        default=20, ge=0, le=100, description="Database max overflow connections"
    )
    database_echo: bool = Field(default=False, description="Echo SQL queries to console")

    # Redis settings
    redis_url: str = Field(default="redis://localhost:6380/0", description="Redis connection URL")

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

    # Security settings - Request limits
    max_request_size: int = Field(
        default=10_485_760,  # 10MB
        ge=1024,  # Minimum 1KB
        le=104_857_600,  # Maximum 100MB
        description="Maximum request size in bytes (10MB default)",
    )

    # Security settings - Rate limiting
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_requests: int = Field(
        default=100, ge=1, le=10000, description="Maximum requests per window"
    )
    rate_limit_window_seconds: int = Field(
        default=60, ge=1, le=3600, description="Rate limit time window in seconds"
    )

    # Security settings - CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8001"],
        description="Allowed CORS origins",
    )
    cors_allow_credentials: bool = Field(default=True, description="Allow CORS credentials")

    # Security settings - API keys (for service-to-service auth)
    api_keys_enabled: bool = Field(default=False, description="Enable API key authentication")
    valid_api_keys: list[str] = Field(
        default=[], description="Valid API keys for service authentication"
    )

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
