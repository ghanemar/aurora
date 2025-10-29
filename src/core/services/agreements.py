"""Agreement service with business logic.

This module provides the service layer for commission agreement operations,
implementing business logic and validation for agreement management.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.agreements import AgreementCreate, AgreementRuleCreate, AgreementUpdate
from src.core.models.computation import AgreementRules, Agreements, AgreementStatus
from src.repositories.agreements import AgreementRepository, AgreementRuleRepository


class AgreementService:
    """Service for agreement business logic.

    This service orchestrates agreement-related operations including
    CRUD operations with business rule validation and versioning.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize agreement service with database session.

        Args:
            session: The async database session
        """
        self.session = session
        self.agreement_repo = AgreementRepository(session)
        self.rule_repo = AgreementRuleRepository(session)

    async def create_agreement(self, agreement_data: AgreementCreate) -> Agreements:
        """Create a new agreement with validation.

        Args:
            agreement_data: Agreement creation data

        Returns:
            Created Agreement instance

        Raises:
            ValueError: If validation fails
        """
        # Validate effective dates
        if agreement_data.effective_until:
            if agreement_data.effective_until <= agreement_data.effective_from:
                raise ValueError("effective_until must be after effective_from")

        # Create agreement with initial version 1
        agreement = await self.agreement_repo.create(
            **agreement_data.model_dump(exclude={"status"}),
            current_version=1,
            status=agreement_data.status or AgreementStatus.DRAFT,
        )
        await self.session.commit()

        return agreement

    async def get_agreement(self, agreement_id: UUID) -> Agreements | None:
        """Get an agreement by ID.

        Args:
            agreement_id: Agreement UUID

        Returns:
            Agreement instance if found, None otherwise
        """
        return await self.agreement_repo.get(agreement_id)

    async def get_all_agreements(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        partner_id: UUID | None = None,
        status: AgreementStatus | None = None,
    ) -> list[Agreements]:
        """Get all agreements with optional filtering.

        Args:
            offset: Number of records to skip
            limit: Maximum number of records to return
            partner_id: Optional filter by partner
            status: Optional filter by status

        Returns:
            List of Agreement instances
        """
        filters = {}
        if partner_id:
            filters["partner_id"] = partner_id
        if status:
            filters["status"] = status

        if filters:
            return await self.agreement_repo.filter_by(
                **filters,
                offset=offset,
                limit=limit,
                order_by="created_at",
            )

        return await self.agreement_repo.get_all(
            offset=offset,
            limit=limit,
            order_by="created_at",
        )

    async def count_agreements(
        self,
        partner_id: UUID | None = None,
        status: AgreementStatus | None = None,
    ) -> int:
        """Count total agreements with optional filtering.

        Args:
            partner_id: Optional filter by partner
            status: Optional filter by status

        Returns:
            Count of matching agreements
        """
        filters = {}
        if partner_id:
            filters["partner_id"] = partner_id
        if status:
            filters["status"] = status

        return await self.agreement_repo.count(**filters)

    async def update_agreement(
        self,
        agreement_id: UUID,
        agreement_data: AgreementUpdate,
    ) -> Agreements:
        """Update an existing agreement with validation.

        Args:
            agreement_id: Agreement UUID
            agreement_data: Agreement update data

        Returns:
            Updated Agreement instance

        Raises:
            ValueError: If agreement not found or validation fails
        """
        # Check if agreement exists
        agreement = await self.agreement_repo.get(agreement_id)
        if not agreement:
            raise ValueError(f"Agreement with ID {agreement_id} not found")

        # Prepare update data (exclude None values for partial updates)
        update_data = agreement_data.model_dump(exclude_unset=True)

        # Validate effective dates if both are present
        effective_from = update_data.get("effective_from", agreement.effective_from)
        effective_until = update_data.get("effective_until", agreement.effective_until)

        if effective_until and effective_until <= effective_from:
            raise ValueError("effective_until must be after effective_from")

        # Update agreement
        updated_agreement = await self.agreement_repo.update(agreement_id, **update_data)
        if not updated_agreement:
            raise ValueError(f"Failed to update agreement with ID {agreement_id}")

        await self.session.commit()

        return updated_agreement

    async def activate_agreement(self, agreement_id: UUID) -> Agreements:
        """Activate an agreement (change status to ACTIVE).

        Args:
            agreement_id: Agreement UUID

        Returns:
            Updated Agreement instance

        Raises:
            ValueError: If agreement not found or cannot be activated
        """
        # Check if agreement exists
        agreement = await self.agreement_repo.get(agreement_id)
        if not agreement:
            raise ValueError(f"Agreement with ID {agreement_id} not found")

        # Only DRAFT agreements can be activated
        if agreement.status != AgreementStatus.DRAFT:
            raise ValueError(f"Cannot activate agreement with status {agreement.status.value}")

        # Check if agreement has at least one rule
        rules = await self.rule_repo.get_rules_by_agreement(agreement_id)
        if not rules:
            raise ValueError("Agreement must have at least one rule before activation")

        # Activate agreement
        updated = await self.agreement_repo.update(
            agreement_id,
            status=AgreementStatus.ACTIVE,
        )

        if not updated:
            raise ValueError(f"Failed to activate agreement with ID {agreement_id}")

        await self.session.commit()

        return updated

    async def deactivate_agreement(self, agreement_id: UUID) -> Agreements:
        """Deactivate an agreement (change status to INACTIVE).

        Args:
            agreement_id: Agreement UUID

        Returns:
            Updated Agreement instance

        Raises:
            ValueError: If agreement not found
        """
        # Check if agreement exists
        agreement = await self.agreement_repo.get(agreement_id)
        if not agreement:
            raise ValueError(f"Agreement with ID {agreement_id} not found")

        # Deactivate agreement
        updated = await self.agreement_repo.update(
            agreement_id,
            status=AgreementStatus.INACTIVE,
        )

        if not updated:
            raise ValueError(f"Failed to deactivate agreement with ID {agreement_id}")

        await self.session.commit()

        return updated

    async def add_rule(self, rule_data: AgreementRuleCreate) -> AgreementRules:
        """Add a commission rule to an agreement.

        Args:
            rule_data: Rule creation data

        Returns:
            Created AgreementRule instance

        Raises:
            ValueError: If validation fails
        """
        # Check if agreement exists
        agreement = await self.agreement_repo.get(rule_data.agreement_id)
        if not agreement:
            raise ValueError(f"Agreement with ID {rule_data.agreement_id} not found")

        # Only add rules to DRAFT or ACTIVE agreements
        if agreement.status not in [AgreementStatus.DRAFT, AgreementStatus.ACTIVE]:
            raise ValueError(f"Cannot add rules to agreement with status {agreement.status.value}")

        # Create rule
        rule = await self.rule_repo.create(
            **rule_data.model_dump(),
            is_active=True,
        )
        await self.session.commit()

        return rule

    async def get_agreement_rules(self, agreement_id: UUID) -> list[AgreementRules]:
        """Get all rules for an agreement.

        Args:
            agreement_id: Agreement UUID

        Returns:
            List of AgreementRule instances
        """
        return await self.rule_repo.get_rules_by_agreement(agreement_id)

    async def get_active_rules(
        self,
        agreement_id: UUID,
        version_number: int | None = None,
    ) -> list[AgreementRules]:
        """Get active rules for an agreement version.

        Args:
            agreement_id: Agreement UUID
            version_number: Optional version number (defaults to current)

        Returns:
            List of active AgreementRule instances

        Raises:
            ValueError: If agreement not found
        """
        # Check if agreement exists
        agreement = await self.agreement_repo.get(agreement_id)
        if not agreement:
            raise ValueError(f"Agreement with ID {agreement_id} not found")

        # Use current version if not specified
        if version_number is None:
            version_number = agreement.current_version

        return await self.rule_repo.get_active_rules(agreement_id, version_number)
