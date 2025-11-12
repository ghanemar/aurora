"""Unit tests for rewards simulation service.

Tests cover:
- Epoch rewards calculation with 5% APY
- Validator commission calculation (5%)
- Per-wallet proportional rewards distribution
- Rewards validation and sum checks
- SOL/lamports conversion utilities
- Edge cases: zero stake, single wallet, extreme concentration
- Parameter validation and error handling
- Deterministic calculation verification
"""

from decimal import Decimal

import pytest
from src.core.services.rewards_simulator import (
    ANNUAL_APY,
    EPOCHS_PER_YEAR,
    LAMPORTS_PER_SOL,
    VALIDATOR_COMMISSION_RATE,
    RewardsSimulator,
)


class TestRewardsSimulatorInitialization:
    """Tests for RewardsSimulator initialization and parameters."""

    def test_default_initialization(self) -> None:
        """Test creating simulator with default parameters."""
        simulator = RewardsSimulator()

        assert simulator.annual_apy == ANNUAL_APY
        assert simulator.epochs_per_year == EPOCHS_PER_YEAR
        assert simulator.validator_commission_rate == VALIDATOR_COMMISSION_RATE

    def test_custom_parameters(self) -> None:
        """Test creating simulator with custom parameters."""
        simulator = RewardsSimulator(
            annual_apy=Decimal("0.08"),
            epochs_per_year=100,
            validator_commission_rate=Decimal("0.10")
        )

        assert simulator.annual_apy == Decimal("0.08")
        assert simulator.epochs_per_year == 100
        assert simulator.validator_commission_rate == Decimal("0.10")

    def test_negative_apy_raises_error(self) -> None:
        """Test that negative APY raises ValueError."""
        with pytest.raises(ValueError, match="annual_apy must be non-negative"):
            RewardsSimulator(annual_apy=Decimal("-0.05"))

    def test_zero_epochs_per_year_raises_error(self) -> None:
        """Test that zero epochs per year raises ValueError."""
        with pytest.raises(ValueError, match="epochs_per_year must be positive"):
            RewardsSimulator(epochs_per_year=0)

    def test_negative_epochs_per_year_raises_error(self) -> None:
        """Test that negative epochs per year raises ValueError."""
        with pytest.raises(ValueError, match="epochs_per_year must be positive"):
            RewardsSimulator(epochs_per_year=-10)

    def test_invalid_commission_rate_raises_error(self) -> None:
        """Test that commission rate outside 0-1 range raises ValueError."""
        with pytest.raises(ValueError, match="validator_commission_rate must be between 0 and 1"):
            RewardsSimulator(validator_commission_rate=Decimal("1.5"))

        with pytest.raises(ValueError, match="validator_commission_rate must be between 0 and 1"):
            RewardsSimulator(validator_commission_rate=Decimal("-0.05"))


