"""Partner wallets service with business logic.

This module provides the service layer for partner wallet operations,
implementing business logic for wallet attribution, CSV imports, and validation.
"""

import csv
import datetime
import io
from typing import BinaryIO
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models.computation import PartnerWallet
from src.repositories.partner_wallets import PartnerWalletRepository
from src.repositories.partners import PartnerRepository
from src.repositories.stake_events import StakeEventRepository


class PartnerWalletService:
    """Service for partner wallet business logic.

    This service orchestrates partner wallet operations including
    CSV imports, validation, and wallet attribution management.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize partner wallet service with database session.

        Args:
            session: The async database session
        """
        self.session = session
        self.wallet_repo = PartnerWalletRepository(session)
        self.partner_repo = PartnerRepository(session)
        self.stake_event_repo = StakeEventRepository(session)

    async def create_wallet(
        self,
        partner_id: UUID,
        chain_id: str,
        wallet_address: str,
        introduced_date: datetime.date,
        notes: str | None = None,
    ) -> PartnerWallet:
        """Create a new partner wallet with validation.

        Args:
            partner_id: Partner UUID
            chain_id: Chain identifier
            wallet_address: Wallet address
            introduced_date: Date wallet was introduced by partner
            notes: Optional notes about this wallet

        Returns:
            Created PartnerWallet instance

        Raises:
            ValueError: If validation fails or wallet already exists
        """
        # Validate partner exists
        partner = await self.partner_repo.get(partner_id)
        if not partner:
            raise ValueError(f"Partner with ID {partner_id} not found")

        if not partner.is_active:
            raise ValueError(f"Partner {partner.partner_name} is not active")

        # Check for duplicate wallet
        existing = await self.wallet_repo.get_by_address(chain_id, wallet_address)
        if existing:
            if existing.partner_id == partner_id:
                raise ValueError(
                    f"Wallet {wallet_address} already registered to this partner on {chain_id}"
                )
            else:
                other_partner = await self.partner_repo.get(existing.partner_id)
                raise ValueError(
                    f"Wallet {wallet_address} already registered to partner "
                    f"'{other_partner.partner_name if other_partner else 'Unknown'}' on {chain_id}"
                )

        # Create wallet
        wallet = await self.wallet_repo.create(
            partner_id=partner_id,
            chain_id=chain_id,
            wallet_address=wallet_address,
            introduced_date=introduced_date,
            is_active=True,
            notes=notes,
        )

        await self.session.commit()
        return wallet

    async def import_wallets_from_csv(
        self,
        partner_id: UUID,
        csv_file: BinaryIO,
        skip_duplicates: bool = False,
    ) -> dict:
        """Import partner wallets from CSV file.

        Expected CSV format:
        chain_id,wallet_address,introduced_date,notes
        solana,ABC123...,2024-01-15,Optional note

        Args:
            partner_id: Partner UUID
            csv_file: Binary file object containing CSV data
            skip_duplicates: If True, skip duplicate wallets; if False, raise error

        Returns:
            Dictionary with import results: {
                "success": int,
                "skipped": int,
                "errors": list[dict]
            }

        Raises:
            ValueError: If partner not found or CSV format invalid
        """
        # Validate partner exists
        partner = await self.partner_repo.get(partner_id)
        if not partner:
            raise ValueError(f"Partner with ID {partner_id} not found")

        if not partner.is_active:
            raise ValueError(f"Partner {partner.partner_name} is not active")

        # Parse CSV
        content = csv_file.read().decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(content))

        # Validate CSV headers
        required_headers = {"chain_id", "wallet_address", "introduced_date"}
        if not required_headers.issubset(set(csv_reader.fieldnames or [])):
            raise ValueError(
                f"CSV must contain headers: {', '.join(required_headers)}"
            )

        results = {"success": 0, "skipped": 0, "errors": []}
        wallets_to_create = []

        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (header is 1)
            try:
                # Parse and validate row data
                chain_id = row["chain_id"].strip()
                wallet_address = row["wallet_address"].strip()
                introduced_date_str = row["introduced_date"].strip()
                notes = row.get("notes", "").strip() or None

                if not chain_id or not wallet_address or not introduced_date_str:
                    results["errors"].append(
                        {
                            "row": row_num,
                            "error": "Missing required fields",
                            "data": row,
                        }
                    )
                    continue

                # Parse date
                try:
                    introduced_date = datetime.datetime.strptime(
                        introduced_date_str, "%Y-%m-%d"
                    ).date()
                except ValueError:
                    results["errors"].append(
                        {
                            "row": row_num,
                            "error": f"Invalid date format '{introduced_date_str}' (expected YYYY-MM-DD)",
                            "data": row,
                        }
                    )
                    continue

                # Check for duplicate
                existing = await self.wallet_repo.get_by_address(
                    chain_id, wallet_address
                )
                if existing:
                    if skip_duplicates:
                        results["skipped"] += 1
                        continue
                    else:
                        other_partner = await self.partner_repo.get(
                            existing.partner_id
                        )
                        results["errors"].append(
                            {
                                "row": row_num,
                                "error": f"Wallet already registered to partner '{other_partner.partner_name if other_partner else 'Unknown'}'",
                                "data": row,
                            }
                        )
                        continue

                # Add to batch creation list
                wallets_to_create.append(
                    {
                        "partner_id": partner_id,
                        "chain_id": chain_id,
                        "wallet_address": wallet_address,
                        "introduced_date": introduced_date,
                        "is_active": True,
                        "notes": notes,
                    }
                )

            except Exception as e:
                results["errors"].append(
                    {"row": row_num, "error": str(e), "data": row}
                )

        # Bulk create wallets
        if wallets_to_create:
            try:
                await self.wallet_repo.bulk_create(wallets_to_create)
                await self.session.commit()
                results["success"] = len(wallets_to_create)
            except Exception as e:
                await self.session.rollback()
                raise ValueError(f"Failed to create wallets: {str(e)}") from e

        return results

    async def get_wallet(self, wallet_id: UUID) -> PartnerWallet | None:
        """Get a partner wallet by ID.

        Args:
            wallet_id: Wallet UUID

        Returns:
            PartnerWallet instance if found, None otherwise
        """
        return await self.wallet_repo.get(wallet_id)

    async def get_wallets_by_partner(
        self,
        partner_id: UUID,
        *,
        chain_id: str | None = None,
        active_only: bool = True,
        offset: int = 0,
        limit: int = 100,
    ) -> list[PartnerWallet]:
        """Get all wallets for a specific partner.

        Args:
            partner_id: Partner UUID
            chain_id: Optional chain filter
            active_only: Only include active wallets
            offset: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of PartnerWallet instances
        """
        return await self.wallet_repo.get_by_partner(
            partner_id,
            chain_id=chain_id,
            active_only=active_only,
            offset=offset,
            limit=limit,
        )

    async def deactivate_wallet(self, wallet_id: UUID) -> PartnerWallet | None:
        """Deactivate a partner wallet (soft delete).

        Args:
            wallet_id: Wallet UUID

        Returns:
            Updated PartnerWallet instance if found, None otherwise
        """
        wallet = await self.wallet_repo.deactivate(wallet_id)
        if wallet:
            await self.session.commit()
        return wallet

    async def validate_wallet_stake_history(
        self, chain_id: str, wallet_address: str
    ) -> dict:
        """Validate wallet has staking history on the chain.

        This helps verify that the wallet address is valid and has
        actually staked with a validator.

        Args:
            chain_id: Chain identifier
            wallet_address: Wallet address to validate

        Returns:
            Dictionary with validation results: {
                "valid": bool,
                "stake_events_count": int,
                "first_stake_date": datetime | None,
                "last_stake_date": datetime | None
            }
        """
        # Get stake events for this wallet
        stake_events = await self.stake_event_repo.get_by_staker(
            chain_id, wallet_address, limit=1000
        )

        if not stake_events:
            return {
                "valid": False,
                "stake_events_count": 0,
                "first_stake_date": None,
                "last_stake_date": None,
            }

        # Sort by timestamp
        sorted_events = sorted(stake_events, key=lambda e: e.event_timestamp)

        return {
            "valid": True,
            "stake_events_count": len(stake_events),
            "first_stake_date": sorted_events[0].event_timestamp,
            "last_stake_date": sorted_events[-1].event_timestamp,
        }

    async def get_wallet_attribution_report(
        self, partner_id: UUID, chain_id: str, period_id: UUID
    ) -> dict:
        """Generate wallet attribution report for a partner.

        This report shows which wallets were active during the period
        and their staking activity.

        Args:
            partner_id: Partner UUID
            chain_id: Chain identifier
            period_id: Period UUID

        Returns:
            Dictionary with attribution report
        """
        # Get partner wallets for this chain
        wallets = await self.wallet_repo.get_by_partner(
            partner_id, chain_id=chain_id, active_only=True
        )

        report = {
            "partner_id": str(partner_id),
            "chain_id": chain_id,
            "period_id": str(period_id),
            "total_wallets": len(wallets),
            "wallets": [],
        }

        for wallet in wallets:
            # Get stake events for this wallet in the period
            stake_events = await self.stake_event_repo.get_by_staker(
                chain_id, wallet.wallet_address, limit=1000
            )

            # Filter events by period (simplified - would need period date range)
            wallet_data = {
                "wallet_id": str(wallet.wallet_id),
                "wallet_address": wallet.wallet_address,
                "introduced_date": wallet.introduced_date.isoformat(),
                "stake_events_count": len(stake_events),
                "is_active": wallet.is_active,
            }

            report["wallets"].append(wallet_data)

        return report

    async def count_wallets_by_partner(
        self, partner_id: UUID, *, active_only: bool = True
    ) -> int:
        """Count wallets for a specific partner.

        Args:
            partner_id: Partner UUID
            active_only: Only count active wallets

        Returns:
            Count of partner wallets
        """
        return await self.wallet_repo.count_by_partner(
            partner_id, active_only=active_only
        )
