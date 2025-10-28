"""Data source adapters for blockchain data ingestion.

This module provides adapters for fetching blockchain data from various providers,
with a consistent interface across different chains and data sources.
"""

from adapters.base import (
    ChainDataProvider,
    Period,
    StakeRewards,
    ValidatorFees,
    ValidatorMEV,
    ValidatorMeta,
)
from adapters.exceptions import (
    ProviderDataNotFoundError,
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)
from adapters.factory import ProviderFactory

__all__ = [
    # Base classes and models
    "ChainDataProvider",
    "Period",
    "ValidatorFees",
    "ValidatorMEV",
    "StakeRewards",
    "ValidatorMeta",
    # Exceptions
    "ProviderError",
    "ProviderTimeoutError",
    "ProviderRateLimitError",
    "ProviderDataNotFoundError",
    # Factory
    "ProviderFactory",
]
