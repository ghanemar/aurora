"""Unit tests for Jito MEV adapter.

Tests the Jito adapter implementation with mocked API responses.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from adapters.base import Period
from adapters.exceptions import (
    ProviderDataNotFoundError,
    ProviderError,
    ProviderValidationError,
)
from adapters.solana.jito import JitoAdapter


# Load test fixtures
@pytest.fixture
def fixtures() -> dict:
    """Load Jito API response fixtures."""
    fixtures_path = Path(__file__).parent.parent / "fixtures" / "jito_responses.json"
    with open(fixtures_path) as f:
        return json.load(f)


@pytest.fixture
def adapter() -> JitoAdapter:
    """Create Jito adapter instance."""
    return JitoAdapter(
        base_url="https://kobe.mainnet.jito.network",
        timeout=30,
        rate_limit_per_second=10,
    )


@pytest.fixture
def test_period() -> Period:
    """Create test period object for epoch 608."""
    return Period(
        period_id="608",
        start_time=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
        end_time=datetime(2024, 1, 2, 0, 0, 0, tzinfo=UTC),
    )


@pytest.fixture
def test_validator() -> str:
    """Test validator vote account."""
    return "63a15aZm4rphdQJcZfL8oSMPwLDmvUW2dFw3WqZpjxEt"


class TestJitoAdapterInitialization:
    """Tests for adapter initialization."""

    def test_initialization(self) -> None:
        """Test adapter initializes with correct values."""
        adapter = JitoAdapter(
            base_url="https://kobe.mainnet.jito.network",
            timeout=60,
            rate_limit_per_second=5,
        )

        assert adapter.provider_name == "jito"
        assert adapter.base_url == "https://kobe.mainnet.jito.network"
        assert adapter.timeout == 60
        assert adapter.rate_limit_per_second == 5

    def test_default_initialization(self) -> None:
        """Test adapter initializes with defaults."""
        adapter = JitoAdapter()

        assert adapter.provider_name == "jito"
        assert adapter.base_url == "https://kobe.mainnet.jito.network"
        assert adapter.timeout == 30
        assert adapter.rate_limit_per_second == 10


class TestGetValidatorPeriodMEV:
    """Tests for get_validator_period_mev method."""

    @pytest.mark.asyncio
    async def test_get_mev_success(
        self,
        adapter: JitoAdapter,
        test_period: Period,
        test_validator: str,
        fixtures: dict,
    ) -> None:
        """Test successfully fetching MEV for a validator."""
        with patch.object(
            adapter, "_request", return_value=fixtures["validator_mev_history_success"]
        ) as mock_request:
            mev = await adapter.get_validator_period_mev(test_period, test_validator)

            # Verify request was made correctly
            mock_request.assert_called_once_with(
                "GET",
                f"/api/v1/validators/{test_validator}",
            )

            # Verify MEV data
            assert mev.validator_key == test_validator
            assert mev.total_mev == 59355050
            assert mev.tip_count == 1
            assert mev.period_id == "608"

    @pytest.mark.asyncio
    async def test_get_mev_zero_rewards(
        self,
        adapter: JitoAdapter,
        test_period: Period,
        test_validator: str,
        fixtures: dict,
    ) -> None:
        """Test fetching MEV when validator has zero rewards."""
        with patch.object(
            adapter, "_request", return_value=fixtures["validator_mev_no_rewards"]
        ):
            mev = await adapter.get_validator_period_mev(test_period, test_validator)

            assert mev.validator_key == test_validator
            assert mev.total_mev == 0
            assert mev.tip_count == 0
            assert mev.period_id == "608"

    @pytest.mark.asyncio
    async def test_get_mev_epoch_not_found(
        self,
        adapter: JitoAdapter,
        test_validator: str,
        fixtures: dict,
    ) -> None:
        """Test fetching MEV for epoch not in response."""
        # Requesting epoch 999 which is not in the response
        missing_epoch_period = Period(
            period_id="999",
            start_time=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            end_time=datetime(2024, 1, 2, 0, 0, 0, tzinfo=UTC),
        )

        with patch.object(
            adapter, "_request", return_value=fixtures["validator_mev_history_success"]
        ):
            mev = await adapter.get_validator_period_mev(
                missing_epoch_period, test_validator
            )

            # Should return zero MEV for missing epoch
            assert mev.validator_key == test_validator
            assert mev.total_mev == 0
            assert mev.tip_count == 0
            assert mev.period_id == "999"

    @pytest.mark.asyncio
    async def test_get_mev_empty_response(
        self,
        adapter: JitoAdapter,
        test_period: Period,
        test_validator: str,
        fixtures: dict,
    ) -> None:
        """Test handling empty response from API."""
        with patch.object(
            adapter, "_request", return_value=fixtures["validator_mev_history_empty"]
        ) as mock_request:
            with pytest.raises(ProviderDataNotFoundError) as exc_info:
                await adapter.get_validator_period_mev(test_period, test_validator)

            mock_request.assert_called_once()
            assert "No MEV data available" in str(exc_info.value)
            assert exc_info.value.provider_name == "jito"

    @pytest.mark.asyncio
    async def test_get_mev_invalid_response_type(
        self,
        adapter: JitoAdapter,
        test_period: Period,
        test_validator: str,
    ) -> None:
        """Test handling invalid response type (not a list)."""
        with patch.object(
            adapter, "_request", return_value={"error": "invalid"}
        ) as mock_request:
            with pytest.raises(ProviderDataNotFoundError) as exc_info:
                await adapter.get_validator_period_mev(test_period, test_validator)

            mock_request.assert_called_once()
            assert "No MEV data available" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_mev_large_rewards(
        self,
        adapter: JitoAdapter,
        test_validator: str,
        fixtures: dict,
    ) -> None:
        """Test handling large MEV reward values."""
        large_reward_period = Period(
            period_id="620",
            start_time=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            end_time=datetime(2024, 1, 2, 0, 0, 0, tzinfo=UTC),
        )

        with patch.object(
            adapter, "_request", return_value=fixtures["validator_mev_large_rewards"]
        ):
            mev = await adapter.get_validator_period_mev(
                large_reward_period, test_validator
            )

            assert mev.total_mev == 5000000000  # 5 SOL in lamports
            assert mev.tip_count == 1


class TestGetValidatorMeta:
    """Tests for get_validator_meta method."""

    @pytest.mark.asyncio
    async def test_get_meta_success(
        self,
        adapter: JitoAdapter,
        test_period: Period,
        test_validator: str,
        fixtures: dict,
    ) -> None:
        """Test successfully fetching validator metadata."""
        with patch.object(
            adapter, "_request", return_value=fixtures["validator_mev_history_success"]
        ):
            meta = await adapter.get_validator_meta(test_period, test_validator)

            assert meta.validator_key == test_validator
            assert meta.commission_rate_bps == 10000  # 100%
            assert meta.is_mev_enabled is True
            assert meta.total_stake == 0  # Not provided by Jito
            assert meta.period_id == "608"

    @pytest.mark.asyncio
    async def test_get_meta_different_commissions(
        self,
        adapter: JitoAdapter,
        test_validator: str,
        fixtures: dict,
    ) -> None:
        """Test fetching metadata with different commission rates."""
        epoch_610_period = Period(
            period_id="610",
            start_time=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            end_time=datetime(2024, 1, 2, 0, 0, 0, tzinfo=UTC),
        )

        with patch.object(
            adapter,
            "_request",
            return_value=fixtures["validator_mev_different_commissions"],
        ):
            meta = await adapter.get_validator_meta(epoch_610_period, test_validator)

            assert meta.commission_rate_bps == 5000  # 50%
            assert meta.is_mev_enabled is True

    @pytest.mark.asyncio
    async def test_get_meta_zero_mev(
        self,
        adapter: JitoAdapter,
        test_period: Period,
        test_validator: str,
        fixtures: dict,
    ) -> None:
        """Test metadata when validator has zero MEV."""
        with patch.object(
            adapter, "_request", return_value=fixtures["validator_mev_no_rewards"]
        ):
            meta = await adapter.get_validator_meta(test_period, test_validator)

            assert meta.commission_rate_bps == 10000
            assert meta.is_mev_enabled is False  # No MEV earned
            assert meta.total_stake == 0

    @pytest.mark.asyncio
    async def test_get_meta_epoch_not_found(
        self,
        adapter: JitoAdapter,
        test_validator: str,
        fixtures: dict,
    ) -> None:
        """Test metadata for epoch not in response."""
        missing_epoch_period = Period(
            period_id="999",
            start_time=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            end_time=datetime(2024, 1, 2, 0, 0, 0, tzinfo=UTC),
        )

        with patch.object(
            adapter, "_request", return_value=fixtures["validator_mev_history_success"]
        ) as mock_request:
            with pytest.raises(ProviderDataNotFoundError) as exc_info:
                await adapter.get_validator_meta(missing_epoch_period, test_validator)

            mock_request.assert_called_once()
            assert "No metadata for validator" in str(exc_info.value)
            assert exc_info.value.provider_name == "jito"

    @pytest.mark.asyncio
    async def test_get_meta_empty_response(
        self,
        adapter: JitoAdapter,
        test_period: Period,
        test_validator: str,
        fixtures: dict,
    ) -> None:
        """Test metadata with empty API response."""
        with patch.object(
            adapter, "_request", return_value=fixtures["validator_mev_history_empty"]
        ) as mock_request:
            with pytest.raises(ProviderDataNotFoundError) as exc_info:
                await adapter.get_validator_meta(test_period, test_validator)

            mock_request.assert_called_once()
            assert "No data available" in str(exc_info.value)


class TestUnsupportedMethods:
    """Tests for methods not supported by Jito API."""

    @pytest.mark.asyncio
    async def test_list_periods_not_supported(
        self,
        adapter: JitoAdapter,
    ) -> None:
        """Test that list_periods raises NotImplementedError."""
        start = datetime(2024, 1, 1, tzinfo=UTC)
        end = datetime(2024, 1, 3, tzinfo=UTC)

        with pytest.raises(NotImplementedError) as exc_info:
            await adapter.list_periods(start, end)

        assert "does not support epoch listing" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_fees_not_supported(
        self,
        adapter: JitoAdapter,
        test_period: Period,
        test_validator: str,
    ) -> None:
        """Test that get_validator_period_fees raises NotImplementedError."""
        with pytest.raises(NotImplementedError) as exc_info:
            await adapter.get_validator_period_fees(test_period, test_validator)

        assert "does not provide fee data" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_rewards_not_supported(
        self,
        adapter: JitoAdapter,
        test_period: Period,
        test_validator: str,
    ) -> None:
        """Test that get_stake_rewards raises NotImplementedError."""
        with pytest.raises(NotImplementedError) as exc_info:
            await adapter.get_stake_rewards(test_period, test_validator)

        assert "does not provide staking rewards" in str(exc_info.value)


class TestErrorHandling:
    """Tests for error handling scenarios."""

    @pytest.mark.asyncio
    async def test_network_error(
        self,
        adapter: JitoAdapter,
        test_period: Period,
        test_validator: str,
    ) -> None:
        """Test handling of network errors."""
        with patch.object(
            adapter, "_request", side_effect=ProviderError("Network error", "jito")
        ) as mock_request:
            with pytest.raises(ProviderError) as exc_info:
                await adapter.get_validator_period_mev(test_period, test_validator)

            mock_request.assert_called_once()
            assert "Network error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_unexpected_exception(
        self,
        adapter: JitoAdapter,
        test_period: Period,
        test_validator: str,
    ) -> None:
        """Test handling of unexpected exceptions."""
        with patch.object(
            adapter, "_request", side_effect=ValueError("Unexpected error")
        ) as mock_request:
            with pytest.raises(ProviderError) as exc_info:
                await adapter.get_validator_period_mev(test_period, test_validator)

            mock_request.assert_called_once()
            assert "Failed to fetch validator MEV" in str(exc_info.value)
            assert exc_info.value.provider_name == "jito"


class TestResourceCleanup:
    """Tests for resource cleanup."""

    @pytest.mark.asyncio
    async def test_close_adapter(self, adapter: JitoAdapter) -> None:
        """Test adapter cleanup."""
        # Close should work without errors even if client not initialized
        await adapter.close()
        assert adapter._client is None
