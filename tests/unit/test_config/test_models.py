"""Unit tests for configuration models."""

import pytest
from pydantic import ValidationError

from config.models import ChainConfig, PeriodType, ProviderConfig, ProviderMap


class TestPeriodType:
    """Tests for PeriodType enum."""

    def test_valid_period_types(self) -> None:
        """Test that all expected period types are valid."""
        assert PeriodType.EPOCH == "EPOCH"
        assert PeriodType.BLOCK_WINDOW == "BLOCK_WINDOW"
        assert PeriodType.SLOT_RANGE == "SLOT_RANGE"

    def test_period_type_values(self) -> None:
        """Test period type enum values."""
        assert PeriodType.EPOCH.value == "EPOCH"
        assert list(PeriodType) == [
            PeriodType.EPOCH,
            PeriodType.BLOCK_WINDOW,
            PeriodType.SLOT_RANGE,
        ]


class TestProviderMap:
    """Tests for ProviderMap model."""

    def test_valid_provider_map(self) -> None:
        """Test creating a valid ProviderMap."""
        provider_map = ProviderMap(
            fees="solana_beach",
            mev="jito",
            rewards="solana_beach",
            meta="solana_beach",
            rpc_url="https://api.mainnet-beta.solana.com",
        )
        assert provider_map.fees == "solana_beach"
        assert provider_map.mev == "jito"
        assert provider_map.rewards == "solana_beach"
        assert provider_map.meta == "solana_beach"
        assert provider_map.rpc_url == "https://api.mainnet-beta.solana.com"

    def test_rpc_url_validation(self) -> None:
        """Test RPC URL validation."""
        # Valid URL
        provider_map = ProviderMap(
            fees="test",
            mev="test",
            rewards="test",
            meta="test",
            rpc_url="  https://example.com  ",
        )
        assert provider_map.rpc_url == "https://example.com"

    def test_empty_rpc_url_fails(self) -> None:
        """Test that empty RPC URL raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            ProviderMap(fees="test", mev="test", rewards="test", meta="test", rpc_url="")
        assert "RPC URL cannot be empty" in str(exc_info.value)

    def test_missing_fields_fails(self) -> None:
        """Test that missing required fields raises validation error."""
        with pytest.raises(ValidationError):
            ProviderMap(fees="test", mev="test")  # type: ignore


class TestChainConfig:
    """Tests for ChainConfig model."""

    def test_valid_chain_config(self) -> None:
        """Test creating a valid ChainConfig."""
        chain_config = ChainConfig(
            chain_id="solana-mainnet",
            name="Solana Mainnet",
            period_type=PeriodType.EPOCH,
            native_unit="SOL",
            native_decimals=9,
            finality_lag=32,
            providers=ProviderMap(
                fees="solana_beach",
                mev="jito",
                rewards="solana_beach",
                meta="solana_beach",
                rpc_url="https://api.mainnet-beta.solana.com",
            ),
        )
        assert chain_config.chain_id == "solana-mainnet"
        assert chain_config.name == "Solana Mainnet"
        assert chain_config.period_type == PeriodType.EPOCH
        assert chain_config.native_unit == "SOL"
        assert chain_config.native_decimals == 9
        assert chain_config.finality_lag == 32
        assert chain_config.providers.fees == "solana_beach"

    def test_string_fields_trimmed(self) -> None:
        """Test that string fields are trimmed."""
        chain_config = ChainConfig(
            chain_id="  test-chain  ",
            name="  Test Chain  ",
            period_type=PeriodType.EPOCH,
            native_unit="  TST  ",
            native_decimals=9,
            finality_lag=10,
            providers=ProviderMap(
                fees="test",
                mev="test",
                rewards="test",
                meta="test",
                rpc_url="https://test.com",
            ),
        )
        assert chain_config.chain_id == "test-chain"
        assert chain_config.name == "Test Chain"
        assert chain_config.native_unit == "TST"

    def test_empty_chain_id_fails(self) -> None:
        """Test that empty chain_id raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            ChainConfig(
                chain_id="",
                name="Test",
                period_type=PeriodType.EPOCH,
                native_unit="TST",
                native_decimals=9,
                finality_lag=10,
                providers=ProviderMap(
                    fees="test",
                    mev="test",
                    rewards="test",
                    meta="test",
                    rpc_url="https://test.com",
                ),
            )
        assert "Field cannot be empty" in str(exc_info.value)

    def test_invalid_decimals_fails(self) -> None:
        """Test that invalid decimals raise validation error."""
        # Negative decimals
        with pytest.raises(ValidationError):
            ChainConfig(
                chain_id="test",
                name="Test",
                period_type=PeriodType.EPOCH,
                native_unit="TST",
                native_decimals=-1,
                finality_lag=10,
                providers=ProviderMap(
                    fees="test",
                    mev="test",
                    rewards="test",
                    meta="test",
                    rpc_url="https://test.com",
                ),
            )

        # Too many decimals
        with pytest.raises(ValidationError):
            ChainConfig(
                chain_id="test",
                name="Test",
                period_type=PeriodType.EPOCH,
                native_unit="TST",
                native_decimals=19,
                finality_lag=10,
                providers=ProviderMap(
                    fees="test",
                    mev="test",
                    rewards="test",
                    meta="test",
                    rpc_url="https://test.com",
                ),
            )

    def test_negative_finality_lag_fails(self) -> None:
        """Test that negative finality_lag raises validation error."""
        with pytest.raises(ValidationError):
            ChainConfig(
                chain_id="test",
                name="Test",
                period_type=PeriodType.EPOCH,
                native_unit="TST",
                native_decimals=9,
                finality_lag=-1,
                providers=ProviderMap(
                    fees="test",
                    mev="test",
                    rewards="test",
                    meta="test",
                    rpc_url="https://test.com",
                ),
            )


