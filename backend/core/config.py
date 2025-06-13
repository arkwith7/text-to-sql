"""
Configuration management for Text-to-SQL AI Agent
Handles environment variables and application settings
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional, List
import os


class Settings(BaseSettings):
    """Application settings with validation and type checking"""
    
    # Model configuration for Pydantic V2
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra='ignore'
    )
    
    # Azure OpenAI Configuration
    azure_openai_endpoint: str = Field(..., description="Azure OpenAI service endpoint", alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: str = Field(..., description="Azure OpenAI API key", alias="AZURE_OPENAI_API_KEY")
    azure_openai_api_version: str = Field(
        default="2024-02-15-preview", 
        description="Azure OpenAI API version",
        alias="AZURE_OPENAI_API_VERSION"
    )
    azure_openai_deployment_name: str = Field(
        default="gpt-4o-mini", 
        description="Azure OpenAI model deployment name",
        alias="AZURE_OPENAI_DEPLOYMENT_NAME"
    )
    
    # Database Configuration
    database_url: str = Field(
        default="postgresql://postgres:password@localhost:5432/northwind",
        description="Main database URL (Northwind)",
        alias="DATABASE_URL"
    )
    app_database_url: str = Field(
        default="sqlite:///./app_data.db", 
        description="Application database URL for user data (SQLite) - relative to main.py execution directory",
        alias="APP_DATABASE_URL"
    )
    northwind_database_url: str = Field(
        default="postgresql://postgres:password@localhost:5432/northwind",
        description="Northwind database URL for business data",
        alias="NORTHWIND_DATABASE_URL"
    )
    
    # Redis Configuration
    redis_url: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL",
        alias="REDIS_URL"
    )
    redis_enabled: bool = Field(default=True, description="Enable Redis caching")
    redis_host: str = Field(default="localhost", description="Redis server host")
    redis_port: int = Field(default=6379, description="Redis server port")
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    redis_db: int = Field(default=0, description="Redis database number")
    redis_ssl: bool = Field(default=False, description="Use SSL for Redis connection")
    
    # Security Configuration
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="Application secret key",
        alias="SECRET_KEY"
    )
    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production-with-256-bit-key",
        description="JWT signing secret key",
        alias="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT signing algorithm", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=60, 
        description="Access token expiration time in minutes",
        alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    refresh_token_expire_days: int = Field(
        default=7,
        description="Refresh token expiration time in days",
        alias="REFRESH_TOKEN_EXPIRE_DAYS"
    )
    
    # Application Configuration
    environment: str = Field(default="development", description="Application environment", alias="ENVIRONMENT")
    debug: bool = Field(default=True, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    server_host: str = Field(default="0.0.0.0", description="Server host", alias="SERVER_HOST")
    server_port: int = Field(default=8001, description="Server port", alias="SERVER_PORT")
    
    # Performance Configuration
    max_query_timeout: int = Field(default=30, description="Maximum query timeout in seconds")
    cache_ttl_seconds: int = Field(default=300, description="Cache TTL in seconds")
    max_concurrent_queries: int = Field(default=10, description="Maximum concurrent queries")
    connection_pool_size: int = Field(default=20, description="Database connection pool size")
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_requests_per_minute: int = Field(default=60, description="Requests per minute per user")
    rate_limit_requests_per_hour: int = Field(default=1000, description="Requests per hour per user")
    
    # Analytics Configuration
    analytics_enabled: bool = Field(default=True, description="Enable analytics tracking")
    analytics_retention_days: int = Field(default=90, description="Analytics data retention period")
    
    # Query Configuration
    max_result_rows: int = Field(default=1000, description="Maximum rows returned per query")
    query_timeout_seconds: int = Field(default=30, description="Query execution timeout")
    enable_query_caching: bool = Field(default=True, description="Enable query result caching")
    
    # Security Settings
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001", "http://frontend:3000"],
        description="CORS allowed origins"
    )
    enable_api_keys: bool = Field(default=True, description="Enable API key authentication")
    password_min_length: int = Field(default=8, description="Minimum password length")

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level", alias="LOG_LEVEL")
    log_to_file: bool = Field(default=True, description="Enable file logging", alias="LOG_TO_FILE")
    log_file_max_size_mb: int = Field(default=10, description="Log file max size in MB", alias="LOG_FILE_MAX_SIZE_MB")
    log_file_backup_count: int = Field(default=5, description="Number of log file backups", alias="LOG_FILE_BACKUP_COUNT")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string",
        alias="LOG_FORMAT"
    )
    
    # Structured Logging
    enable_json_logging: bool = Field(default=True, description="Enable JSON structured logging", alias="ENABLE_JSON_LOGGING")
    log_sql_queries: bool = Field(default=True, description="Log SQL queries", alias="LOG_SQL_QUERIES")
    log_api_requests: bool = Field(default=True, description="Log API requests", alias="LOG_API_REQUESTS")
    log_chat_messages: bool = Field(default=True, description="Log chat messages", alias="LOG_CHAT_MESSAGES")
    log_auth_events: bool = Field(default=True, description="Log authentication events", alias="LOG_AUTH_EVENTS")
    
    # Log Retention
    log_retention_days: int = Field(default=30, description="Log retention period in days", alias="LOG_RETENTION_DAYS")
    enable_log_compression: bool = Field(default=True, description="Compress old log files", alias="ENABLE_LOG_COMPRESSION")
    
    # Debug Logging
    debug_sql_queries: bool = Field(default=False, description="Enable debug level SQL query logging", alias="DEBUG_SQL_QUERIES")
    debug_api_requests: bool = Field(default=False, description="Enable debug level API request logging", alias="DEBUG_API_REQUESTS")
    log_request_body: bool = Field(default=True, description="Log request body (with masking)", alias="LOG_REQUEST_BODY")
    log_response_body: bool = Field(default=False, description="Log response body", alias="LOG_RESPONSE_BODY")
    
    # Performance Logging
    log_slow_queries: bool = Field(default=True, description="Log slow queries", alias="LOG_SLOW_QUERIES")
    slow_query_threshold_seconds: float = Field(default=1.0, description="Slow query threshold in seconds", alias="SLOW_QUERY_THRESHOLD_SECONDS")
    log_performance_metrics: bool = Field(default=True, description="Log performance metrics", alias="LOG_PERFORMANCE_METRICS")
    
    # Error Logging
    log_stack_traces: bool = Field(default=True, description="Include stack traces in error logs", alias="LOG_STACK_TRACES")
    enable_error_alerting: bool = Field(default=False, description="Enable error alerting", alias="ENABLE_ERROR_ALERTING")
    error_alert_webhook_url: Optional[str] = Field(default=None, description="Webhook URL for error alerts", alias="ERROR_ALERT_WEBHOOK_URL")
    
    # Log Filtering
    exclude_health_check_logs: bool = Field(default=True, description="Exclude health check from logs", alias="EXCLUDE_HEALTH_CHECK_LOGS")
    exclude_static_file_logs: bool = Field(default=True, description="Exclude static file requests from logs", alias="EXCLUDE_STATIC_FILE_LOGS")
    sensitive_data_patterns: List[str] = Field(
        default=["password", "token", "secret", "key", "auth", "credential"],
        description="Patterns to mask in logs",
        alias="SENSITIVE_DATA_PATTERNS"
    )

# Global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get the global settings instance"""
    return settings

# Validation checks
def validate_settings():
    """Validate critical settings on startup"""
    if not settings.azure_openai_endpoint:
        raise ValueError("AZURE_OPENAI_ENDPOINT is required")
    
    if not settings.azure_openai_api_key:
        raise ValueError("AZURE_OPENAI_API_KEY is required")
    
    if settings.environment == "production" and settings.jwt_secret_key == "your-secret-key-change-in-production-with-256-bit-key":
        raise ValueError("JWT_SECRET_KEY must be changed in production")
    
    return True
