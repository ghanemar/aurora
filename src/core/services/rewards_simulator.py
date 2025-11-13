"""Rewards simulation service for testing and validation.

This module provides simulated epoch rewards calculations based on
5% APY assumption for Solana validators. It's designed to generate
realistic test data for validating the commission calculation engine.

The simulation follows Solana staking mechanics:
- Active stake earns rewards each epoch
- Validator takes commission (typically 5%)
- Remaining rewards distributed proportionally to stakers
- Rewards calculated per epoch (~73 epochs per year on Solana)

Usage:
    simulator = RewardsSimulator()

    # Calculate epoch-level rewards
    epoch_rewards = simulator.simulate_epoch_rewards(
        active_stake_lamports=190_000_000_000_000,  # 190K SOL
        epoch=820
    )

    # Calculate per-wallet rewards
    wallet_rewards = simulator.calculate_wallet_rewards(
        wallet_stake_lamports=50_000_000_000_000,  # 50K SOL
        total_active_stake_lamports=190_000_000_000_000,
        staker_rewards_lamports=epoch_rewards['staker_rewards_lamports']
    )
"""

from decimal import Decimal
from typing import TypedDict


# Simulation constants based on Solana mainnet characteristics
ANNUAL_APY = Decimal("0.05")  # 5% annual percentage yield
EPOCHS_PER_YEAR = 73  # Approximate Solana epochs per year (~2 days per epoch)
VALIDATOR_COMMISSION_RATE = Decimal("0.05")  # 5% validator commission
LAMPORTS_PER_SOL = 1_000_000_000  # 1 SOL = 1 billion lamports


class EpochRewardsResult(TypedDict):
    """Result of epoch rewards simulation.

    All amounts in lamports (1 SOL = 1,000,000,000 lamports).
    """
    total_epoch_rewards_lamports: int
    validator_commission_lamports: int
    staker_rewards_lamports: int
    active_stake_lamports: int
    epoch: int
    is_simulated: bool
    simulation_params: dict


