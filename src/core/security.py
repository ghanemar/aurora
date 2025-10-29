"""Security utilities for input validation and protection.

This module provides utilities for:
- Input sanitization and validation
- SQL injection protection patterns
- Safe string handling for database queries
- Request validation helpers
"""

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ValidationError(Exception):
    """Raised when input validation fails."""

    pass


# Patterns for input validation
SAFE_ALPHANUMERIC_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")
SAFE_CHAIN_ID_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SAFE_IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*$")

# Dangerous SQL keywords that should never appear in user input
SQL_INJECTION_KEYWORDS = {
    "SELECT",
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "CREATE",
    "ALTER",
    "TRUNCATE",
    "EXECUTE",
    "EXEC",
    "UNION",
    "DECLARE",
    "--",
    ";",
    "/*",
    "*/",
    "xp_",
    "sp_",
}


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """Sanitize a string input by removing dangerous characters.

    Args:
        value: String to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string

    Raises:
        ValidationError: If input is invalid
    """
    if not isinstance(value, str):
        raise ValidationError(f"Expected string, got {type(value).__name__}")

    # Strip whitespace
    value = value.strip()

    # Check length
    if len(value) > max_length:
        raise ValidationError(f"String exceeds maximum length of {max_length}")

    # Check for SQL injection patterns
    value_upper = value.upper()
    for keyword in SQL_INJECTION_KEYWORDS:
        if keyword in value_upper:
            raise ValidationError(f"Potentially dangerous keyword detected: {keyword}")

    return value


def validate_chain_id(chain_id: str) -> str:
    """Validate a chain identifier.

    Chain IDs must be lowercase alphanumeric with hyphens.
    Example: "solana-mainnet", "ethereum-mainnet"

    Args:
        chain_id: Chain identifier to validate

    Returns:
        Validated chain ID

    Raises:
        ValidationError: If chain ID format is invalid
    """
    chain_id = sanitize_string(chain_id, max_length=50)

    if not SAFE_CHAIN_ID_PATTERN.match(chain_id):
        raise ValidationError("Chain ID must be lowercase alphanumeric with hyphens only")

    return chain_id


def validate_identifier(identifier: str, field_name: str = "identifier") -> str:
    """Validate a safe identifier (for table names, column names, etc.).

    Identifiers must start with a letter and contain only alphanumeric and underscores.

    Args:
        identifier: Identifier to validate
        field_name: Name of the field for error messages

    Returns:
        Validated identifier

    Raises:
        ValidationError: If identifier format is invalid
    """
    identifier = sanitize_string(identifier, max_length=100)

    if not SAFE_IDENTIFIER_PATTERN.match(identifier):
        raise ValidationError(
            f"{field_name} must start with letter and contain only alphanumeric/underscore"
        )

    return identifier


def validate_pagination_params(
    page: int, page_size: int, max_page_size: int = 100
) -> tuple[int, int]:
    """Validate pagination parameters.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        max_page_size: Maximum allowed page size

    Returns:
        Tuple of (validated_page, validated_page_size)

    Raises:
        ValidationError: If parameters are invalid
    """
    if page < 1:
        raise ValidationError("Page must be >= 1")

    if page_size < 1:
        raise ValidationError("Page size must be >= 1")

    if page_size > max_page_size:
        raise ValidationError(f"Page size cannot exceed {max_page_size}")

    return page, page_size


class PaginationParams(BaseModel):
    """Pydantic model for pagination parameters."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page (max 100)")

    def to_offset_limit(self) -> tuple[int, int]:
        """Convert page/page_size to offset/limit for SQL queries.

        Returns:
            Tuple of (offset, limit)
        """
        offset = (self.page - 1) * self.page_size
        limit = self.page_size
        return offset, limit


class SafeQueryFilter(BaseModel):
    """Base model for safe query filters with validation.

    All filter models should inherit from this to ensure proper validation.
    """

    @field_validator("*", mode="before")
    @classmethod
    def sanitize_string_fields(cls, v: Any) -> Any:
        """Automatically sanitize all string fields."""
        if isinstance(v, str):
            return sanitize_string(v)
        return v


def escape_like_pattern(pattern: str) -> str:
    """Escape special characters in LIKE patterns.

    Args:
        pattern: Pattern string for LIKE query

    Returns:
        Escaped pattern safe for SQL LIKE

    Note:
        SQLAlchemy handles parameterization, but we still escape
        special LIKE characters (%, _, \\) to prevent unintended matches.
    """
    pattern = sanitize_string(pattern, max_length=200)

    # Escape LIKE special characters
    pattern = pattern.replace("\\", "\\\\")  # Backslash first
    pattern = pattern.replace("%", "\\%")  # Percent wildcard
    pattern = pattern.replace("_", "\\_")  # Underscore wildcard

    return pattern


# SQL Injection Protection Guidelines:
# 1. ALWAYS use SQLAlchemy ORM - never raw SQL strings
# 2. ALWAYS use parameterized queries with bound parameters
# 3. NEVER concatenate user input into SQL strings
# 4. NEVER use string formatting (f-strings, %, format()) for SQL
# 5. Validate and sanitize all user inputs before use
# 6. Use Pydantic models for automatic validation
# 7. Apply proper database permissions and least privilege

# Good Example (using SQLAlchemy):
# stmt = select(Chain).where(Chain.chain_id == chain_id)
# result = await session.execute(stmt)

# Bad Example (SQL injection vulnerable):
# query = f"SELECT * FROM chains WHERE chain_id = '{chain_id}'"
# DO NOT DO THIS!


# ============================================================================
# Password Hashing and Verification (for authentication)
# ============================================================================

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

from src.config.settings import get_settings

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt.

    Args:
        password: Plain-text password to hash

    Returns:
        Bcrypt-hashed password string

    Example:
        hashed = hash_password("my_secure_password")
        # Returns: $2b$12$...
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash.

    Args:
        plain_password: Plain-text password to verify
        hashed_password: Bcrypt-hashed password to compare against

    Returns:
        True if password matches, False otherwise

    Example:
        is_valid = verify_password("my_password", stored_hash)
    """
    return pwd_context.verify(plain_password, hashed_password)


# ============================================================================
# JWT Token Generation and Verification (for authentication)
# ============================================================================


def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token.

    Args:
        data: Dictionary of claims to encode in the token
        expires_delta: Optional custom expiration time delta

    Returns:
        Encoded JWT token string

    Example:
        token = create_access_token({"sub": user.username})
    """
    settings = get_settings()
    to_encode = data.copy()

    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire})

    # Encode JWT token
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    """Decode and validate a JWT access token.

    Args:
        token: JWT token string to decode

    Returns:
        Dictionary of decoded claims if valid, None if invalid

    Example:
        payload = decode_access_token(token)
        if payload:
            username = payload.get("sub")
    """
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None
