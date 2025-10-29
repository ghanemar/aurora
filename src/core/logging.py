"""Security-aware structured logging configuration.

This module provides:
- Security event logging (auth, permissions, rate limits)
- PII filtering for sensitive data
- Structured logging with correlation IDs
- Integration with structlog for JSON output
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, WrappedLogger

from src.config.settings import settings

# Sensitive field names that should be filtered from logs
SENSITIVE_FIELDS = {
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "authorization",
    "auth",
    "credential",
    "private_key",
    "access_token",
    "refresh_token",
    "session_id",
    "cookie",
}


def filter_sensitive_data(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Filter sensitive data from log events.

    Replaces sensitive field values with [REDACTED] to prevent
    accidental logging of credentials or personal information.

    Args:
        logger: The logger instance
        method_name: Name of the logging method
        event_dict: Event dictionary to filter

    Returns:
        Filtered event dictionary
    """
    for key in list(event_dict.keys()):
        # Check if key name suggests sensitive data
        if any(sensitive in key.lower() for sensitive in SENSITIVE_FIELDS):
            event_dict[key] = "[REDACTED]"

        # Check nested dictionaries
        elif isinstance(event_dict[key], dict):
            for nested_key in list(event_dict[key].keys()):
                if any(sensitive in nested_key.lower() for sensitive in SENSITIVE_FIELDS):
                    event_dict[key][nested_key] = "[REDACTED]"

    return event_dict


def add_correlation_id(logger: WrappedLogger, method_name: str, event_dict: EventDict) -> EventDict:
    """Add correlation ID to log events if present in context.

    Args:
        logger: The logger instance
        method_name: Name of the logging method
        event_dict: Event dictionary to enhance

    Returns:
        Enhanced event dictionary
    """
    # Check if correlation_id is in the bound context
    if hasattr(logger, "_context") and "correlation_id" in logger._context:
        event_dict["correlation_id"] = logger._context["correlation_id"]

    return event_dict


def setup_logging(log_level: str | None = None) -> None:
    """Configure structured logging for the application.

    Sets up structlog with:
    - JSON formatting for machine-readable logs
    - PII filtering for sensitive data
    - Timestamp and log level
    - Correlation ID support

    Args:
        log_level: Override log level (defaults to settings.LOG_LEVEL)
    """
    level_str: str = log_level or str(getattr(settings, "log_level", "INFO"))

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level_str.upper()),
    )

    # Configure structlog processors
    processors = [
        # Add log level
        structlog.stdlib.add_log_level,
        # Add logger name
        structlog.stdlib.add_logger_name,
        # Add timestamp in ISO format
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        # Filter sensitive data (IMPORTANT for security)
        filter_sensitive_data,
        # Add correlation ID if present
        add_correlation_id,
        # Format stack traces
        structlog.processors.format_exc_info,
        # Render as JSON for production
        structlog.processors.JSONRenderer(),
    ]

    # For development, use console renderer for readability
    if settings.debug:
        processors[-1] = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=processors,  # type: ignore[arg-type]
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a logger instance with the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)  # type: ignore[no-any-return]


# Security event helpers
def log_security_event(
    logger: structlog.BoundLogger,
    event_type: str,
    user_id: str | None = None,
    ip_address: str | None = None,
    **kwargs: Any,
) -> None:
    """Log a security-related event.

    Args:
        logger: Logger instance
        event_type: Type of security event (auth_success, auth_failure, etc.)
        user_id: User identifier if applicable
        ip_address: Client IP address
        **kwargs: Additional context for the event
    """
    logger.info(
        "security_event",
        event_type=event_type,
        user_id=user_id or "anonymous",
        ip_address=ip_address or "unknown",
        **kwargs,
    )


def log_auth_attempt(
    logger: structlog.BoundLogger,
    success: bool,
    username: str,
    ip_address: str,
    reason: str | None = None,
) -> None:
    """Log an authentication attempt.

    Args:
        logger: Logger instance
        success: Whether authentication succeeded
        username: Username attempting to authenticate
        ip_address: Client IP address
        reason: Failure reason if unsuccessful
    """
    event_type = "auth_success" if success else "auth_failure"
    log_security_event(
        logger,
        event_type=event_type,
        username=username,
        ip_address=ip_address,
        reason=reason,
    )


def log_permission_denied(
    logger: structlog.BoundLogger,
    user_id: str,
    resource: str,
    action: str,
    ip_address: str,
) -> None:
    """Log a permission denial event.

    Args:
        logger: Logger instance
        user_id: User identifier
        resource: Resource being accessed
        action: Action attempted
        ip_address: Client IP address
    """
    log_security_event(
        logger,
        event_type="permission_denied",
        user_id=user_id,
        resource=resource,
        action=action,
        ip_address=ip_address,
    )


def log_rate_limit_exceeded(
    logger: structlog.BoundLogger,
    user_id: str | None,
    ip_address: str,
    endpoint: str,
    limit: int,
) -> None:
    """Log a rate limit exceeded event.

    Args:
        logger: Logger instance
        user_id: User identifier if authenticated
        ip_address: Client IP address
        endpoint: API endpoint
        limit: Rate limit that was exceeded
    """
    log_security_event(
        logger,
        event_type="rate_limit_exceeded",
        user_id=user_id,
        ip_address=ip_address,
        endpoint=endpoint,
        limit=limit,
    )


def log_data_access(
    logger: structlog.BoundLogger,
    user_id: str,
    resource: str,
    operation: str,
    record_count: int | None = None,
) -> None:
    """Log a data access event for audit trails.

    Args:
        logger: Logger instance
        user_id: User identifier
        resource: Resource accessed
        operation: Operation performed (read, write, delete)
        record_count: Number of records affected
    """
    log_security_event(
        logger,
        event_type="data_access",
        user_id=user_id,
        resource=resource,
        operation=operation,
        record_count=record_count,
    )


# Logging best practices:
# 1. NEVER log sensitive data (passwords, tokens, personal info)
# 2. ALWAYS log security events (auth, permissions, rate limits)
# 3. Use structured logging for machine parsing
# 4. Include correlation IDs for request tracing
# 5. Log at appropriate levels (DEBUG, INFO, WARNING, ERROR)
# 6. Include context (user_id, ip_address, resource)
# 7. Filter sensitive fields automatically
# 8. Use JSON format for production logs
