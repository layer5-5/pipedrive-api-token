"""Configuration management for Pipedrive MCP Server."""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Server Configuration
    app_name: str = "Pipedrive MCP Server"
    app_version: str = "2.0.0"
    environment: str = "development"
    debug: bool = False

    # Server Host/Port
    host: str = "0.0.0.0"
    port: int = 8002

    # Pipedrive Configuration
    pipedrive_api_base_url: str = "https://api.pipedrive.com"

    # Layer55 Configuration
    layer55_api_url: str = "https://api.layer55.eu"
    pipedrive_server_id: str = "pipedrive"

    # Redis Configuration - TODO: Implement caching layer
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None

    # Cache TTLs (seconds) - TODO: Implement caching layer
    cache_ttl_token: int = 3600  # 1 hour
    cache_ttl_metadata: int = 86400  # 24 hours
    cache_ttl_deal: int = 300  # 5 minutes
    cache_ttl_search: int = 60  # 1 minute

    # Rate Limiting
    rate_limit_global: int = 100  # requests per minute
    rate_limit_write: int = 20  # requests per minute
    rate_limit_read: int = 60  # requests per minute
    rate_limit_search: int = 30  # requests per minute

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # CORS
    cors_origins: list[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    # Performance
    connection_pool_size: int = 10
    request_timeout: int = 30

    # Data Retrieval Logging
    enable_data_retrieval_logging: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Global settings instance
settings = Settings()