class TestEpochRewardsSimulation:
    """Tests for simulate_epoch_rewards method."""

    def test_basic_epoch_rewards_calculation(self) -> None:
        """Test epoch rewards calculation with typical values."""
        simulator = RewardsSimulator()
        active_stake = 190_000_000_000_000  # 190K SOL in lamports

        result = simulator.simulate_epoch_rewards(
            active_stake_lamports=active_stake,
            epoch=820
        )

        # Calculate expected values
        # epoch_rate = 0.05 / 73 = 0.000684931506849315
        # total_rewards = 190,000 SOL * 0.000684931506849315 = ~130.137 SOL
        # = 130,136,986,301 lamports
        expected_total = 130_136_986_301

        assert result["total_epoch_rewards_lamports"] == expected_total
        assert result["active_stake_lamports"] == active_stake
        assert result["epoch"] == 820
        assert result["is_simulated"] is True

        # Validator commission = 5% of total
        expected_commission = int(expected_total * 0.05)
        assert result["validator_commission_lamports"] == expected_commission

        # Staker rewards = 95% of total
        expected_staker_rewards = expected_total - expected_commission
        assert result["staker_rewards_lamports"] == expected_staker_rewards

        # Verify commission + staker rewards = total
        assert (result["validator_commission_lamports"] +
                result["staker_rewards_lamports"] ==
                result["total_epoch_rewards_lamports"])

    def test_epoch_rewards_with_zero_stake(self) -> None:
        """Test epoch rewards calculation with zero stake."""
        simulator = RewardsSimulator()

        result = simulator.simulate_epoch_rewards(
            active_stake_lamports=0,
            epoch=800
        )

        assert result["total_epoch_rewards_lamports"] == 0
        assert result["validator_commission_lamports"] == 0
        assert result["staker_rewards_lamports"] == 0

    def test_epoch_rewards_with_small_stake(self) -> None:
        """Test epoch rewards calculation with small stake amount."""
        simulator = RewardsSimulator()
        active_stake = 1_000_000_000  # 1 SOL in lamports

        result = simulator.simulate_epoch_rewards(
            active_stake_lamports=active_stake,
            epoch=850
        )

        # With 1 SOL stake:
        # epoch_rewards = 1 SOL * (0.05 / 73) = ~0.000684931 SOL = 684,931 lamports
        assert result["total_epoch_rewards_lamports"] > 0
        assert result["validator_commission_lamports"] > 0
        assert result["staker_rewards_lamports"] > 0

    def test_epoch_rewards_with_large_stake(self) -> None:
        """Test epoch rewards calculation with large stake amount."""
        simulator = RewardsSimulator()
        active_stake = 10_000_000_000_000_000  # 10 million SOL in lamports

        result = simulator.simulate_epoch_rewards(
            active_stake_lamports=active_stake,
            epoch=860
        )

        # With 10M SOL stake:
        # epoch_rewards = 10,000,000 SOL * (0.05 / 73) = ~6,849.315 SOL
        assert result["total_epoch_rewards_lamports"] > 0
        assert result["validator_commission_lamports"] > 0
        assert result["staker_rewards_lamports"] > 0

    def test_epoch_rewards_simulation_params(self) -> None:
        """Test that simulation parameters are included in result."""
        simulator = RewardsSimulator(
            annual_apy=Decimal("0.08"),
            epochs_per_year=100,
            validator_commission_rate=Decimal("0.10")
        )

        result = simulator.simulate_epoch_rewards(
            active_stake_lamports=100_000_000_000_000,
            epoch=820
        )

        params = result["simulation_params"]
        assert params["apy"] == 0.08
        assert params["epochs_per_year"] == 100
        assert params["validator_commission_rate"] == 0.10

    def test_negative_stake_raises_error(self) -> None:
        """Test that negative stake raises ValueError."""
        simulator = RewardsSimulator()

        with pytest.raises(ValueError, match="active_stake_lamports must be non-negative"):
            simulator.simulate_epoch_rewards(
                active_stake_lamports=-1000,
                epoch=820
            )

    def test_negative_epoch_raises_error(self) -> None:
        """Test that negative epoch raises ValueError."""
        simulator = RewardsSimulator()

        with pytest.raises(ValueError, match="epoch must be non-negative"):
            simulator.simulate_epoch_rewards(
                active_stake_lamports=100_000_000_000_000,
                epoch=-1
            )

    def test_epoch_rewards_deterministic(self) -> None:
        """Test that epoch rewards calculation is deterministic."""
        simulator = RewardsSimulator()
        active_stake = 190_000_000_000_000

        # Calculate rewards twice
        result1 = simulator.simulate_epoch_rewards(
            active_stake_lamports=active_stake,
            epoch=820
        )
        result2 = simulator.simulate_epoch_rewards(
            active_stake_lamports=active_stake,
            epoch=820
        )

        # Results should be identical
        assert result1["total_epoch_rewards_lamports"] == result2["total_epoch_rewards_lamports"]
        assert result1["validator_commission_lamports"] == result2["validator_commission_lamports"]
        assert result1["staker_rewards_lamports"] == result2["staker_rewards_lamports"]


