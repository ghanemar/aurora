"""Configuration module for Aurora.

This module provides configuration loading and management for blockchain
networks and data providers.
"""

from src.config.chains import ChainConfigError, ChainRegistry
from src.config.models import ChainConfig, PeriodType, ProviderConfig, ProviderMap
from src.config.providers import ProviderConfigError, ProviderRegistry
from src.config.settings import Settings, settings

__all__ = [
    # Settings
    "Settings",
    "settings",
    # Models
    "ChainConfig",
    "ProviderConfig",
    "ProviderMap",
    "PeriodType",
    # Registries
    "ChainRegistry",
    "ProviderRegistry",
    # Exceptions
    "ChainConfigError",
    "ProviderConfigError",
]
