"""Base adapter interface for blockchain data providers.

This module defines the abstract base class and data models that all chain-specific
adapters must implement, ensuring consistent interaction patterns across providers.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any

import httpx
from pydantic import BaseModel, Field
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from adapters.exceptions import (
    CircuitBreakerOpenError,
    ProviderAuthenticationError,
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderValidationError,
)


class Period(BaseModel):
    """Represents a time period on a blockchain.

    Attributes:
        period_id: Unique identifier for the period (e.g., epoch number, block range)
        start_time: UTC timestamp when the period started
        end_time: UTC timestamp when the period ended
        metadata: Additional period-specific data (optional)
    """

    period_id: str = Field(..., description="Unique period identifier")
    start_time: datetime = Field(..., description="Period start time (UTC)")
    end_time: datetime = Field(..., description="Period end time (UTC)")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional period metadata"
    )


class ValidatorFees(BaseModel):
    """Transaction fees earned by a validator in a period.

    Attributes:
        validator_key: Validator's public key or identifier
        total_fees: Total fees earned in native units (smallest denomination)
        fee_count: Number of fee-bearing transactions
        period_id: Period identifier for these fees
    """

    validator_key: str = Field(..., description="Validator identifier")
    total_fees: int = Field(..., ge=0, description="Total fees in native units")
    fee_count: int = Field(..., ge=0, description="Number of transactions with fees")
    period_id: str = Field(..., description="Period identifier")


class ValidatorMEV(BaseModel):
    """MEV (Maximal Extractable Value) earned by a validator in a period.

    Attributes:
        validator_key: Validator's public key or identifier
        total_mev: Total MEV earned in native units (smallest denomination)
        tip_count: Number of MEV-bearing transactions/bundles
        period_id: Period identifier for this MEV data
    """

    validator_key: str = Field(..., description="Validator identifier")
    total_mev: int = Field(..., ge=0, description="Total MEV in native units")
    tip_count: int = Field(..., ge=0, description="Number of MEV transactions")
    period_id: str = Field(..., description="Period identifier")


class StakeRewards(BaseModel):
    """Staking rewards for a validator or staker in a period.

    Attributes:
        validator_key: Validator's public key or identifier
        staker_address: Staker's address (None for validator self-stake)
        rewards: Reward amount in native units (smallest denomination)
        commission: Commission amount in native units (for validator)
        period_id: Period identifier for these rewards
    """

    validator_key: str = Field(..., description="Validator identifier")
    staker_address: str | None = Field(None, description="Staker address (if applicable)")
    rewards: int = Field(..., description="Reward amount in native units")
    commission: int = Field(..., ge=0, description="Commission amount in native units")
    period_id: str = Field(..., description="Period identifier")


class ValidatorMeta(BaseModel):
    """Metadata for a validator in a specific period.

    Attributes:
        validator_key: Validator's public key or identifier
        commission_rate_bps: Commission rate in basis points (100 bps = 1%)
        is_mev_enabled: Whether MEV is enabled for this validator
        total_stake: Total stake delegated to validator in native units
        period_id: Period identifier for this metadata snapshot
    """

    validator_key: str = Field(..., description="Validator identifier")
    commission_rate_bps: int = Field(
        ..., ge=0, le=10000, description="Commission rate in basis points"
    )
    is_mev_enabled: bool = Field(..., description="MEV enabled status")
    total_stake: int = Field(..., ge=0, description="Total delegated stake in native units")
    period_id: str = Field(..., description="Period identifier")


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"  # Blocking requests
    HALF_OPEN = "HALF_OPEN"  # Testing if service recovered


class CircuitBreaker:
    """Circuit breaker for provider fault tolerance.

    Tracks failures and automatically opens circuit when failure threshold
    is exceeded, preventing cascading failures and giving provider time to recover.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_attempts: int = 1,
    ) -> None:
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            half_open_attempts: Number of test requests in half-open state
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_attempts = half_open_attempts

        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.state = CircuitState.CLOSED
        self.half_open_successes = 0

    def record_success(self) -> None:
        """Record successful request."""
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_successes += 1
            if self.half_open_successes >= self.half_open_attempts:
                self._close()
        elif self.state == CircuitState.CLOSED:
            self.failure_count = max(0, self.failure_count - 1)

    def record_failure(self) -> None:
        """Record failed request."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            self._open()
        elif self.failure_count >= self.failure_threshold:
            self._open()

    def can_attempt(self) -> bool:
        """Check if request can be attempted.

        Returns:
            True if request should be attempted, False otherwise

        Raises:
            CircuitBreakerOpenError: If circuit is open and not ready for retry
        """
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._half_open()
                return True
            return False

        # HALF_OPEN state
        return True

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        return (time.time() - self.last_failure_time) >= self.recovery_timeout

    def _open(self) -> None:
        """Open the circuit."""
        self.state = CircuitState.OPEN
        self.half_open_successes = 0

    def _half_open(self) -> None:
        """Move to half-open state for testing."""
        self.state = CircuitState.HALF_OPEN
        self.half_open_successes = 0

    def _close(self) -> None:
        """Close the circuit."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.half_open_successes = 0

    def get_state_info(self) -> dict[str, Any]:
        """Get current circuit breaker state information."""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time,
            "can_attempt": self.can_attempt(),
        }


