"""Unit tests for Solana Beach adapter.

Tests the Solana Beach adapter implementation with mocked API responses.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from adapters.base import Period
from adapters.exceptions import (
    ProviderDataNotFoundError,
    ProviderError,
    ProviderValidationError,
)
from adapters.solana.solana_beach import SolanaBeachAdapter


# Load test fixtures
@pytest.fixture
def fixtures() -> dict:
    """Load Solana Beach API response fixtures."""
    fixtures_path = Path(__file__).parent.parent / "fixtures" / "solana_beach_responses.json"
    with open(fixtures_path) as f:
        return json.load(f)


@pytest.fixture
def adapter() -> SolanaBeachAdapter:
    """Create Solana Beach adapter instance."""
    return SolanaBeachAdapter(
        base_url="https://api.solanabeach.io/v1",
        api_key="test_key",
        timeout=30,
        rate_limit_per_second=10,
    )


@pytest.fixture
def test_period() -> Period:
    """Create test period object."""
    return Period(
        period_id="500",
        start_time=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        end_time=datetime(2024, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
    )


class TestSolanaBeachAdapterInitialization:
    """Tests for adapter initialization."""

    def test_initialization(self) -> None:
        """Test adapter initializes with correct values."""
        adapter = SolanaBeachAdapter(
            base_url="https://api.solanabeach.io/v1",
            api_key="test_key",
            timeout=60,
            rate_limit_per_second=5,
        )

        assert adapter.provider_name == "solana_beach"
        assert adapter.base_url == "https://api.solanabeach.io/v1"
        assert adapter.api_key == "test_key"
        assert adapter.timeout == 60
        assert adapter.rate_limit_per_second == 5

    def test_default_initialization(self) -> None:
        """Test adapter initializes with defaults."""
        adapter = SolanaBeachAdapter()

        assert adapter.provider_name == "solana_beach"
        assert adapter.base_url == "https://api.solanabeach.io/v1"
        assert adapter.timeout == 30
        assert adapter.rate_limit_per_second == 10


class TestListPeriods:
    """Tests for list_periods method."""

    @pytest.mark.asyncio
    async def test_list_periods_success(
        self,
        adapter: SolanaBeachAdapter,
        fixtures: dict,
    ) -> None:
        """Test successfully listing periods."""
        with patch.object(
            adapter, "_request", return_value=fixtures["epochs_response"]
        ) as mock_request:
            start = datetime(2024, 1, 1, tzinfo=timezone.utc)
            end = datetime(2024, 1, 3, tzinfo=timezone.utc)

            periods = await adapter.list_periods(start, end)

            # Should only return finalized epochs (500, 501)
            assert len(periods) == 2
            assert periods[0].period_id == "500"
            assert periods[1].period_id == "501"

            # Verify request was made
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_periods_empty(
        self,
        adapter: SolanaBeachAdapter,
    ) -> None:
        """Test listing periods with no results."""
        with patch.object(adapter, "_request", return_value={"epochs": []}):
            start = datetime(2024, 1, 1, tzinfo=timezone.utc)
            end = datetime(2024, 1, 3, tzinfo=timezone.utc)

            periods = await adapter.list_periods(start, end)

            assert len(periods) == 0

    @pytest.mark.asyncio
    async def test_list_periods_error(
        self,
        adapter: SolanaBeachAdapter,
    ) -> None:
        """Test error handling in list_periods."""
        with patch.object(adapter, "_request", side_effect=ProviderError("API error")):
            start = datetime(2024, 1, 1, tzinfo=timezone.utc)
            end = datetime(2024, 1, 3, tzinfo=timezone.utc)

            with pytest.raises(ProviderError):
                await adapter.list_periods(start, end)


class TestGetValidatorPeriodFees:
    """Tests for get_validator_period_fees method."""

    @pytest.mark.asyncio
    async def test_get_fees_success(
        self,
        adapter: SolanaBeachAdapter,
        test_period: Period,
        fixtures: dict,
    ) -> None:
        """Test successfully fetching validator fees."""
        with patch.object(
            adapter, "_request", return_value=fixtures["validator_fees_response"]
        ):
            fees = await adapter.get_validator_period_fees(
                test_period,
                "GvZEwtCHZ7YtCkQCaLRVEXsyVvQkRDhphsZPkhov5cSo",
            )

            assert fees.validator_key == "GvZEwtCHZ7YtCkQCaLRVEXsyVvQkRDhphsZPkhov5cSo"
            assert fees.total_fees == 5000000000
            assert fees.fee_count == 1250
            assert fees.period_id == "500"

    @pytest.mark.asyncio
    async def test_get_fees_no_data(
        self,
        adapter: SolanaBeachAdapter,
        test_period: Period,
        fixtures: dict,
    ) -> None:
        """Test fetching fees when no data available."""
        with patch.object(
            adapter, "_request", return_value=fixtures["validator_fees_no_data"]
        ):
            with pytest.raises(ProviderDataNotFoundError) as exc_info:
                await adapter.get_validator_period_fees(
                    test_period,
                    "GvZEwtCHZ7YtCkQCaLRVEXsyVvQkRDhphsZPkhov5cSo",
                )

            assert exc_info.value.resource_type == "validator_fees"

    @pytest.mark.asyncio
    async def test_get_fees_invalid_response(
        self,
        adapter: SolanaBeachAdapter,
        test_period: Period,
    ) -> None:
        """Test handling invalid fee response."""
        with patch.object(
            adapter,
            "_request",
            return_value={"total_fees": "invalid", "transaction_count": 100},
        ):
            with pytest.raises(ProviderValidationError):
                await adapter.get_validator_period_fees(
                    test_period,
                    "GvZEwtCHZ7YtCkQCaLRVEXsyVvQkRDhphsZPkhov5cSo",
                )


class TestGetValidatorPeriodMEV:
    """Tests for get_validator_period_mev method."""

    @pytest.mark.asyncio
    async def test_get_mev_success(
        self,
        adapter: SolanaBeachAdapter,
        test_period: Period,
        fixtures: dict,
    ) -> None:
        """Test successfully fetching validator MEV."""
        with patch.object(
            adapter, "_request", return_value=fixtures["validator_mev_response"]
        ):
            mev = await adapter.get_validator_period_mev(
                test_period,
                "GvZEwtCHZ7YtCkQCaLRVEXsyVvQkRDhphsZPkhov5cSo",
            )

            assert mev.validator_key == "GvZEwtCHZ7YtCkQCaLRVEXsyVvQkRDhphsZPkhov5cSo"
            assert mev.total_mev == 2000000000
            assert mev.tip_count == 50
            assert mev.period_id == "500"

    @pytest.mark.asyncio
    async def test_get_mev_no_data(
        self,
        adapter: SolanaBeachAdapter,
        test_period: Period,
        fixtures: dict,
    ) -> None:
        """Test fetching MEV when no data available (returns zeros)."""
        with patch.object(
            adapter, "_request", return_value=fixtures["validator_mev_no_data"]
        ):
            mev = await adapter.get_validator_period_mev(
                test_period,
                "GvZEwtCHZ7YtCkQCaLRVEXsyVvQkRDhphsZPkhov5cSo",
            )

            # Should return zero values instead of raising error
            assert mev.total_mev == 0
            assert mev.tip_count == 0


class TestGetStakeRewards:
    """Tests for get_stake_rewards method."""

    @pytest.mark.asyncio
    async def test_get_rewards_success(
        self,
        adapter: SolanaBeachAdapter,
        test_period: Period,
        fixtures: dict,
    ) -> None:
        """Test successfully fetching stake rewards."""
        with patch.object(
            adapter, "_request", return_value=fixtures["validator_rewards_response"]
        ):
            rewards = await adapter.get_stake_rewards(
                test_period,
                "GvZEwtCHZ7YtCkQCaLRVEXsyVvQkRDhphsZPkhov5cSo",
            )

            assert len(rewards) == 3

            # First staker
            assert rewards[0].validator_key == "GvZEwtCHZ7YtCkQCaLRVEXsyVvQkRDhphsZPkhov5cSo"
            assert rewards[0].staker_address == "9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin"
            assert rewards[0].rewards == 1000000000
            assert rewards[0].commission == 100000000

            # Self-stake (no staker address)
            assert rewards[2].staker_address is None
            assert rewards[2].rewards == 500000000

    @pytest.mark.asyncio
    async def test_get_rewards_no_data(
        self,
        adapter: SolanaBeachAdapter,
        test_period: Period,
        fixtures: dict,
    ) -> None:
        """Test fetching rewards when no data available."""
        with patch.object(
            adapter, "_request", return_value=fixtures["validator_rewards_no_data"]
        ):
            with pytest.raises(ProviderDataNotFoundError) as exc_info:
                await adapter.get_stake_rewards(
                    test_period,
                    "GvZEwtCHZ7YtCkQCaLRVEXsyVvQkRDhphsZPkhov5cSo",
                )

            assert exc_info.value.resource_type == "stake_rewards"

    @pytest.mark.asyncio
    async def test_get_rewards_invalid_response(
        self,
        adapter: SolanaBeachAdapter,
        test_period: Period,
    ) -> None:
        """Test handling invalid rewards response."""
        with patch.object(
            adapter,
            "_request",
            return_value={
                "rewards": [
                    {
                        "staker_address": "addr1",
                        "rewards": "invalid",
                        "commission": 100,
                    }
                ]
            },
        ):
            with pytest.raises(ProviderValidationError):
                await adapter.get_stake_rewards(
                    test_period,
                    "GvZEwtCHZ7YtCkQCaLRVEXsyVvQkRDhphsZPkhov5cSo",
                )


class TestGetValidatorMeta:
    """Tests for get_validator_meta method."""

    @pytest.mark.asyncio
    async def test_get_meta_success(
        self,
        adapter: SolanaBeachAdapter,
        test_period: Period,
        fixtures: dict,
    ) -> None:
        """Test successfully fetching validator metadata."""
        with patch.object(
            adapter, "_request", return_value=fixtures["validator_meta_response"]
        ):
            meta = await adapter.get_validator_meta(
                test_period,
                "GvZEwtCHZ7YtCkQCaLRVEXsyVvQkRDhphsZPkhov5cSo",
            )

            assert meta.validator_key == "GvZEwtCHZ7YtCkQCaLRVEXsyVvQkRDhphsZPkhov5cSo"
            assert meta.commission_rate_bps == 1000  # 10% = 1000 bps
            assert meta.is_mev_enabled is True
            assert meta.total_stake == 50000000000000
            assert meta.period_id == "500"

    @pytest.mark.asyncio
    async def test_get_meta_no_mev(
        self,
        adapter: SolanaBeachAdapter,
        test_period: Period,
        fixtures: dict,
    ) -> None:
        """Test fetching metadata for validator without MEV."""
        with patch.object(
            adapter, "_request", return_value=fixtures["validator_meta_no_mev"]
        ):
            meta = await adapter.get_validator_meta(
                test_period,
                "GvZEwtCHZ7YtCkQCaLRVEXsyVvQkRDhphsZPkhov5cSo",
            )

            assert meta.commission_rate_bps == 500  # 5% = 500 bps
            assert meta.is_mev_enabled is False

    @pytest.mark.asyncio
    async def test_get_meta_no_data(
        self,
        adapter: SolanaBeachAdapter,
        test_period: Period,
    ) -> None:
        """Test fetching metadata when no data available."""
        with patch.object(adapter, "_request", return_value=None):
            with pytest.raises(ProviderDataNotFoundError) as exc_info:
                await adapter.get_validator_meta(
                    test_period,
                    "GvZEwtCHZ7YtCkQCaLRVEXsyVvQkRDhphsZPkhov5cSo",
                )

            assert exc_info.value.resource_type == "validator_meta"

    @pytest.mark.asyncio
    async def test_get_meta_invalid_response(
        self,
        adapter: SolanaBeachAdapter,
        test_period: Period,
    ) -> None:
        """Test handling invalid metadata response."""
        with patch.object(
            adapter,
            "_request",
            return_value={
                "commission": "invalid",
                "mev_enabled": True,
                "total_stake": 1000,
            },
        ):
            with pytest.raises(ProviderValidationError):
                await adapter.get_validator_meta(
                    test_period,
                    "GvZEwtCHZ7YtCkQCaLRVEXsyVvQkRDhphsZPkhov5cSo",
                )


class TestErrorHandling:
    """Tests for error handling across all methods."""

    @pytest.mark.asyncio
    async def test_provider_error_propagation(
        self,
        adapter: SolanaBeachAdapter,
        test_period: Period,
    ) -> None:
        """Test that ProviderError is properly propagated."""
        with patch.object(
            adapter, "_request", side_effect=ProviderError("Test error")
        ):
            with pytest.raises(ProviderError):
                await adapter.get_validator_period_fees(
                    test_period,
                    "test_validator",
                )

    @pytest.mark.asyncio
    async def test_generic_exception_handling(
        self,
        adapter: SolanaBeachAdapter,
        test_period: Period,
    ) -> None:
        """Test generic exception handling wraps in ProviderError."""
        with patch.object(adapter, "_request", side_effect=ValueError("Unexpected error")):
            with pytest.raises(ProviderError) as exc_info:
                await adapter.get_validator_period_fees(
                    test_period,
                    "test_validator",
                )

            assert "Failed to fetch validator fees" in str(exc_info.value)
