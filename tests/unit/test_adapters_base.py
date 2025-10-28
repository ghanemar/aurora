"""Unit tests for base adapter functionality.

Tests the abstract base adapter class, circuit breaker, and common functionality.
"""

import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from adapters.base import (
    ChainDataProvider,
    CircuitBreaker,
    CircuitState,
    Period,
    StakeRewards,
    ValidatorFees,
    ValidatorMeta,
    ValidatorMEV,
)
from adapters.exceptions import (
    CircuitBreakerOpenError,
    ProviderAuthenticationError,
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)
from pydantic import ValidationError


# Concrete implementation for testing
class TestAdapter(ChainDataProvider):
    """Test implementation of ChainDataProvider."""

    async def list_periods(self, start: datetime, end: datetime) -> list[Period]:
        """Test implementation."""
        return []

    async def get_validator_period_fees(
        self, period: Period, validator_identity: str
    ) -> ValidatorFees:
        """Test implementation."""
        return ValidatorFees(
            validator_key=validator_identity,
            total_fees=0,
            fee_count=0,
            period_id=period.period_id,
        )

    async def get_validator_period_mev(
        self, period: Period, validator_identity: str
    ) -> ValidatorMEV:
        """Test implementation."""
        return ValidatorMEV(
            validator_key=validator_identity,
            total_mev=0,
            tip_count=0,
            period_id=period.period_id,
        )

    async def get_stake_rewards(
        self, period: Period, validator_identity: str
    ) -> list[StakeRewards]:
        """Test implementation."""
        return []

    async def get_validator_meta(
        self, period: Period, validator_identity: str
    ) -> ValidatorMeta:
        """Test implementation."""
        return ValidatorMeta(
            validator_key=validator_identity,
            commission_rate_bps=1000,
            is_mev_enabled=True,
            total_stake=0,
            period_id=period.period_id,
        )


class TestPeriodModel:
    """Tests for Period data model."""

    def test_period_creation(self) -> None:
        """Test creating a valid Period object."""
        start = datetime(2024, 1, 1, 0, 0, 0)
        end = datetime(2024, 1, 1, 1, 0, 0)

        period = Period(
            period_id="epoch-100",
            start_time=start,
            end_time=end,
        )

        assert period.period_id == "epoch-100"
        assert period.start_time == start
        assert period.end_time == end
        assert period.metadata == {}

    def test_period_with_metadata(self) -> None:
        """Test Period with metadata."""
        start = datetime(2024, 1, 1, 0, 0, 0)
        end = datetime(2024, 1, 1, 1, 0, 0)
        metadata = {"chain": "solana", "slot_range": [1000, 2000]}

        period = Period(
            period_id="epoch-100",
            start_time=start,
            end_time=end,
            metadata=metadata,
        )

        assert period.metadata == metadata


class TestValidatorFeesModel:
    """Tests for ValidatorFees data model."""

    def test_validator_fees_creation(self) -> None:
        """Test creating valid ValidatorFees object."""
        fees = ValidatorFees(
            validator_key="abc123",
            total_fees=1000000,
            fee_count=50,
            period_id="epoch-100",
        )

        assert fees.validator_key == "abc123"
        assert fees.total_fees == 1000000
        assert fees.fee_count == 50
        assert fees.period_id == "epoch-100"

    def test_validator_fees_non_negative(self) -> None:
        """Test that negative fees are rejected."""
        with pytest.raises(ValidationError):
            ValidatorFees(
                validator_key="abc123",
                total_fees=-1000,
                fee_count=50,
                period_id="epoch-100",
            )


class TestValidatorMEVModel:
    """Tests for ValidatorMEV data model."""

    def test_validator_mev_creation(self) -> None:
        """Test creating valid ValidatorMEV object."""
        mev = ValidatorMEV(
            validator_key="abc123",
            total_mev=5000000,
            tip_count=10,
            period_id="epoch-100",
        )

        assert mev.validator_key == "abc123"
        assert mev.total_mev == 5000000
        assert mev.tip_count == 10
        assert mev.period_id == "epoch-100"


class TestStakeRewardsModel:
    """Tests for StakeRewards data model."""

    def test_stake_rewards_creation(self) -> None:
        """Test creating valid StakeRewards object."""
        rewards = StakeRewards(
            validator_key="abc123",
            staker_address="staker456",
            rewards=100000,
            commission=10000,
            period_id="epoch-100",
        )

        assert rewards.validator_key == "abc123"
        assert rewards.staker_address == "staker456"
        assert rewards.rewards == 100000
        assert rewards.commission == 10000

    def test_stake_rewards_no_staker(self) -> None:
        """Test StakeRewards without staker address (validator self-stake)."""
        rewards = StakeRewards(
            validator_key="abc123",
            staker_address=None,
            rewards=100000,
            commission=10000,
            period_id="epoch-100",
        )

        assert rewards.staker_address is None


