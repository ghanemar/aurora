"""SQLAlchemy ORM models for Aurora multi-chain validator platform.

This package exports all database models for:
- Configuration & Registry: Chain, Provider, ChainProviderMapping
- Periods & Identity: CanonicalPeriod, CanonicalValidatorIdentity
- Staging Layer: IngestionRun, StagingPayload, IngestionStatus, DataType
- Canonical Layer: CanonicalValidatorFees, CanonicalValidatorMEV, CanonicalStakeRewards, CanonicalValidatorMeta
- Computation Layer: ValidatorPnL, Partners, Agreements, AgreementVersions, AgreementRules, PartnerCommissionLines, PartnerCommissionStatements
- Authentication: User, UserRole
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
from .canonical import (
    CanonicalStakeRewards,
    CanonicalValidatorFees,
    CanonicalValidatorMeta,
    CanonicalValidatorMEV,
)
from .chains import (
    CanonicalPeriod,
    CanonicalValidatorIdentity,
    Chain,
    ChainProviderMapping,
    Provider,
    Validator,
)
from .computation import (
    AgreementRules,
    Agreements,
    AgreementStatus,
    AgreementVersions,
    AttributionMethod,
    PartnerCommissionLines,
    PartnerCommissionStatements,
    Partners,
    PartnerWallet,
    RevenueComponent,
    StatementStatus,
    ValidatorPnL,
)
from .sample_data import (
    SampleEpochReward,
    SampleStakeAccount,
    SampleValidatorEpochSummary,
)
from .staging import (
    DataType,
    IngestionRun,
    IngestionStatus,
    StagingPayload,
)
from .users import User, UserRole

__all__ = [
    # Base
    "BaseModel",
    # Configuration & Registry
    "Chain",
    "Provider",
    "ChainProviderMapping",
    "Validator",
    # Periods & Identity
    "CanonicalPeriod",
    "CanonicalValidatorIdentity",
    # Staging Layer
    "IngestionRun",
    "StagingPayload",
    "IngestionStatus",
    "DataType",
    # Canonical Layer
    "CanonicalValidatorFees",
    "CanonicalValidatorMEV",
    "CanonicalStakeRewards",
    "CanonicalValidatorMeta",
    # Computation Layer
    "ValidatorPnL",
    "Partners",
    "PartnerWallet",
    "Agreements",
    "AgreementVersions",
    "AgreementRules",
    "PartnerCommissionLines",
    "PartnerCommissionStatements",
    # Computation Enums
    "AgreementStatus",
    "RevenueComponent",
    "AttributionMethod",
    "StatementStatus",
    # Sample Data (Testing)
    "SampleValidatorEpochSummary",
    "SampleStakeAccount",
    "SampleEpochReward",
    # Authentication
    "User",
    "UserRole",
]
