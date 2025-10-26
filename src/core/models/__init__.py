"""SQLAlchemy ORM models for Aurora multi-chain validator platform.

This package exports all database models for:
- Configuration & Registry: Chain, Provider, ChainProviderMapping
- Canonical Layer: CanonicalPeriod, CanonicalValidatorIdentity
- Staging Layer: IngestionRun, StagingPayload, IngestionStatus, DataType
- Base Model: BaseModel with common timestamp fields

Example:
    from src.core.models import Chain, Provider, ChainProviderMapping

    # Create a new chain
    chain = Chain(
        chain_id="solana-mainnet",
        name="Solana Mainnet",
        period_type="EPOCH",
        native_unit="lamports",
        native_decimals=9,
        finality_lag=2,
        is_active=True
    )
"""

from .base import BaseModel
from .chains import (
    CanonicalPeriod,
    CanonicalValidatorIdentity,
    Chain,
    ChainProviderMapping,
    Provider,
)
from .staging import (
    DataType,
    IngestionRun,
    IngestionStatus,
    StagingPayload,
)

__all__ = [
    # Base
    "BaseModel",
    # Configuration & Registry
    "Chain",
    "Provider",
    "ChainProviderMapping",
    # Canonical Layer
    "CanonicalPeriod",
    "CanonicalValidatorIdentity",
    # Staging Layer
    "IngestionRun",
    "StagingPayload",
    "IngestionStatus",
    "DataType",
]
