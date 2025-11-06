"""Validator service with business logic.

This module provides the service layer for validator-related operations,
implementing business logic and validation for validator P&L management.
"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models.chains import Validator
from src.core.models.computation import ValidatorPnL
from src.repositories.validators import ValidatorPnLRepository, ValidatorRegistryRepository


class ValidatorService:
    """Service for validator business logic.

    This service orchestrates validator-related operations including
    P&L retrieval, calculation management, and validator registry operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize validator service with database session.

        Args:
            session: The async database session
        """
        self.session = session
        self.pnl_repo = ValidatorPnLRepository(session)
        self.registry_repo = ValidatorRegistryRepository(session)

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


    async def get_validator_stats(self) -> dict:
        """Get validator statistics grouped by chain.

        Returns:
            Dictionary with total count and counts per chain
            Format: {
                "total": int,
                "chains": {
                    "chain_id_1": count,
                    "chain_id_2": count,
                    ...
                }
            }
        """
        from sqlalchemy import func, select
        from src.core.models.chains import Validator

        # Query to count active validators per chain from validators registry
        stmt = (
            select(
                Validator.chain_id,
                func.count(Validator.validator_key).label("count"),
            )
            .where(Validator.is_active == True)
            .group_by(Validator.chain_id)
        )

        result = await self.session.execute(stmt)
        chain_stats = {row.chain_id: row.count for row in result.fetchall()}

        total = sum(chain_stats.values())

        return {
            "total": total,
            "chains": chain_stats,
        }


    # Validator Registry Methods

    async def get_all_validators_registry(
        self,
        chain_id: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Validator]:
        """Get all validators from the registry with optional chain filter.

        Args:
            chain_id: Optional chain identifier filter
            offset: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Validator instances
        """
        if chain_id:
            return await self.registry_repo.get_by_chain(chain_id, offset=offset, limit=limit)
        else:
            return await self.registry_repo.get_all(offset=offset, limit=limit)

    async def count_validators_registry(self, chain_id: str | None = None) -> int:
        """Count total validators in the registry with optional chain filter.

        Args:
            chain_id: Optional chain identifier filter

        Returns:
            Total count of validators
        """
        if chain_id:
            filters = {"chain_id": chain_id}
            return await self.registry_repo.count(**filters)
        else:
            return await self.registry_repo.count()

    async def get_validator_by_key_and_chain(
        self,
        validator_key: str,
        chain_id: str,
    ) -> Validator | None:
        """Get validator from registry by composite key.

        Args:
            validator_key: Validator identifier
            chain_id: Chain identifier

        Returns:
            Validator instance if found, None otherwise
        """
        return await self.registry_repo.get_by_key_and_chain(validator_key, chain_id)

    async def create_validator(
        self,
        validator_key: str,
        chain_id: str,
        description: str | None = None,
    ) -> Validator:
        """Create a new validator in the registry.

        Args:
            validator_key: Validator identifier
            chain_id: Chain identifier
            description: Optional description

        Returns:
            Created Validator instance

        Raises:
            ValueError: If validator already exists
        """
        # Check if validator already exists
        existing = await self.registry_repo.get_by_key_and_chain(validator_key, chain_id)
        if existing:
            raise ValueError(
                f"Validator {validator_key} already exists for chain {chain_id}"
            )

        # Create new validator
        validator_data = {
            "validator_key": validator_key,
            "chain_id": chain_id,
            "description": description,
            "is_active": True,
        }

        validator = await self.registry_repo.create(**validator_data)
        return validator

    async def update_validator(
        self,
        validator_key: str,
        chain_id: str,
        description: str | None = None,
        is_active: bool | None = None,
    ) -> Validator | None:
        """Update an existing validator in the registry.

        Args:
            validator_key: Validator identifier
            chain_id: Chain identifier
            description: Optional new description
            is_active: Optional new active status

        Returns:
            Updated Validator instance if found, None otherwise
        """
        update_data = {}
        if description is not None:
            update_data["description"] = description
        if is_active is not None:
            update_data["is_active"] = is_active

        if not update_data:
            # No updates provided, just return existing
            return await self.registry_repo.get_by_key_and_chain(validator_key, chain_id)

        return await self.registry_repo.update_by_composite_key(
            validator_key, chain_id, update_data
        )

    async def delete_validator(
        self,
        validator_key: str,
        chain_id: str,
    ) -> bool:
        """Delete a validator from the registry.

        Args:
            validator_key: Validator identifier
            chain_id: Chain identifier

        Returns:
            True if deleted, False if not found
        """
        return await self.registry_repo.delete_by_composite_key(validator_key, chain_id)