class TestProviderConfig:
    """Tests for ProviderConfig model."""

    def test_valid_provider_config(self) -> None:
        """Test creating a valid ProviderConfig."""
        provider_config = ProviderConfig(
            provider_name="solana_beach",
            enabled=True,
            base_url="https://api.solanabeach.io/v1",
            api_key="test-api-key",
            rate_limit=10,
            timeout=30,
            retry_attempts=3,
            metadata={"description": "Solana Beach API"},
        )
        assert provider_config.provider_name == "solana_beach"
        assert provider_config.enabled is True
        assert provider_config.base_url == "https://api.solanabeach.io/v1"
        assert provider_config.api_key == "test-api-key"
        assert provider_config.rate_limit == 10
        assert provider_config.timeout == 30
        assert provider_config.retry_attempts == 3
        assert provider_config.metadata == {"description": "Solana Beach API"}

    def test_default_values(self) -> None:
        """Test default values for optional fields."""
        provider_config = ProviderConfig(provider_name="test_provider")
        assert provider_config.enabled is True
        assert provider_config.base_url is None
        assert provider_config.api_key is None
        assert provider_config.rate_limit == 10
        assert provider_config.timeout == 30
        assert provider_config.retry_attempts == 3
        assert provider_config.metadata == {}

    def test_provider_name_trimmed(self) -> None:
        """Test that provider_name is trimmed."""
        provider_config = ProviderConfig(provider_name="  test_provider  ")
        assert provider_config.provider_name == "test_provider"

    def test_empty_provider_name_fails(self) -> None:
        """Test that empty provider_name raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            ProviderConfig(provider_name="")
        assert "Provider name cannot be empty" in str(exc_info.value)

    def test_base_url_validation(self) -> None:
        """Test base URL validation."""
        # Valid HTTPS URL
        provider_config = ProviderConfig(provider_name="test", base_url="https://example.com")
        assert provider_config.base_url == "https://example.com"

        # Valid HTTP URL
        provider_config = ProviderConfig(provider_name="test", base_url="http://example.com")
        assert provider_config.base_url == "http://example.com"

        # Empty string becomes None
        provider_config = ProviderConfig(provider_name="test", base_url="   ")
        assert provider_config.base_url is None

    def test_invalid_base_url_fails(self) -> None:
        """Test that invalid base URL raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            ProviderConfig(provider_name="test", base_url="ftp://example.com")
        assert "Base URL must start with http:// or https://" in str(exc_info.value)

    def test_invalid_rate_limit_fails(self) -> None:
        """Test that invalid rate_limit raises validation error."""
        with pytest.raises(ValidationError):
            ProviderConfig(provider_name="test", rate_limit=0)

    def test_invalid_timeout_fails(self) -> None:
        """Test that invalid timeout raises validation error."""
        # Too small
        with pytest.raises(ValidationError):
            ProviderConfig(provider_name="test", timeout=0)

        # Too large
        with pytest.raises(ValidationError):
            ProviderConfig(provider_name="test", timeout=301)

    def test_invalid_retry_attempts_fails(self) -> None:
        """Test that invalid retry_attempts raises validation error."""
        # Negative
        with pytest.raises(ValidationError):
            ProviderConfig(provider_name="test", retry_attempts=-1)

        # Too many
        with pytest.raises(ValidationError):
            ProviderConfig(provider_name="test", retry_attempts=11)
