"""Configuration module for Aurora.

This module provides configuration loading and management for blockchain
networks and data providers.
"""

from aurora.config.chains import ChainConfigError, ChainRegistry
from aurora.config.models import ChainConfig, PeriodType, ProviderConfig, ProviderMap
from aurora.config.providers import ProviderConfigError, ProviderRegistry
from aurora.config.settings import Settings, settings

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