class TestWalletRewardsCalculation:
    """Tests for calculate_wallet_rewards method."""

    def test_single_wallet_gets_all_rewards(self) -> None:
        """Test that single wallet with all stake gets all rewards."""
        simulator = RewardsSimulator()

        wallet_rewards = simulator.calculate_wallet_rewards(
            wallet_stake_lamports=190_000_000_000_000,
            total_active_stake_lamports=190_000_000_000_000,
            staker_rewards_lamports=123_630_137_000
        )

        # Single wallet owns 100% of stake, should get 100% of rewards
        assert wallet_rewards == 123_630_137_000

    def test_proportional_wallet_rewards(self) -> None:
        """Test proportional rewards distribution to multiple wallets."""
        simulator = RewardsSimulator()
        total_stake = 190_000_000_000_000  # 190K SOL
        staker_rewards = 123_630_137_000  # ~123.63 SOL

        # Wallet 1: 50K SOL (26.32% of stake)
        wallet1_rewards = simulator.calculate_wallet_rewards(
            wallet_stake_lamports=50_000_000_000_000,
            total_active_stake_lamports=total_stake,
            staker_rewards_lamports=staker_rewards
        )

        # Wallet 2: 90K SOL (47.37% of stake)
        wallet2_rewards = simulator.calculate_wallet_rewards(
            wallet_stake_lamports=90_000_000_000_000,
            total_active_stake_lamports=total_stake,
            staker_rewards_lamports=staker_rewards
        )

        # Wallet 3: 50K SOL (26.32% of stake)
        wallet3_rewards = simulator.calculate_wallet_rewards(
            wallet_stake_lamports=50_000_000_000_000,
            total_active_stake_lamports=total_stake,
            staker_rewards_lamports=staker_rewards
        )

        # Verify proportional distribution
        assert wallet1_rewards > 0
        assert wallet2_rewards > wallet1_rewards  # Wallet 2 has more stake
        assert wallet2_rewards > wallet3_rewards
        assert wallet1_rewards == wallet3_rewards  # Equal stakes

        # Sum should be close to total (within rounding tolerance)
        total_distributed = wallet1_rewards + wallet2_rewards + wallet3_rewards
        assert abs(total_distributed - staker_rewards) <= 2  # Allow 2 lamports rounding

    def test_extreme_stake_concentration(self) -> None:
        """Test wallet rewards with extreme stake concentration (realistic scenario)."""
        simulator = RewardsSimulator()
        total_stake = 14_306_746_310_000_000  # 14.3M SOL (from Phase 1 data)
        staker_rewards = 10_000_000_000_000  # 10K SOL rewards

        # Whale wallet: 8.65M SOL (60.48% of stake) - from Phase 1 findings
        whale_rewards = simulator.calculate_wallet_rewards(
            wallet_stake_lamports=8_652_864_920_000_000,
            total_active_stake_lamports=total_stake,
            staker_rewards_lamports=staker_rewards
        )

        # Regular wallet: 100K SOL (0.70% of stake)
        regular_rewards = simulator.calculate_wallet_rewards(
            wallet_stake_lamports=100_000_000_000_000,
            total_active_stake_lamports=total_stake,
            staker_rewards_lamports=staker_rewards
        )

        # Whale should get ~60% of rewards
        expected_whale_proportion = 0.6048
        actual_whale_proportion = whale_rewards / staker_rewards
        assert abs(actual_whale_proportion - expected_whale_proportion) < 0.001

        # Regular wallet gets proportionally small amount
        assert regular_rewards < whale_rewards
        assert regular_rewards > 0

    def test_wallet_rewards_with_zero_total_stake(self) -> None:
        """Test wallet rewards when total stake is zero."""
        simulator = RewardsSimulator()

        wallet_rewards = simulator.calculate_wallet_rewards(
            wallet_stake_lamports=0,
            total_active_stake_lamports=0,
            staker_rewards_lamports=123_630_137_000
        )

        # Should return 0 when total stake is zero
        assert wallet_rewards == 0

    def test_wallet_rewards_with_zero_wallet_stake(self) -> None:
        """Test wallet rewards when wallet stake is zero."""
        simulator = RewardsSimulator()

        wallet_rewards = simulator.calculate_wallet_rewards(
            wallet_stake_lamports=0,
            total_active_stake_lamports=190_000_000_000_000,
            staker_rewards_lamports=123_630_137_000
        )

        # Wallet with no stake gets no rewards
        assert wallet_rewards == 0

    def test_negative_wallet_stake_raises_error(self) -> None:
        """Test that negative wallet stake raises ValueError."""
        simulator = RewardsSimulator()

        with pytest.raises(ValueError, match="wallet_stake_lamports must be non-negative"):
            simulator.calculate_wallet_rewards(
                wallet_stake_lamports=-1000,
                total_active_stake_lamports=190_000_000_000_000,
                staker_rewards_lamports=123_630_137_000
            )

    def test_negative_total_stake_raises_error(self) -> None:
        """Test that negative total stake raises ValueError."""
        simulator = RewardsSimulator()

        with pytest.raises(ValueError, match="total_active_stake_lamports must be non-negative"):
            simulator.calculate_wallet_rewards(
                wallet_stake_lamports=50_000_000_000_000,
                total_active_stake_lamports=-1000,
                staker_rewards_lamports=123_630_137_000
            )

    def test_negative_staker_rewards_raises_error(self) -> None:
        """Test that negative staker rewards raises ValueError."""
        simulator = RewardsSimulator()

        with pytest.raises(ValueError, match="staker_rewards_lamports must be non-negative"):
            simulator.calculate_wallet_rewards(
                wallet_stake_lamports=50_000_000_000_000,
                total_active_stake_lamports=190_000_000_000_000,
                staker_rewards_lamports=-1000
            )

    def test_wallet_stake_exceeds_total_raises_error(self) -> None:
        """Test that wallet stake > total stake raises ValueError."""
        simulator = RewardsSimulator()

        with pytest.raises(ValueError, match="wallet_stake_lamports cannot exceed total_active_stake_lamports"):
            simulator.calculate_wallet_rewards(
                wallet_stake_lamports=200_000_000_000_000,
                total_active_stake_lamports=190_000_000_000_000,
                staker_rewards_lamports=123_630_137_000
            )


