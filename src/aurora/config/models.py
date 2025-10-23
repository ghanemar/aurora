"""Configuration models for Aurora.

This module defines Pydantic models for chain and provider configurations.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class PeriodType(str, Enum):
    """Types of periods used by different blockchain networks."""

    EPOCH = "EPOCH"
    BLOCK_WINDOW = "BLOCK_WINDOW"
    SLOT_RANGE = "SLOT_RANGE"


class ProviderMap(BaseModel):
    """Map of data providers for a specific chain.

    Attributes:
        fees: Provider for transaction fees data
        mev: Provider for MEV (Maximal Extractable Value) data
        rewards: Provider for staking rewards data
        meta: Provider for metadata and general chain information
        rpc_url: RPC endpoint URL for the chain
    """

    fees: str = Field(..., description="Provider for transaction fees data")
    mev: str = Field(..., description="Provider for MEV data")
    rewards: str = Field(..., description="Provider for staking rewards data")
    meta: str = Field(..., description="Provider for metadata")
    rpc_url: str = Field(..., description="RPC endpoint URL")

    @field_validator("rpc_url")
    @classmethod
    def validate_rpc_url(cls, v: str) -> str:
        """Validate that RPC URL is not empty."""
        if not v or not v.strip():
            raise ValueError("RPC URL cannot be empty")
        return v.strip()


class ChainConfig(BaseModel):
    """Configuration for a blockchain network.

    Attributes:
        chain_id: Unique identifier for the chain
        name: Human-readable name of the chain
        period_type: Type of period used by the chain (epoch, block window, etc.)
        native_unit: Native currency unit (e.g., "SOL", "ETH")
        native_decimals: Number of decimal places for the native currency
        finality_lag: Number of blocks/epochs for finality
        providers: Map of data providers for this chain
    """

    chain_id: str = Field(..., description="Unique chain identifier")
    name: str = Field(..., description="Human-readable chain name")
    period_type: PeriodType = Field(..., description="Period type for this chain")
    native_unit: str = Field(..., description="Native currency unit")
    native_decimals: int = Field(..., ge=0, le=18, description="Native currency decimals")
    finality_lag: int = Field(..., ge=0, description="Blocks/epochs for finality")
    providers: ProviderMap = Field(..., description="Provider map for this chain")

    @field_validator("chain_id", "name", "native_unit")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        """Validate that string fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()


class ProviderConfig(BaseModel):
    """Configuration for a data provider.

    Attributes:
        provider_name: Unique identifier for the provider
        enabled: Whether this provider is currently active
        base_url: Base URL for the provider's API (if applicable)
        api_key: API key for authentication (if required)
        rate_limit: Maximum requests per second
        timeout: Request timeout in seconds
        retry_attempts: Number of retry attempts for failed requests
        metadata: Additional provider-specific configuration
    """

    provider_name: str = Field(..., description="Unique provider identifier")
    enabled: bool = Field(default=True, description="Whether provider is active")
    base_url: str | None = Field(default=None, description="Base API URL")
    api_key: str | None = Field(default=None, description="API key for authentication")
    rate_limit: int = Field(default=10, ge=1, description="Requests per second")
    timeout: int = Field(default=30, ge=1, le=300, description="Request timeout in seconds")
    retry_attempts: int = Field(default=3, ge=0, le=10, description="Number of retry attempts")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional config")

    @field_validator("provider_name")
    @classmethod
    def validate_provider_name(cls, v: str) -> str:
        """Validate that provider name is not empty."""
        if not v or not v.strip():
            raise ValueError("Provider name cannot be empty")
        return v.strip()

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: str | None) -> str | None:
        """Validate that base URL is properly formatted if provided."""
        if v is not None:
            v = v.strip()
            if not v:
                return None
            if not (v.startswith("http://") or v.startswith("https://")):
                raise ValueError("Base URL must start with http:// or https://")
        return v