class ChainDataProvider(ABC):
    """Abstract base class for all blockchain data providers.

    This class defines the interface that all chain-specific adapters must implement,
    providing consistent methods for fetching validator data across different providers.
    It includes built-in retry logic, rate limiting, and circuit breaker protection.
    """

    def __init__(
        self,
        provider_name: str,
        base_url: str,
        api_key: str | None = None,
        timeout: int = 30,
        rate_limit_per_second: int | None = None,
        retry_attempts: int = 3,
        circuit_breaker_threshold: int = 5,
    ) -> None:
        """Initialize the data provider.

        Args:
            provider_name: Name of the provider (for logging and error messages)
            base_url: Base URL for the provider's API
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
            rate_limit_per_second: Maximum requests per second (None for no limit)
            retry_attempts: Number of retry attempts for failed requests
            circuit_breaker_threshold: Failures before circuit breaker opens
        """
        self.provider_name = provider_name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.rate_limit_per_second = rate_limit_per_second
        self.retry_attempts = retry_attempts

        self._client: httpx.AsyncClient | None = None
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=circuit_breaker_threshold,
            recovery_timeout=60,
            half_open_attempts=1,
        )
        self._last_request_time: float | None = None
        self._rate_limit_lock = asyncio.Lock()

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client.

        Returns:
            Configured async HTTP client
        """
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers=self._get_headers(),
            )
        return self._client

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers including authentication if configured.

        Returns:
            Dictionary of HTTP headers
        """
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        if self.rate_limit_per_second is None:
            return

        async with self._rate_limit_lock:
            if self._last_request_time is not None:
                min_interval = 1.0 / self.rate_limit_per_second
                elapsed = time.time() - self._last_request_time
                if elapsed < min_interval:
                    await asyncio.sleep(min_interval - elapsed)
            self._last_request_time = time.time()

    @retry(
        retry=retry_if_exception_type(
            (httpx.TimeoutException, httpx.NetworkError, ProviderTimeoutError)
        ),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make HTTP request with retry logic and circuit breaker.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments to pass to httpx request

        Returns:
            Response JSON data

        Raises:
            CircuitBreakerOpenError: If circuit breaker is open
            ProviderTimeoutError: If request times out
            ProviderRateLimitError: If rate limit is exceeded
            ProviderAuthenticationError: If authentication fails
            ProviderError: For other provider errors
        """
        # Check circuit breaker
        if not self._circuit_breaker.can_attempt():
            raise CircuitBreakerOpenError(
                "Circuit breaker is open, requests temporarily blocked",
                provider_name=self.provider_name,
                open_until=self._circuit_breaker.last_failure_time + 60
                if self._circuit_breaker.last_failure_time
                else None,
            )

        # Enforce rate limiting
        await self._enforce_rate_limit()

        try:
            client = await self._get_client()
            response = await client.request(method, endpoint, **kwargs)

            # Check for rate limiting response
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                self._circuit_breaker.record_failure()
                raise ProviderRateLimitError(
                    "Rate limit exceeded",
                    provider_name=self.provider_name,
                    retry_after=int(retry_after) if retry_after else None,
                )

            # Check for authentication errors
            if response.status_code == 401:
                self._circuit_breaker.record_failure()
                raise ProviderAuthenticationError(
                    "Authentication failed - check API key",
                    provider_name=self.provider_name,
                )

            response.raise_for_status()
            self._circuit_breaker.record_success()
            result: dict[str, Any] = response.json()
            return result

        except httpx.TimeoutException as e:
            self._circuit_breaker.record_failure()
            raise ProviderTimeoutError(
                f"Request timed out after {self.timeout}s",
                provider_name=self.provider_name,
            ) from e
        except httpx.HTTPStatusError as e:
            self._circuit_breaker.record_failure()
            raise ProviderError(
                f"HTTP error: {e.response.status_code}",
                provider_name=self.provider_name,
                details={"status_code": e.response.status_code, "response": e.response.text},
            ) from e
        except httpx.RequestError as e:
            self._circuit_breaker.record_failure()
            raise ProviderError(
                f"Request failed: {str(e)}",
                provider_name=self.provider_name,
            ) from e

    @abstractmethod
    async def list_periods(self, start: datetime, end: datetime) -> list[Period]:
        """List finalized periods within the given time range.

        Args:
            start: Start of time range (UTC)
            end: End of time range (UTC)

        Returns:
            List of Period objects representing finalized periods

        Raises:
            ProviderError: If request fails
        """
        pass

    @abstractmethod
    async def get_validator_period_fees(
        self, period: Period, validator_identity: str
    ) -> ValidatorFees:
        """Fetch execution fees for a validator in a specific period.

        Args:
            period: Period to fetch fees for
            validator_identity: Validator's public key or identifier

        Returns:
            ValidatorFees object with fee data

        Raises:
            ProviderDataNotFoundError: If validator or period not found
            ProviderError: If request fails
        """
        pass

    @abstractmethod
    async def get_validator_period_mev(
        self, period: Period, validator_identity: str
    ) -> ValidatorMEV:
        """Fetch MEV tips for a validator in a specific period.

        Args:
            period: Period to fetch MEV for
            validator_identity: Validator's public key or identifier

        Returns:
            ValidatorMEV object with MEV data

        Raises:
            ProviderDataNotFoundError: If validator or period not found
            ProviderError: If request fails
        """
        pass

    @abstractmethod
    async def get_stake_rewards(
        self, period: Period, validator_identity: str
    ) -> list[StakeRewards]:
        """Fetch staking rewards for a validator in a specific period.

        Args:
            period: Period to fetch rewards for
            validator_identity: Validator's public key or identifier

        Returns:
            List of StakeRewards objects (one per staker)

        Raises:
            ProviderDataNotFoundError: If validator or period not found
            ProviderError: If request fails
        """
        pass

    @abstractmethod
    async def get_validator_meta(
        self, period: Period, validator_identity: str
    ) -> ValidatorMeta:
        """Fetch validator metadata for a specific period.

        Args:
            period: Period to fetch metadata for
            validator_identity: Validator's public key or identifier

        Returns:
            ValidatorMeta object with validator metadata

        Raises:
            ProviderDataNotFoundError: If validator or period not found
            ProviderError: If request fails
        """
        pass

    def get_circuit_breaker_state(self) -> dict[str, Any]:
        """Get current circuit breaker state.

        Returns:
            Dictionary with circuit breaker state information
        """
        return self._circuit_breaker.get_state_info()

    async def close(self) -> None:
        """Close HTTP client and clean up resources."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
