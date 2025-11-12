"""Commission calculation service for partner rewards.

This service calculates partner commissions based on withdrawer wallet attribution
and stake-weighted reward distribution for the GlobalStake validator sample data.

Key Concepts:
    - Withdrawer-Based Attribution: Commissions are attributed to the partner who
      introduced the withdrawer wallet (economic beneficiary)
    - Stake-Weighted Distribution: Rewards are proportional to stake amount
    - Continuous Epoch Ranges: Only accepts continuous epoch sequences (e.g., 800-805)
    - Deterministic Calculations: Same inputs always produce same outputs

Example:
    >>> calculator = CommissionCalculator(session)
    >>> result = await calculator.calculate_partner_commission(
    ...     partner_id=partner_id,
    ...     start_epoch=800,
    ...     end_epoch=805
    ... )
    >>> print(f"Commission: {result['total_commission_lamports'] / 1e9:.2f} SOL")
"""

from decimal import Decimal
from typing import TypedDict
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import Partners, PartnerWallet
from src.core.models.sample_data import (
    SampleEpochReward,
    SampleStakeAccount,
    SampleValidatorEpochSummary,
)


class EpochCommissionDetail(TypedDict):
    """Commission details for a single epoch."""

    epoch: int
    total_active_stake_lamports: int
    partner_stake_lamports: int
    stake_percentage: Decimal
    total_staker_rewards_lamports: int
    partner_rewards_lamports: int
    commission_rate: Decimal
    partner_commission_lamports: int


class CommissionCalculationResult(TypedDict):
    """Result of commission calculation for a partner across epochs."""

    partner_id: UUID
    partner_name: str
    start_epoch: int
    end_epoch: int
    epoch_count: int
    total_partner_stake_lamports: int
    total_partner_rewards_lamports: int
    commission_rate: Decimal
    total_commission_lamports: int
    epoch_details: list[EpochCommissionDetail]