class TestValidatorMetaModel:
    """Tests for ValidatorMeta data model."""

    def test_validator_meta_creation(self) -> None:
        """Test creating valid ValidatorMeta object."""
        meta = ValidatorMeta(
            validator_key="abc123",
            commission_rate_bps=1000,
            is_mev_enabled=True,
            total_stake=5000000000,
            period_id="epoch-100",
        )

        assert meta.validator_key == "abc123"
        assert meta.commission_rate_bps == 1000
        assert meta.is_mev_enabled is True
        assert meta.total_stake == 5000000000

    def test_validator_meta_commission_range(self) -> None:
        """Test commission rate must be in valid range."""
        with pytest.raises(ValidationError):
            ValidatorMeta(
                validator_key="abc123",
                commission_rate_bps=15000,  # Invalid: > 10000
                is_mev_enabled=True,
                total_stake=5000000000,
                period_id="epoch-100",
            )


class TestCircuitBreaker:
    """Tests for CircuitBreaker functionality."""

    def test_initial_state_closed(self) -> None:
        """Test circuit breaker starts in closed state."""
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED
        assert cb.can_attempt() is True

    def test_opens_after_threshold_failures(self) -> None:
        """Test circuit opens after failure threshold."""
        cb = CircuitBreaker(failure_threshold=3)

        # Record failures
        for _ in range(3):
            cb.record_failure()

        assert cb.state == CircuitState.OPEN

    def test_half_open_after_recovery_timeout(self) -> None:
        """Test circuit moves to half-open after timeout."""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)

        # Trigger circuit to open
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Wait for recovery timeout
        time.sleep(1.1)

        # Next attempt should move to half-open
        assert cb.can_attempt() is True
        assert cb.state == CircuitState.HALF_OPEN

    def test_closes_after_successful_half_open(self) -> None:
        """Test circuit closes after successful half-open attempt."""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1, half_open_attempts=1)

        # Open circuit
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Wait and transition to half-open
        time.sleep(1.1)
        cb.can_attempt()
        assert cb.state == CircuitState.HALF_OPEN

        # Record success - should close
        cb.record_success()
        assert cb.state == CircuitState.CLOSED

    def test_reopens_on_half_open_failure(self) -> None:
        """Test circuit reopens if half-open attempt fails."""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)

        # Open circuit
        cb.record_failure()
        cb.record_failure()

        # Move to half-open
        time.sleep(1.1)
        cb.can_attempt()

        # Fail again - should reopen
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_get_state_info(self) -> None:
        """Test getting circuit breaker state information."""
        cb = CircuitBreaker()
        info = cb.get_state_info()

        assert "state" in info
        assert "failure_count" in info
        assert "can_attempt" in info
        assert info["state"] == CircuitState.CLOSED.value


