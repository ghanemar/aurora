"""Custom exceptions for data provider adapters.

This module defines exception hierarchy for handling various failure modes
when interacting with blockchain data providers.
"""

from typing import Any


class ProviderError(Exception):
    """Base exception for all provider-related errors.

    This is the parent class for all adapter exceptions and should be used
    for catching any provider-related failures.

    Attributes:
        message: Human-readable error message
        provider_name: Name of the provider that raised the error (optional)
        details: Additional error details (optional)
    """

    def __init__(
        self,
        message: str,
        provider_name: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize ProviderError.

        Args:
            message: Human-readable error message
            provider_name: Name of the provider that raised the error
            details: Additional error details
        """
        self.message = message
        self.provider_name = provider_name
        self.details = details or {}
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format error message with provider name if available."""
        if self.provider_name:
            return f"[{self.provider_name}] {self.message}"
        return self.message


class ProviderTimeoutError(ProviderError):
    """Provider request timed out.

    Raised when a request to the provider exceeds the configured timeout period.
    This may indicate network issues or provider performance problems.
    """

    pass


class ProviderRateLimitError(ProviderError):
    """Provider rate limit exceeded.

    Raised when too many requests have been sent to the provider in a given time
    period. The adapter should implement backoff strategies to handle this.

    Attributes:
        retry_after: Number of seconds to wait before retrying (optional)
    """

    def __init__(
        self,
        message: str,
        provider_name: str | None = None,
        details: dict[str, Any] | None = None,
        retry_after: int | None = None,
    ) -> None:
        """Initialize ProviderRateLimitError.

        Args:
            message: Human-readable error message
            provider_name: Name of the provider that raised the error
            details: Additional error details
            retry_after: Suggested seconds to wait before retrying
        """
        super().__init__(message, provider_name, details)
        self.retry_after = retry_after


class ProviderDataNotFoundError(ProviderError):
    """Requested data not found at provider.

    Raised when the provider does not have data for the requested resource.
    This could be due to invalid identifiers, data not yet available, or
    data outside the provider's retention period.

    Attributes:
        resource_type: Type of resource requested (e.g., "epoch", "validator")
        resource_id: Identifier of the resource not found
    """

    def __init__(
        self,
        message: str,
        provider_name: str | None = None,
        details: dict[str, Any] | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
    ) -> None:
        """Initialize ProviderDataNotFoundError.

        Args:
            message: Human-readable error message
            provider_name: Name of the provider that raised the error
            details: Additional error details
            resource_type: Type of resource that was not found
            resource_id: Identifier of the resource not found
        """
        super().__init__(message, provider_name, details)
        self.resource_type = resource_type
        self.resource_id = resource_id


class ProviderAuthenticationError(ProviderError):
    """Authentication with provider failed.

    Raised when API key is invalid, expired, or missing when required.
    """

    pass


class ProviderValidationError(ProviderError):
    """Provider response validation failed.

    Raised when the provider returns data that doesn't match expected schema
    or contains invalid values.
    """

    pass


class CircuitBreakerOpenError(ProviderError):
    """Circuit breaker is open, requests blocked.

    Raised when the circuit breaker has detected too many failures and is
    temporarily blocking requests to protect the provider and application.

    Attributes:
        open_until: Timestamp when circuit breaker will attempt to close
    """

    def __init__(
        self,
        message: str,
        provider_name: str | None = None,
        details: dict[str, Any] | None = None,
        open_until: float | None = None,
    ) -> None:
        """Initialize CircuitBreakerOpenError.

        Args:
            message: Human-readable error message
            provider_name: Name of the provider that raised the error
            details: Additional error details
            open_until: Unix timestamp when circuit breaker will attempt to close
        """
        super().__init__(message, provider_name, details)
        self.open_until = open_until