class CommissionCalculator:
    """Calculates partner commissions based on stake-weighted reward distribution."""

    def __init__(self, session: AsyncSession):
        """Initialize the commission calculator.

        Args:
            session: Database session for queries
        """
        self.session = session

    async def calculate_partner_commission(
        self,
        partner_id: UUID,
        start_epoch: int,
        end_epoch: int,
        commission_rate: Decimal = Decimal("0.10"),  # 10% default commission rate
    ) -> CommissionCalculationResult:
        """Calculate commission for a partner across an epoch range.

        This method:
        1. Validates epoch range is continuous
        2. Calculates partner's stake per epoch (via withdrawer wallets)
        3. Calculates proportional rewards for partner's stake
        4. Applies commission rate to partner's rewards

        Args:
            partner_id: UUID of partner to calculate commission for
            start_epoch: First epoch in range (inclusive)
            end_epoch: Last epoch in range (inclusive)
            commission_rate: Commission rate as decimal (0.10 = 10%)

        Returns:
            Commission calculation result with per-epoch details

        Raises:
            ValueError: If epoch range is invalid or discontinuous
        """
        # Validate epoch range
        if start_epoch > end_epoch:
            raise ValueError(
                f"Start epoch ({start_epoch}) must be <= end epoch ({end_epoch})"
            )

        # Get partner details
        result = await self.session.execute(
            select(Partners).where(Partners.partner_id == partner_id)
        )
        partner = result.scalar_one_or_none()
        if not partner:
            raise ValueError(f"Partner not found: {partner_id}")

        # Get all epochs in range to ensure continuity
        result = await self.session.execute(
            select(SampleValidatorEpochSummary)
            .where(
                SampleValidatorEpochSummary.epoch >= start_epoch,
                SampleValidatorEpochSummary.epoch <= end_epoch,
            )
            .order_by(SampleValidatorEpochSummary.epoch)
        )
        epoch_summaries = result.scalars().all()

        # Validate continuity
        epochs_in_db = [summary.epoch for summary in epoch_summaries]
        expected_epochs = list(range(start_epoch, end_epoch + 1))
        if epochs_in_db != expected_epochs:
            raise ValueError(
                f"Epoch range {start_epoch}-{end_epoch} is not continuous. "
                f"Available epochs: {epochs_in_db}"
            )

        # Calculate commission for each epoch
        epoch_details: list[EpochCommissionDetail] = []
        total_partner_stake = 0
        total_partner_rewards = 0
        total_commission = 0

        for summary in epoch_summaries:
            # Get epoch rewards
            result = await self.session.execute(
                select(SampleEpochReward).where(
                    SampleEpochReward.epoch == summary.epoch
                )
            )
            epoch_reward = result.scalar_one_or_none()
            if not epoch_reward:
                raise ValueError(f"Epoch rewards not found for epoch {summary.epoch}")

            # Calculate partner's stake for this epoch
            partner_stake = await self._calculate_partner_stake_for_epoch(
                partner_id=partner_id, epoch=summary.epoch
            )

            # Calculate stake percentage
            stake_percentage = Decimal("0")
            if summary.total_active_stake_lamports > 0:
                stake_percentage = (
                    Decimal(str(partner_stake))
                    / Decimal(str(summary.total_active_stake_lamports))
                )

            # Calculate partner's proportional rewards
            partner_rewards = int(
                Decimal(str(epoch_reward.staker_rewards_lamports)) * stake_percentage
            )

            # Calculate commission
            partner_commission = int(Decimal(str(partner_rewards)) * commission_rate)

            # Accumulate totals
            total_partner_stake += partner_stake
            total_partner_rewards += partner_rewards
            total_commission += partner_commission

            # Store epoch details
            epoch_details.append(
                EpochCommissionDetail(
                    epoch=summary.epoch,
                    total_active_stake_lamports=summary.total_active_stake_lamports,
                    partner_stake_lamports=partner_stake,
                    stake_percentage=stake_percentage,
                    total_staker_rewards_lamports=epoch_reward.staker_rewards_lamports,
                    partner_rewards_lamports=partner_rewards,
                    commission_rate=commission_rate,
                    partner_commission_lamports=partner_commission,
                )
            )

        return CommissionCalculationResult(
            partner_id=partner_id,
            partner_name=partner.partner_name,
            start_epoch=start_epoch,
            end_epoch=end_epoch,
            epoch_count=len(epoch_details),
            total_partner_stake_lamports=total_partner_stake,
            total_partner_rewards_lamports=total_partner_rewards,
            commission_rate=commission_rate,
            total_commission_lamports=total_commission,
            epoch_details=epoch_details,
        )

    async def _calculate_partner_stake_for_epoch(
        self, partner_id: UUID, epoch: int
    ) -> int:
        """Calculate total active stake for a partner in a specific epoch.

        This sums up all stake from withdrawer wallets attributed to the partner.

        Args:
            partner_id: Partner UUID
            epoch: Epoch number

        Returns:
            Total stake in lamports
        """
        # Get all withdrawer wallet IDs for this partner
        result = await self.session.execute(
            select(PartnerWallet.wallet_id).where(
                PartnerWallet.partner_id == partner_id
            )
        )
        wallet_ids = [row[0] for row in result.all()]

        if not wallet_ids:
            return 0

        # Sum stake from all stake accounts with these withdrawer wallets
        result = await self.session.execute(
            select(SampleStakeAccount).where(
                SampleStakeAccount.epoch == epoch,
                SampleStakeAccount.withdrawer_wallet_id.in_(wallet_ids),
            )
        )
        stake_accounts = result.scalars().all()

        total_stake = sum(account.stake_lamports for account in stake_accounts)
        return total_stake

    async def calculate_all_partners_commission(
        self,
        start_epoch: int,
        end_epoch: int,
        commission_rate: Decimal = Decimal("0.10"),
    ) -> list[CommissionCalculationResult]:
        """Calculate commissions for all active partners.

        Args:
            start_epoch: First epoch in range (inclusive)
            end_epoch: Last epoch in range (inclusive)
            commission_rate: Commission rate as decimal (0.10 = 10%)

        Returns:
            List of commission results for all partners with stake
        """
        # Get all active partners
        result = await self.session.execute(
            select(Partners).where(Partners.is_active == True)
        )
        partners = result.scalars().all()

        results: list[CommissionCalculationResult] = []
        for partner in partners:
            try:
                commission_result = await self.calculate_partner_commission(
                    partner_id=partner.partner_id,
                    start_epoch=start_epoch,
                    end_epoch=end_epoch,
                    commission_rate=commission_rate,
                )
                # Only include partners with actual stake
                if commission_result["total_partner_stake_lamports"] > 0:
                    results.append(commission_result)
            except Exception:
                # Skip partners with no stake or errors
                continue

        return results
