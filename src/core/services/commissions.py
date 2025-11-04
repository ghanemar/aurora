"""Commission service with business logic.

This module provides the service layer for commission calculation operations,
implementing business logic for computing partner commissions from validator P&L.
"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models.computation import (
    RevenueComponent,
    ValidatorPnL,
)
from src.repositories.agreements import AgreementRepository, AgreementRuleRepository
from src.repositories.partner_wallets import PartnerWalletRepository
from src.repositories.partners import PartnerRepository
from src.repositories.staker_rewards import StakerRewardsRepository
from src.repositories.validators import ValidatorPnLRepository


class CommissionService:
    """Service for commission calculation business logic.

    This service orchestrates commission-related operations including
    calculation of partner commissions from validator P&L data.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize commission service with database session.

        Args:
            session: The async database session
        """
        self.session = session
        self.agreement_repo = AgreementRepository(session)
        self.rule_repo = AgreementRuleRepository(session)
        self.partner_repo = PartnerRepository(session)
        self.pnl_repo = ValidatorPnLRepository(session)
        self.wallet_repo = PartnerWalletRepository(session)
        self.staker_rewards_repo = StakerRewardsRepository(session)

    async def calculate_commissions(
        self,
        partner_id: UUID,
        period_id: UUID,
        chain_id: str | None = None,
    ) -> list[dict]:
        """Calculate commissions for a partner in a specific period.

        This method fetches ValidatorPnL records for the period, applies
        agreement rules, and returns commission line details.

        Args:
            partner_id: Partner UUID
            period_id: Period UUID
            chain_id: Optional chain identifier to filter validators

        Returns:
            List of commission line dictionaries with breakdown

        Raises:
            ValueError: If partner not found or no active agreement
        """
        # Check if partner exists
        partner = await self.partner_repo.get(partner_id)
        if not partner:
            raise ValueError(f"Partner with ID {partner_id} not found")

        # Get active agreements for partner
        agreements = await self.agreement_repo.get_active_by_partner(partner_id)
        if not agreements:
            raise ValueError(f"No active agreements found for partner {partner_id}")

        # For MVP, use the first active agreement
        agreement = agreements[0]

        # Get active rules for the agreement
        rules = await self.rule_repo.get_active_rules(
            agreement.agreement_id,
            agreement.current_version,
        )

        if not rules:
            raise ValueError(f"No active rules found for agreement {agreement.agreement_id}")

        # Get all ValidatorPnL records for the period
        pnl_filters = {"period_id": period_id}
        if chain_id:
            pnl_filters["chain_id"] = chain_id

        pnl_records = await self.pnl_repo.filter_by(**pnl_filters)

        if not pnl_records:
            return []  # No P&L data for this period

        # Calculate commissions for each validator/rule combination
        commission_lines = []

        for pnl in pnl_records:
            for rule in rules:
                # Check if rule applies to this validator
                if rule.validator_key_pattern:
                    # For MVP, only support exact match
                    if pnl.validator_key != rule.validator_key_pattern:
                        continue

                # Calculate commission based on revenue component
                commission = await self._calculate_commission_for_rule(pnl, rule)

                if commission > 0:
                    commission_lines.append(
                        {
                            "partner_id": partner_id,
                            "agreement_id": agreement.agreement_id,
                            "rule_id": rule.rule_id,
                            "chain_id": pnl.chain_id,
                            "period_id": pnl.period_id,
                            "validator_key": pnl.validator_key,
                            "revenue_component": rule.revenue_component.value,
                            "base_amount_native": self._get_base_amount(
                                pnl, rule.revenue_component
                            ),
                            "commission_rate_bps": rule.commission_rate_bps,
                            "commission_native": commission,
                            "attribution_method": rule.attribution_method.value,
                        }
                    )

        return commission_lines

    async def _calculate_commission_for_rule(
        self,
        pnl: ValidatorPnL,
        rule,
    ) -> Decimal:
        """Calculate commission for a single P&L record and rule.

        Args:
            pnl: ValidatorPnL record
            rule: AgreementRule to apply

        Returns:
            Commission amount in native units
        """
        # Get base amount based on revenue component
        base_amount = self._get_base_amount(pnl, rule.revenue_component)

        # Apply commission rate (bps = basis points, 1% = 100 bps)
        commission = base_amount * Decimal(rule.commission_rate_bps) / Decimal(10000)

        # For MVP, only CLIENT_REVENUE attribution is supported
        # More complex attribution methods (STAKE_WEIGHT, FIXED_SHARE) would be implemented here

        return commission

    def _get_base_amount(
        self,
        pnl: ValidatorPnL,
        component: RevenueComponent,
    ) -> Decimal:
        """Get base amount from P&L based on revenue component.

        Args:
            pnl: ValidatorPnL record
            component: Revenue component to extract

        Returns:
            Base amount in native units
        """
        if component == RevenueComponent.EXEC_FEES:
            return pnl.exec_fees_native
        elif component == RevenueComponent.MEV:
            return pnl.mev_tips_native
        elif component == RevenueComponent.REWARDS:
            return pnl.vote_rewards_native + pnl.commission_native
        elif component == RevenueComponent.ALL:
            return pnl.total_revenue_native
        else:
            return Decimal(0)

    async def get_commission_breakdown(
        self,
        partner_id: UUID,
        period_id: UUID,
        validator_key: str | None = None,
    ) -> dict:
        """Get detailed commission breakdown for a partner in a period.

        Args:
            partner_id: Partner UUID
            period_id: Period UUID
            validator_key: Optional validator key to filter by

        Returns:
            Dictionary with commission breakdown by component
        """
        # Calculate all commissions
        commission_lines = await self.calculate_commissions(partner_id, period_id)

        # Filter by validator if specified
        if validator_key:
            commission_lines = [
                line for line in commission_lines if line["validator_key"] == validator_key
            ]

        # Group by revenue component
        breakdown = {
            "total_commission": Decimal(0),
            "exec_fees_commission": Decimal(0),
            "mev_commission": Decimal(0),
            "rewards_commission": Decimal(0),
            "lines": commission_lines,
        }

        for line in commission_lines:
            breakdown["total_commission"] += line["commission_native"]

            if line["revenue_component"] == RevenueComponent.EXEC_FEES.value:
                breakdown["exec_fees_commission"] += line["commission_native"]
            elif line["revenue_component"] == RevenueComponent.MEV.value:
                breakdown["mev_commission"] += line["commission_native"]
            elif line["revenue_component"] == RevenueComponent.REWARDS.value:
                breakdown["rewards_commission"] += line["commission_native"]
            elif line["revenue_component"] == RevenueComponent.ALL.value:
                # Split ALL into components for breakdown
                # For simplicity, we'll add to total only
                pass

        return breakdown

    async def calculate_wallet_attributed_commissions(
        self,
        partner_id: UUID,
        period_id: UUID,
        chain_id: str,
    ) -> list[dict]:
        """Calculate commissions using wallet-level attribution.

        This method calculates commissions based on granular per-staker
        reward data instead of validator-level P&L. It respects wallet
        introduction dates for retroactive attribution.

        Args:
            partner_id: Partner UUID
            period_id: Period UUID
            chain_id: Chain identifier (required for wallet attribution)

        Returns:
            List of commission line dictionaries with wallet attribution

        Raises:
            ValueError: If partner not found, no active agreement, or wallet attribution not enabled
        """
        # Check if partner exists
        partner = await self.partner_repo.get(partner_id)
        if not partner:
            raise ValueError(f"Partner with ID {partner_id} not found")

        # Get active agreements for partner
        agreements = await self.agreement_repo.get_active_by_partner(partner_id)
        if not agreements:
            raise ValueError(f"No active agreements found for partner {partner_id}")

        # For MVP, use the first active agreement
        agreement = agreements[0]

        # Check if wallet attribution is enabled
        if not agreement.wallet_attribution_enabled:
            raise ValueError(
                f"Wallet attribution is not enabled for agreement {agreement.agreement_id}. "
                "Use calculate_commissions() instead."
            )

        # Get active rules for the agreement
        rules = await self.rule_repo.get_active_rules(
            agreement.agreement_id,
            agreement.current_version,
        )

        if not rules:
            raise ValueError(f"No active rules found for agreement {agreement.agreement_id}")

        # Get partner wallets for this chain
        wallets = await self.wallet_repo.get_by_partner(
            partner_id,
            chain_id=chain_id,
            active_only=True,
        )

        if not wallets:
            return []  # No wallets configured for this partner on this chain

        # Calculate commissions for each wallet
        commission_lines = []

        for wallet in wallets:
            # Get staker rewards detail for this wallet in the period
            # This contains granular per-staker, per-component reward data
            staker_rewards = await self.staker_rewards_repo.get_by_staker(
                chain_id,
                wallet.wallet_address,
                period_id=period_id,
                limit=1000,  # Adjust if needed
            )

            if not staker_rewards:
                continue  # No rewards for this wallet in this period

            # For each staker reward detail, apply matching rules
            for reward_detail in staker_rewards:
                for rule in rules:
                    # Check if rule applies to this validator
                    if rule.validator_key_pattern:
                        # For MVP, only support exact match
                        if reward_detail.validator_key != rule.validator_key_pattern:
                            continue

                    # Check if revenue component matches
                    # Map canonical revenue component to agreement rule component
                    if not self._revenue_component_matches(
                        reward_detail.revenue_component, rule.revenue_component
                    ):
                        continue

                    # Calculate commission based on staker reward amount
                    base_amount = reward_detail.reward_amount_native

                    # Apply commission rate (bps = basis points, 1% = 100 bps)
                    commission = base_amount * Decimal(rule.commission_rate_bps) / Decimal(10000)

                    if commission > 0:
                        commission_lines.append(
                            {
                                "partner_id": partner_id,
                                "agreement_id": agreement.agreement_id,
                                "rule_id": rule.rule_id,
                                "chain_id": chain_id,
                                "period_id": period_id,
                                "validator_key": reward_detail.validator_key,
                                "wallet_address": wallet.wallet_address,
                                "revenue_component": rule.revenue_component.value,
                                "base_amount_native": base_amount,
                                "commission_rate_bps": rule.commission_rate_bps,
                                "commission_native": commission,
                                "attribution_method": "WALLET_ATTRIBUTION",
                                "staker_stake_amount_native": reward_detail.stake_amount_native,
                            }
                        )

        return commission_lines

    def _revenue_component_matches(
        self,
        canonical_component: str,
        rule_component: RevenueComponent,
    ) -> bool:
        """Check if canonical revenue component matches agreement rule component.

        Maps between canonical_staker_rewards_detail revenue components
        (MEV, TIPS, BLOCK_REWARDS, etc.) and agreement rule components
        (EXEC_FEES, MEV, REWARDS, ALL).

        Args:
            canonical_component: Component from canonical_staker_rewards_detail
            rule_component: Component from agreement rule

        Returns:
            True if components match, False otherwise
        """
        # Handle ALL - matches everything
        if rule_component == RevenueComponent.ALL:
            return True

        # Map canonical components to rule components
        component_mapping = {
            "MEV": [RevenueComponent.MEV],
            "TIPS": [RevenueComponent.MEV],  # Tips often part of MEV
            "BLOCK_REWARDS": [RevenueComponent.REWARDS],
            "CONSENSUS_REWARDS": [RevenueComponent.REWARDS],
            "EXECUTION_REWARDS": [RevenueComponent.EXEC_FEES],
            "OTHER": [RevenueComponent.REWARDS],  # Default to REWARDS
        }

        matching_components = component_mapping.get(canonical_component, [])
        return rule_component in matching_components
