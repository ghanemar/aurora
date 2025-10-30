"""Authentication and authorization API endpoints.

This module provides endpoints for:
- User login and JWT token generation
- Current user information retrieval
- Token validation
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user
from src.core.models import User
from src.core.security import create_access_token, verify_password
from src.db.session import get_db

# Create router
router = APIRouter(prefix="/auth", tags=["auth"])


# ============================================================================
# Pydantic Schemas
# ============================================================================


class LoginRequest(BaseModel):
    """Login request schema."""

    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=8, max_length=100, description="Password")


class TokenResponse(BaseModel):
    """JWT token response schema."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


class UserResponse(BaseModel):
    """User information response schema."""

    id: UUID = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: EmailStr = Field(..., description="Email address")
    full_name: str = Field(..., description="Full name")
    role: str = Field(..., description="User role (admin or partner)")
    is_active: bool = Field(..., description="Whether user is active")
    partner_id: UUID | None = Field(None, description="Partner ID (for partner role)")

    class Config:
        """Pydantic config."""

        from_attributes = True


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/login", response_model=TokenResponse)
async def login(
    login_request: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate user and return JWT token.

    Args:
        login_request: Login credentials (username and password)
        db: Database session

    Returns:
        JWT access token

    Raises:
        HTTPException: If credentials are invalid
    """
    # Fetch user by username
    stmt = select(User).where(User.username == login_request.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    # Verify user exists and password is correct
    if user is None or not verify_password(login_request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )

    # Create JWT token
    access_token = create_access_token(data={"sub": user.username})

    return TokenResponse(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Get current authenticated user information.

    Args:
        current_user: Current authenticated user from JWT token

    Returns:
        Current user information
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        partner_id=current_user.partner_id,
    )
