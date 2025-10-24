"""Configuration settings module for the application.

This module provides application settings management using Pydantic Settings,
with support for loading configuration from environment variables and .env files.
Settings are cached using lru_cache for efficient access throughout the application.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings.

    This class manages all configuration settings for the application, with
    automatic loading from environment variables and .env files. Settings
    are validated using Pydantic.

    Attributes:
        DEBUG: Flag indicating whether debug mode is enabled. Defaults to False.
    """

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    DEBUG: bool = False


@lru_cache
def get_settings():
    """Returns a cached instance of application settings.

    This function creates and caches a Settings instance, ensuring that
    settings are loaded only once and reused throughout the application
    lifecycle for improved performance.

    Returns:
        Settings: The cached application settings instance.

    Examples:
        >>> settings = get_settings()
        >>> if settings.DEBUG:
        ...     print("Debug mode enabled")
    """
    return Settings()
