# TODO: Add JWT_SECRET_KEY for JWT token validation, as specified in the requirements.md.
# This is a critical security requirement for authenticating requests from the Layer55 API backend.
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
    port: int = 8004  # Default port (avoiding conflict with Smart Insights on 8002)
    mcp_server_port: Optional[int] = None  # Environment variable override

    # Pipedrive Configuration
    pipedrive_api_base_url: str = "https://api.pipedrive.com"
    # NOTE: API tokens are NEVER stored in settings/env variables
    # They are extracted from request headers (X-API-Token) via the @require_api_key decorator
    # and injected as function parameters. See auth/api_key_auth.py

    # Layer55 Configuration
    layer55_api_url: str = "https://api.layer55.eu"
    pipedrive_server_id: str = "pipedrive"

    # JWT Configuration - Should be set via environment variable in production
    jwt_secret_key: str = "dev-fallback-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60

    # API Key Configuration - Should be set via environment variable in production
    valid_api_keys: list[
        str
    ] = []  # Empty list means accept any non-empty key in development

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

    # Export Configuration
    exports_directory: str = "./exports"
    max_export_age_hours: int = 24  # Clean up exports older than 24 hours
    enable_export_cleanup: bool = True

    # Langfuse Monitoring Configuration
    langfuse_secret_key: Optional[str] = None
    langfuse_public_key: Optional[str] = None
    langfuse_base_url: Optional[str] = None
    langfuse_enabled: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="",  # Allow direct environment variable mapping
    )


# Global settings instance
try:
    settings = Settings()

    # Override port if MCP_SERVER_PORT is set
    if settings.mcp_server_port:
        settings.port = settings.mcp_server_port

    if not settings.jwt_secret_key:
        import warnings

        warnings.warn(
            "JWT_SECRET_KEY not set - authentication will fail. Set this environment variable in production."
        )
except Exception as e:
    import warnings

    warnings.warn(f"Configuration error: {e}")
    # Fallback settings for development
    settings = Settings(jwt_secret_key="dev-fallback-key")