class TestChainDataProvider:
    """Tests for ChainDataProvider base class."""

    @pytest.mark.asyncio
    async def test_initialization(self) -> None:
        """Test adapter initialization."""
        adapter = TestAdapter(
            provider_name="test",
            base_url="https://api.example.com",
            api_key="test_key",
            timeout=60,
            rate_limit_per_second=10,
        )

        assert adapter.provider_name == "test"
        assert adapter.base_url == "https://api.example.com"
        assert adapter.api_key == "test_key"
        assert adapter.timeout == 60
        assert adapter.rate_limit_per_second == 10

        await adapter.close()

    @pytest.mark.asyncio
    async def test_get_headers_with_api_key(self) -> None:
        """Test headers include API key when configured."""
        adapter = TestAdapter(
            provider_name="test",
            base_url="https://api.example.com",
            api_key="secret_key",
        )

        headers = adapter._get_headers()
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer secret_key"

        await adapter.close()

    @pytest.mark.asyncio
    async def test_get_headers_without_api_key(self) -> None:
        """Test headers without API key."""
        adapter = TestAdapter(
            provider_name="test",
            base_url="https://api.example.com",
        )

        headers = adapter._get_headers()
        assert "Authorization" not in headers
        assert headers["Content-Type"] == "application/json"

        await adapter.close()

    @pytest.mark.asyncio
    async def test_rate_limiting(self) -> None:
        """Test rate limiting enforcement."""
        adapter = TestAdapter(
            provider_name="test",
            base_url="https://api.example.com",
            rate_limit_per_second=2,  # 2 requests per second = 0.5s interval
        )

        start_time = time.time()

        # Make 3 requests
        await adapter._enforce_rate_limit()
        await adapter._enforce_rate_limit()
        await adapter._enforce_rate_limit()

        elapsed = time.time() - start_time

        # Should take at least 1 second (2 intervals of 0.5s each)
        assert elapsed >= 1.0

        await adapter.close()

    @pytest.mark.asyncio
    async def test_request_timeout_error(self) -> None:
        """Test request timeout raises ProviderTimeoutError."""
        adapter = TestAdapter(
            provider_name="test",
            base_url="https://api.example.com",
            timeout=1,
        )

        with patch.object(
            adapter, "_get_client", return_value=AsyncMock()
        ) as mock_client_getter:
            mock_client = mock_client_getter.return_value
            mock_client.request = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))

            with pytest.raises(ProviderTimeoutError):
                await adapter._request("GET", "/test")

        await adapter.close()

    @pytest.mark.asyncio
    async def test_request_rate_limit_error(self) -> None:
        """Test 429 response raises ProviderRateLimitError."""
        adapter = TestAdapter(
            provider_name="test",
            base_url="https://api.example.com",
        )

        with patch.object(
            adapter, "_get_client", return_value=AsyncMock()
        ) as mock_client_getter:
            mock_client = mock_client_getter.return_value
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_response.headers = {"Retry-After": "60"}
            mock_client.request = AsyncMock(return_value=mock_response)

            with pytest.raises(ProviderRateLimitError) as exc_info:
                await adapter._request("GET", "/test")

            assert exc_info.value.retry_after == 60

        await adapter.close()

    @pytest.mark.asyncio
    async def test_request_auth_error(self) -> None:
        """Test 401 response raises ProviderAuthenticationError."""
        adapter = TestAdapter(
            provider_name="test",
            base_url="https://api.example.com",
        )

        with patch.object(
            adapter, "_get_client", return_value=AsyncMock()
        ) as mock_client_getter:
            mock_client = mock_client_getter.return_value
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_client.request = AsyncMock(return_value=mock_response)

            with pytest.raises(ProviderAuthenticationError):
                await adapter._request("GET", "/test")

        await adapter.close()

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens(self) -> None:
        """Test circuit breaker opens after failures."""
        adapter = TestAdapter(
            provider_name="test",
            base_url="https://api.example.com",
            circuit_breaker_threshold=2,
            retry_attempts=1,  # Disable retries to test circuit breaker directly
        )

        with patch.object(
            adapter, "_get_client", return_value=AsyncMock()
        ) as mock_client_getter:
            mock_client = mock_client_getter.return_value
            # Use HTTPStatusError which doesn't trigger retry
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_client.request = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "Server error", request=MagicMock(), response=mock_response
                )
            )

            # First two failures should work, but open the circuit
            with pytest.raises(ProviderError):
                await adapter._request("GET", "/test")

            with pytest.raises(ProviderError):
                await adapter._request("GET", "/test")

            # Circuit should be open now
            state = adapter.get_circuit_breaker_state()
            assert state["state"] == CircuitState.OPEN.value

            # Next request should be blocked
            with pytest.raises(CircuitBreakerOpenError):
                await adapter._request("GET", "/test")

        await adapter.close()

    @pytest.mark.asyncio
    async def test_successful_request(self) -> None:
        """Test successful request flow."""
        adapter = TestAdapter(
            provider_name="test",
            base_url="https://api.example.com",
        )

        with patch.object(
            adapter, "_get_client", return_value=AsyncMock()
        ) as mock_client_getter:
            mock_client = mock_client_getter.return_value
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json = MagicMock(return_value={"data": "test"})
            mock_response.raise_for_status = MagicMock()
            mock_client.request = AsyncMock(return_value=mock_response)

            result = await adapter._request("GET", "/test")

            assert result == {"data": "test"}
            state = adapter.get_circuit_breaker_state()
            assert state["state"] == CircuitState.CLOSED.value

        await adapter.close()

    @pytest.mark.asyncio
    async def test_close_cleanup(self) -> None:
        """Test close() cleans up resources."""
        adapter = TestAdapter(
            provider_name="test",
            base_url="https://api.example.com",
        )

        # Initialize client
        await adapter._get_client()
        assert adapter._client is not None

        # Close should clean up
        await adapter.close()
        assert adapter._client is None