class RewardsSimulator:
    """Simulates epoch rewards for Solana validators.

    This service provides deterministic reward calculations based on
    5% APY assumption. Used for generating realistic test data without
    requiring actual blockchain data ingestion.

    All calculations use integer arithmetic (lamports) to avoid floating
    point precision issues. Results are deterministic and reproducible.
    """

    def __init__(
        self,
        annual_apy: Decimal = ANNUAL_APY,
        epochs_per_year: int = EPOCHS_PER_YEAR,
        validator_commission_rate: Decimal = VALIDATOR_COMMISSION_RATE
    ) -> None:
        """Initialize rewards simulator with configurable parameters.

        Args:
            annual_apy: Annual percentage yield (default: 0.05 for 5%)
            epochs_per_year: Number of epochs per year (default: 73 for Solana)
            validator_commission_rate: Validator commission rate (default: 0.05 for 5%)

        Raises:
            ValueError: If any parameter is negative or epochs_per_year is zero
        """
        if annual_apy < 0:
            raise ValueError("annual_apy must be non-negative")
        if epochs_per_year <= 0:
            raise ValueError("epochs_per_year must be positive")
        if validator_commission_rate < 0 or validator_commission_rate > 1:
            raise ValueError("validator_commission_rate must be between 0 and 1")

        self.annual_apy = annual_apy
        self.epochs_per_year = epochs_per_year
        self.validator_commission_rate = validator_commission_rate

    def simulate_epoch_rewards(
        self,
        active_stake_lamports: int,
        epoch: int
    ) -> EpochRewardsResult:
        """Simulate epoch rewards based on 5% APY assumption.

        Calculates total epoch rewards, validator commission, and staker rewards
        using the formula:
            epoch_rewards = active_stake * (annual_apy / epochs_per_year)
            validator_commission = epoch_rewards * validator_commission_rate
            staker_rewards = epoch_rewards - validator_commission

        Args:
            active_stake_lamports: Total active stake for the validator in lamports
            epoch: Epoch number for tracking purposes

        Returns:
            Dictionary with rewards breakdown:
                - total_epoch_rewards_lamports: Total rewards earned
                - validator_commission_lamports: Validator's commission
                - staker_rewards_lamports: Rewards distributed to stakers
                - active_stake_lamports: Input active stake
                - epoch: Epoch number
                - is_simulated: Always True for simulated data
                - simulation_params: Parameters used for simulation

        Raises:
            ValueError: If active_stake_lamports or epoch is negative

        Example:
            >>> simulator = RewardsSimulator()
            >>> result = simulator.simulate_epoch_rewards(
            ...     active_stake_lamports=190_000_000_000_000,  # 190K SOL
            ...     epoch=820
            ... )
            >>> result['total_epoch_rewards_lamports']
            130136986301  # ~130.14 SOL per epoch
        """
        if active_stake_lamports < 0:
            raise ValueError("active_stake_lamports must be non-negative")
        if epoch < 0:
            raise ValueError("epoch must be non-negative")

        # Calculate epoch rewards (annual rate / epochs per year)
        epoch_rate = self.annual_apy / self.epochs_per_year
        total_epoch_rewards = int(Decimal(active_stake_lamports) * epoch_rate)

        # Split between validator commission and staker rewards
        validator_commission = int(Decimal(total_epoch_rewards) * self.validator_commission_rate)
        staker_rewards = total_epoch_rewards - validator_commission

        return EpochRewardsResult(
            total_epoch_rewards_lamports=total_epoch_rewards,
            validator_commission_lamports=validator_commission,
            staker_rewards_lamports=staker_rewards,
            active_stake_lamports=active_stake_lamports,
            epoch=epoch,
            is_simulated=True,
            simulation_params={
                "apy": float(self.annual_apy),
                "epochs_per_year": self.epochs_per_year,
                "validator_commission_rate": float(self.validator_commission_rate)
            }
        )

    def calculate_wallet_rewards(
        self,
        wallet_stake_lamports: int,
        total_active_stake_lamports: int,
        staker_rewards_lamports: int
    ) -> int:
        """Calculate proportional rewards for a wallet based on its stake.

        Distributes staker rewards proportionally based on each wallet's
        share of the total active stake:
            wallet_rewards = (wallet_stake / total_active_stake) * staker_rewards

        Args:
            wallet_stake_lamports: Individual wallet's stake amount in lamports
            total_active_stake_lamports: Total active stake across all wallets in lamports
            staker_rewards_lamports: Total staker rewards to distribute in lamports

        Returns:
            Wallet's proportional share of staker rewards in lamports

        Raises:
            ValueError: If any parameter is negative or if wallet_stake > total_active_stake

        Example:
            >>> simulator = RewardsSimulator()
            >>> # Wallet with 50K SOL stake, total 190K SOL, 123.6 SOL rewards
            >>> wallet_rewards = simulator.calculate_wallet_rewards(
            ...     wallet_stake_lamports=50_000_000_000_000,
            ...     total_active_stake_lamports=190_000_000_000_000,
            ...     staker_rewards_lamports=123_630_137_000_000
            ... )
            >>> wallet_rewards
            32534246052  # ~32.53 SOL (26.3% of total stake)
        """
        if wallet_stake_lamports < 0:
            raise ValueError("wallet_stake_lamports must be non-negative")
        if total_active_stake_lamports < 0:
            raise ValueError("total_active_stake_lamports must be non-negative")
        if staker_rewards_lamports < 0:
            raise ValueError("staker_rewards_lamports must be non-negative")
        if wallet_stake_lamports > total_active_stake_lamports:
            raise ValueError("wallet_stake_lamports cannot exceed total_active_stake_lamports")

        # Handle edge case of zero total stake
        if total_active_stake_lamports == 0:
            return 0

        # Calculate proportional share using Decimal for precision
        stake_proportion = Decimal(wallet_stake_lamports) / Decimal(total_active_stake_lamports)
        wallet_rewards = int(Decimal(staker_rewards_lamports) * stake_proportion)

        return wallet_rewards

    def validate_rewards_distribution(
        self,
        wallet_rewards: list[int],
        staker_rewards_lamports: int,
        tolerance_lamports: int = 1000
    ) -> tuple[bool, int]:
        """Validate that wallet rewards sum correctly with minimal rounding error.

        Ensures the sum of individual wallet rewards equals total staker rewards
        within acceptable tolerance. This catches calculation errors from rounding
        or precision loss.

        Args:
            wallet_rewards: List of individual wallet reward amounts in lamports
            staker_rewards_lamports: Total staker rewards that should be distributed
            tolerance_lamports: Maximum acceptable difference in lamports (default: 1000)

        Returns:
            Tuple of (is_valid, difference_lamports):
                - is_valid: True if sum within tolerance, False otherwise
                - difference_lamports: Absolute difference between sum and expected

        Raises:
            ValueError: If staker_rewards_lamports is negative

        Example:
            >>> simulator = RewardsSimulator()
            >>> wallet_rewards = [30_000_000_000, 60_000_000_000, 33_630_137_000]
            >>> is_valid, diff = simulator.validate_rewards_distribution(
            ...     wallet_rewards=wallet_rewards,
            ...     staker_rewards_lamports=123_630_137_000,
            ...     tolerance_lamports=1000
            ... )
            >>> is_valid
            True
            >>> diff
            0
        """
        if staker_rewards_lamports < 0:
            raise ValueError("staker_rewards_lamports must be non-negative")

        total_distributed = sum(wallet_rewards)
        difference = abs(total_distributed - staker_rewards_lamports)
        is_valid = difference <= tolerance_lamports

        return is_valid, difference

    def sol_to_lamports(self, sol_amount: Decimal) -> int:
        """Convert SOL amount to lamports.

        Args:
            sol_amount: Amount in SOL

        Returns:
            Amount in lamports (integer)

        Example:
            >>> simulator = RewardsSimulator()
            >>> simulator.sol_to_lamports(Decimal("123.456789"))
            123456789000
        """
        return int(sol_amount * LAMPORTS_PER_SOL)

    def lamports_to_sol(self, lamports: int) -> Decimal:
        """Convert lamports to SOL amount.

        Args:
            lamports: Amount in lamports

        Returns:
            Amount in SOL (Decimal for precision)

        Example:
            >>> simulator = RewardsSimulator()
            >>> simulator.lamports_to_sol(123456789000)
            Decimal('123.456789')
        """
        return Decimal(lamports) / LAMPORTS_PER_SOL
