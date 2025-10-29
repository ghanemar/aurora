"""Partner service with business logic.

This module provides the service layer for partner-related operations,
implementing business logic and validation for partner management.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.partners import PartnerCreate, PartnerUpdate
from src.core.models.computation import Partners
from src.repositories.partners import PartnerRepository


class PartnerService:
    """Service for partner business logic.

    This service orchestrates partner-related operations including
    CRUD operations with business rule validation.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize partner service with database session.

        Args:
            session: The async database session
        """
        self.session = session
        self.partner_repo = PartnerRepository(session)

    async def create_partner(self, partner_data: PartnerCreate) -> Partners:
        """Create a new partner with validation.

        Args:
            partner_data: Partner creation data

        Returns:
            Created Partner instance

        Raises:
            ValueError: If validation fails
        """
        # Check for duplicate partner name
        existing = await self.partner_repo.get_by_name(partner_data.partner_name)
        if existing:
            raise ValueError(f"Partner with name '{partner_data.partner_name}' already exists")

        # Check for duplicate email
        existing_email = await self.partner_repo.filter_by(
            contact_email=partner_data.contact_email,
            limit=1,
        )
        if existing_email:
            raise ValueError(f"Partner with email '{partner_data.contact_email}' already exists")

        # Create partner
        partner = await self.partner_repo.create(**partner_data.model_dump())
        await self.session.commit()

        return partner

    async def get_partner(self, partner_id: UUID) -> Partners | None:
        """Get a partner by ID.

        Args:
            partner_id: Partner UUID

        Returns:
            Partner instance if found, None otherwise
        """
        return await self.partner_repo.get(partner_id)

    async def get_all_partners(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        is_active: bool | None = None,
    ) -> list[Partners]:
        """Get all partners with optional filtering.

        Args:
            offset: Number of records to skip
            limit: Maximum number of records to return
            is_active: Optional filter by active status

        Returns:
            List of Partner instances
        """
        if is_active is not None:
            return await self.partner_repo.filter_by(
                is_active=is_active,
                offset=offset,
                limit=limit,
                order_by="partner_name",
            )

        return await self.partner_repo.get_all(
            offset=offset,
            limit=limit,
            order_by="partner_name",
        )

    async def count_partners(self, is_active: bool | None = None) -> int:
        """Count total partners with optional filtering.

        Args:
            is_active: Optional filter by active status

        Returns:
            Count of matching partners
        """
        filters = {}
        if is_active is not None:
            filters["is_active"] = is_active

        return await self.partner_repo.count(**filters)

    async def update_partner(
        self,
        partner_id: UUID,
        partner_data: PartnerUpdate,
    ) -> Partners:
        """Update an existing partner with validation.

        Args:
            partner_id: Partner UUID
            partner_data: Partner update data

        Returns:
            Updated Partner instance

        Raises:
            ValueError: If partner not found or validation fails
        """
        # Check if partner exists
        partner = await self.partner_repo.get(partner_id)
        if not partner:
            raise ValueError(f"Partner with ID {partner_id} not found")

        # Prepare update data (exclude None values for partial updates)
        update_data = partner_data.model_dump(exclude_unset=True)

        # Check for duplicate name if name is being updated
        if "partner_name" in update_data:
            existing = await self.partner_repo.get_by_name(update_data["partner_name"])
            if existing and existing.partner_id != partner_id:
                raise ValueError(
                    f"Partner with name '{update_data['partner_name']}' already exists"
                )

        # Check for duplicate email if email is being updated
        if "contact_email" in update_data:
            existing_email = await self.partner_repo.filter_by(
                contact_email=update_data["contact_email"],
                limit=1,
            )
            if existing_email and existing_email[0].partner_id != partner_id:
                raise ValueError(
                    f"Partner with email '{update_data['contact_email']}' already exists"
                )

        # Update partner
        updated_partner = await self.partner_repo.update(partner_id, **update_data)
        if not updated_partner:
            raise ValueError(f"Failed to update partner with ID {partner_id}")

        await self.session.commit()

        return updated_partner

    async def delete_partner(self, partner_id: UUID) -> bool:
        """Soft delete a partner (set is_active = False).

        Args:
            partner_id: Partner UUID

        Returns:
            True if partner was deactivated, False if not found

        Raises:
            ValueError: If partner has active agreements
        """
        # Check if partner exists
        partner = await self.partner_repo.get(partner_id)
        if not partner:
            return False

        # Check for active agreements (would be handled by AgreementService)
        # For now, we'll just set is_active to False
        updated = await self.partner_repo.update(partner_id, is_active=False)

        if updated:
            await self.session.commit()
            return True

        return False
