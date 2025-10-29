"""Validator service with business logic.

This module provides the service layer for validator-related operations,
implementing business logic and validation for validator P&L management.
"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models.computation import ValidatorPnL
from src.repositories.validators import ValidatorPnLRepository


class ValidatorService:
    """Service for validator business logic.

    This service orchestrates validator-related operations including
    P&L retrieval and calculation management.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize validator service with database session.

        Args:
            session: The async database session
        """
        self.session = session
        self.pnl_repo = ValidatorPnLRepository(session)

    async def get_validator_pnl(
        self,
        validator_key: str,
        chain_id: str | None = None,
        period_id: UUID | None = None,
    ) -> list[ValidatorPnL]:
        """Get validator P&L records with optional filtering.

        Args:
            validator_key: Validator public key or identifier
            chain_id: Optional chain identifier to filter by
            period_id: Optional period UUID to filter by

        Returns:
            List of ValidatorPnL records matching filters

        Raises:
            ValueError: If validator_key is invalid
        """
        if not validator_key or not validator_key.strip():
            raise ValueError("validator_key must be provided")

        filters = {"validator_key": validator_key}

        if chain_id:
            filters["chain_id"] = chain_id

        if period_id:
            filters["period_id"] = period_id

        return await self.pnl_repo.filter_by(**filters, order_by="computed_at")

    async def get_validator_pnl_by_period(
        self,
        validator_key: str,
        period_id: UUID,
    ) -> ValidatorPnL | None:
        """Get validator P&L for a specific period.

        Args:
            validator_key: Validator public key or identifier
            period_id: Period UUID

        Returns:
            ValidatorPnL record if found, None otherwise

        Raises:
            ValueError: If parameters are invalid
        """
        if not validator_key or not validator_key.strip():
            raise ValueError("validator_key must be provided")

        if not period_id:
            raise ValueError("period_id must be provided")

        pnl_records = await self.pnl_repo.filter_by(
            validator_key=validator_key,
            period_id=period_id,
            limit=1,
        )

        return pnl_records[0] if pnl_records else None

    async def calculate_total_revenue(
        self,
        exec_fees: Decimal,
        mev_tips: Decimal,
        vote_rewards: Decimal,
        commission: Decimal,
    ) -> Decimal:
        """Calculate total revenue from all components.

        This is a business logic method that can be extended with
        additional validation or transformations.

        Args:
            exec_fees: Execution fees in native units
            mev_tips: MEV tips in native units
            vote_rewards: Vote/block rewards in native units
            commission: Commission from delegators in native units

        Returns:
            Total revenue as sum of all components

        Raises:
            ValueError: If any component is negative
        """
        if any(val < 0 for val in [exec_fees, mev_tips, vote_rewards, commission]):
            raise ValueError("Revenue components cannot be negative")

        return exec_fees + mev_tips + vote_rewards + commission
