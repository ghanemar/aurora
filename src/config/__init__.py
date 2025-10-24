"""Configuration module for Aurora.

This module provides configuration loading and management for blockchain
networks and data providers.
"""

from config.chains import ChainConfigError, ChainRegistry
from config.models import ChainConfig, PeriodType, ProviderConfig, ProviderMap
from config.providers import ProviderConfigError, ProviderRegistry
from config.settings import Settings, settings

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