class TestRewardsValidation:
    """Tests for validate_rewards_distribution method."""

    def test_perfect_distribution_validation(self) -> None:
        """Test validation with perfect sum (no rounding error)."""
        simulator = RewardsSimulator()
        staker_rewards = 123_630_137_000
        wallet_rewards = [41_210_045_666, 41_210_045_667, 41_210_045_667]

        is_valid, difference = simulator.validate_rewards_distribution(
            wallet_rewards=wallet_rewards,
            staker_rewards_lamports=staker_rewards,
            tolerance_lamports=1000
        )

        assert is_valid is True
        assert difference == 0

    def test_distribution_within_tolerance(self) -> None:
        """Test validation with small rounding error within tolerance."""
        simulator = RewardsSimulator()
        staker_rewards = 123_630_137_000
        # Sum is 123_630_137_500 (500 lamports over)
        wallet_rewards = [41_210_045_800, 41_210_045_850, 41_210_045_850]

        is_valid, difference = simulator.validate_rewards_distribution(
            wallet_rewards=wallet_rewards,
            staker_rewards_lamports=staker_rewards,
            tolerance_lamports=1000
        )

        assert is_valid is True
        assert difference == 500

    def test_distribution_exceeds_tolerance(self) -> None:
        """Test validation with rounding error exceeding tolerance."""
        simulator = RewardsSimulator()
        staker_rewards = 123_630_137_000
        # Sum is 124_000_000_000 (369,863,000 lamports over)
        wallet_rewards = [40_000_000_000, 42_000_000_000, 42_000_000_000]

        is_valid, difference = simulator.validate_rewards_distribution(
            wallet_rewards=wallet_rewards,
            staker_rewards_lamports=staker_rewards,
            tolerance_lamports=1000
        )

        assert is_valid is False
        assert difference == 369_863_000

    def test_validation_with_empty_wallet_list(self) -> None:
        """Test validation with no wallets."""
        simulator = RewardsSimulator()

        is_valid, difference = simulator.validate_rewards_distribution(
            wallet_rewards=[],
            staker_rewards_lamports=123_630_137_000,
            tolerance_lamports=1000
        )

        assert is_valid is False
        assert difference == 123_630_137_000

    def test_validation_with_single_wallet(self) -> None:
        """Test validation with single wallet."""
        simulator = RewardsSimulator()
        staker_rewards = 123_630_137_000

        is_valid, difference = simulator.validate_rewards_distribution(
            wallet_rewards=[staker_rewards],
            staker_rewards_lamports=staker_rewards,
            tolerance_lamports=1000
        )

        assert is_valid is True
        assert difference == 0

    def test_negative_staker_rewards_raises_error(self) -> None:
        """Test that negative staker rewards raises ValueError."""
        simulator = RewardsSimulator()

        with pytest.raises(ValueError, match="staker_rewards_lamports must be non-negative"):
            simulator.validate_rewards_distribution(
                wallet_rewards=[100, 200, 300],
                staker_rewards_lamports=-1000,
                tolerance_lamports=1000
            )


class TestConversionUtilities:
    """Tests for SOL/lamports conversion utilities."""

    def test_sol_to_lamports_conversion(self) -> None:
        """Test converting SOL to lamports."""
        simulator = RewardsSimulator()

        # Test various amounts
        assert simulator.sol_to_lamports(Decimal("1.0")) == 1_000_000_000
        assert simulator.sol_to_lamports(Decimal("123.456789")) == 123_456_789_000
        assert simulator.sol_to_lamports(Decimal("0.000000001")) == 1
        assert simulator.sol_to_lamports(Decimal("0")) == 0

    def test_lamports_to_sol_conversion(self) -> None:
        """Test converting lamports to SOL."""
        simulator = RewardsSimulator()

        # Test various amounts
        assert simulator.lamports_to_sol(1_000_000_000) == Decimal("1.0")
        assert simulator.lamports_to_sol(123_456_789_000) == Decimal("123.456789")
        assert simulator.lamports_to_sol(1) == Decimal("0.000000001")
        assert simulator.lamports_to_sol(0) == Decimal("0")

    def test_round_trip_conversion(self) -> None:
        """Test that conversions are reversible."""
        simulator = RewardsSimulator()

        # SOL -> lamports -> SOL
        original_sol = Decimal("190000.123456789")
        lamports = simulator.sol_to_lamports(original_sol)
        converted_back = simulator.lamports_to_sol(lamports)
        assert converted_back == original_sol

        # lamports -> SOL -> lamports
        original_lamports = 190_000_123_456_789
        sol = simulator.lamports_to_sol(original_lamports)
        converted_back_lamports = simulator.sol_to_lamports(sol)
        assert converted_back_lamports == original_lamports


class TestRealisticScenarios:
    """Tests using realistic data from Phase 1 findings."""

    def test_globalstake_sample_data_simulation(self) -> None:
        """Test simulation using actual GlobalStake sample data characteristics."""
        simulator = RewardsSimulator()

        # From Phase 1 findings: Total stake = 14,306,746.31 SOL
        total_stake_lamports = 14_306_746_310_000_000

        # Simulate epoch 820
        epoch_result = simulator.simulate_epoch_rewards(
            active_stake_lamports=total_stake_lamports,
            epoch=820
        )

        # Verify rewards were calculated
        assert epoch_result["total_epoch_rewards_lamports"] > 0
        assert epoch_result["validator_commission_lamports"] > 0
        assert epoch_result["staker_rewards_lamports"] > 0

        # Test whale wallet (60.48% of stake from Phase 1)
        whale_stake = 8_652_864_920_000_000
        whale_rewards = simulator.calculate_wallet_rewards(
            wallet_stake_lamports=whale_stake,
            total_active_stake_lamports=total_stake_lamports,
            staker_rewards_lamports=epoch_result["staker_rewards_lamports"]
        )

        # Whale should get approximately 60.48% of staker rewards
        expected_whale_share = epoch_result["staker_rewards_lamports"] * 0.6048
        assert abs(whale_rewards - expected_whale_share) < 1_000_000  # Within 0.001 SOL

    def test_partner_commission_scenario(self) -> None:
        """Test realistic partner commission calculation scenario."""
        simulator = RewardsSimulator()

        # Partner 1: 60.48% stake (whale partner from Phase 1)
        # Partner 2: 38.75% stake (distributed partner from Phase 1)
        # Unassigned: 0.77% stake

        total_stake = 14_306_746_310_000_000
        partner1_stake = int(total_stake * 0.6048)
        partner2_stake = int(total_stake * 0.3875)
        unassigned_stake = total_stake - partner1_stake - partner2_stake

        # Simulate epoch rewards
        epoch_result = simulator.simulate_epoch_rewards(
            active_stake_lamports=total_stake,
            epoch=830
        )

        staker_rewards = epoch_result["staker_rewards_lamports"]

        # Calculate partner rewards
        partner1_rewards = simulator.calculate_wallet_rewards(
            wallet_stake_lamports=partner1_stake,
            total_active_stake_lamports=total_stake,
            staker_rewards_lamports=staker_rewards
        )

        partner2_rewards = simulator.calculate_wallet_rewards(
            wallet_stake_lamports=partner2_stake,
            total_active_stake_lamports=total_stake,
            staker_rewards_lamports=staker_rewards
        )

        unassigned_rewards = simulator.calculate_wallet_rewards(
            wallet_stake_lamports=unassigned_stake,
            total_active_stake_lamports=total_stake,
            staker_rewards_lamports=staker_rewards
        )

        # Verify distribution
        assert partner1_rewards > partner2_rewards  # Whale partner dominates
        assert partner2_rewards > unassigned_rewards
        assert unassigned_rewards > 0

        # Validate total distribution
        is_valid, diff = simulator.validate_rewards_distribution(
            wallet_rewards=[partner1_rewards, partner2_rewards, unassigned_rewards],
            staker_rewards_lamports=staker_rewards,
            tolerance_lamports=10
        )

        assert is_valid is True
        assert diff <= 10
