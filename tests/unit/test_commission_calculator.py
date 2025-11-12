"""Unit tests for CommissionCalculator service.

Tests commission calculation logic including:
- Partner stake calculation per epoch
- Proportional reward distribution
- Commission rate application
- Epoch range validation
- Extreme concentration scenarios
"""

import pytest
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select

from src.core.models import Partners, PartnerWallet
from src.core.models.sample_data import (
    SampleEpochReward,
    SampleStakeAccount,
    SampleValidatorEpochSummary,
)
from src.core.services.commission_calculator import CommissionCalculator


@pytest.fixture
async def setup_test_data(test_session):
    """Set up sample data for commission calculation tests."""
    # Create test partners
    partner1 = Partners(
        partner_name="Test Partner 1",
        contact_email="partner1@test.com",
        is_active=True,
    )
    partner2 = Partners(
        partner_name="Test Partner 2",
        contact_email="partner2@test.com",
        is_active=True,
    )
    test_session.add(partner1)
    test_session.add(partner2)
    await test_session.flush()

    # Create test wallets
    wallet1 = PartnerWallet(
        partner_id=partner1.partner_id,
        chain_id="test-chain",
        wallet_address="wallet1_address",
        introduced_date="2024-01-01",
        is_active=True,
    )
    wallet2 = PartnerWallet(
        partner_id=partner2.partner_id,
        chain_id="test-chain",
        wallet_address="wallet2_address",
        introduced_date="2024-01-01",
        is_active=True,
    )
    test_session.add(wallet1)
    test_session.add(wallet2)
    await test_session.flush()

    # Create epoch summaries for epochs 100-102
    for epoch in [100, 101, 102]:
        summary = SampleValidatorEpochSummary(
            epoch=epoch,
            validator_vote_pubkey="test_validator_vote",
            validator_node_pubkey="test_validator_node",
            commission_bps=500,  # 5%
            total_delegated_stake_lamports=int(1000e9),  # 1000 SOL
            total_active_stake_lamports=int(1000e9),
            total_stakers=2,
        )
        test_session.add(summary)
        await test_session.flush()

        # Create epoch rewards
        reward = SampleEpochReward(
            epoch_summary_id=summary.summary_id,
            epoch=epoch,
            validator_vote_pubkey="test_validator_vote",
            total_epoch_rewards_lamports=int(10e9),  # 10 SOL total
            validator_commission_lamports=int(0.5e9),  # 0.5 SOL (5%)
            staker_rewards_lamports=int(9.5e9),  # 9.5 SOL to stakers
            active_stake_lamports=int(1000e9),
            is_simulated=True,
            simulation_params={"apy": "0.05"},
        )
        test_session.add(reward)

        # Create stake accounts
        # Partner 1 has 60% stake (600 SOL)
        stake1 = SampleStakeAccount(
            epoch_summary_id=summary.summary_id,
            epoch=epoch,
            validator_vote_pubkey="test_validator_vote",
            stake_account_pubkey=f"stake1_epoch{epoch}",
            staker_wallet_id=wallet1.wallet_id,
            withdrawer_wallet_id=wallet1.wallet_id,
            stake_lamports=int(600e9),
            activation_epoch=epoch,
        )
        test_session.add(stake1)

        # Partner 2 has 40% stake (400 SOL)
        stake2 = SampleStakeAccount(
            epoch_summary_id=summary.summary_id,
            epoch=epoch,
            validator_vote_pubkey="test_validator_vote",
            stake_account_pubkey=f"stake2_epoch{epoch}",
            staker_wallet_id=wallet2.wallet_id,
            withdrawer_wallet_id=wallet2.wallet_id,
            stake_lamports=int(400e9),
            activation_epoch=epoch,
        )
        test_session.add(stake2)

    await test_session.commit()

    return {
        "partner1": partner1,
        "partner2": partner2,
        "wallet1": wallet1,
        "wallet2": wallet2,
    }


class TestCommissionCalculator:
    """Tests for CommissionCalculator service."""

    @pytest.mark.asyncio
    async def test_calculate_single_epoch_commission(self, test_session, setup_test_data):
        """Test commission calculation for a single epoch."""
        data = await setup_test_data
        calculator = CommissionCalculator(test_session)

        result = await calculator.calculate_partner_commission(
            partner_id=data["partner1"].partner_id,
            start_epoch=100,
            end_epoch=100,
            commission_rate=Decimal("0.10"),  # 10% commission
        )

        # Partner 1 has 60% stake → 60% of 9.5 SOL rewards = 5.7 SOL
        # 10% commission on 5.7 SOL = 0.57 SOL
        assert result["epoch_count"] == 1
        assert result["total_partner_stake_lamports"] == int(600e9)
        assert abs(result["total_partner_rewards_lamports"] - int(5.7e9)) < 1000  # Allow small rounding
        assert abs(result["total_commission_lamports"] - int(0.57e9)) < 100

    @pytest.mark.asyncio
    async def test_calculate_multi_epoch_commission(self, test_session, setup_test_data):
        """Test commission calculation across multiple epochs."""
        data = await setup_test_data
        calculator = CommissionCalculator(test_session)

        result = await calculator.calculate_partner_commission(
            partner_id=data["partner1"].partner_id,
            start_epoch=100,
            end_epoch=102,
            commission_rate=Decimal("0.10"),
        )

        # 3 epochs × 0.57 SOL commission = 1.71 SOL
        assert result["epoch_count"] == 3
        assert result["total_partner_stake_lamports"] == int(1800e9)  # 600 × 3
        assert abs(result["total_commission_lamports"] - int(1.71e9)) < 1000

    @pytest.mark.asyncio
    async def test_different_commission_rates(self, test_session, setup_test_data):
        """Test that different commission rates produce correct results."""
        data = await setup_test_data
        calculator = CommissionCalculator(test_session)

        # 5% commission
        result_5pct = await calculator.calculate_partner_commission(
            partner_id=data["partner1"].partner_id,
            start_epoch=100,
            end_epoch=100,
            commission_rate=Decimal("0.05"),
        )

        # 20% commission
        result_20pct = await calculator.calculate_partner_commission(
            partner_id=data["partner1"].partner_id,
            start_epoch=100,
            end_epoch=100,
            commission_rate=Decimal("0.20"),
        )

        # 20% should be 4x of 5%
        assert result_20pct["total_commission_lamports"] == result_5pct["total_commission_lamports"] * 4

    @pytest.mark.asyncio
    async def test_proportional_distribution(self, test_session, setup_test_data):
        """Test that rewards are distributed proportionally to stake."""
        data = await setup_test_data
        calculator = CommissionCalculator(test_session)

        result1 = await calculator.calculate_partner_commission(
            partner_id=data["partner1"].partner_id,
            start_epoch=100,
            end_epoch=100,
            commission_rate=Decimal("0.10"),
        )

        result2 = await calculator.calculate_partner_commission(
            partner_id=data["partner2"].partner_id,
            start_epoch=100,
            end_epoch=100,
            commission_rate=Decimal("0.10"),
        )

        # Partner 1: 60% stake, Partner 2: 40% stake
        # Rewards should be in 60:40 ratio (3:2)
        ratio = result1["total_partner_rewards_lamports"] / result2["total_partner_rewards_lamports"]
        assert abs(ratio - 1.5) < 0.01  # 60/40 = 1.5

    @pytest.mark.asyncio
    async def test_invalid_epoch_range(self, test_session, setup_test_data):
        """Test that invalid epoch ranges raise errors."""
        data = await setup_test_data
        calculator = CommissionCalculator(test_session)

        # Start > end
        with pytest.raises(ValueError, match="Start epoch .* must be <= end epoch"):
            await calculator.calculate_partner_commission(
                partner_id=data["partner1"].partner_id,
                start_epoch=102,
                end_epoch=100,
            )

    @pytest.mark.asyncio
    async def test_discontinuous_epoch_range(self, test_session, setup_test_data):
        """Test that discontinuous epoch ranges raise errors."""
        data = await setup_test_data
        calculator = CommissionCalculator(test_session)

        # Range 100-110 is discontinuous (we only have 100-102)
        with pytest.raises(ValueError, match="not continuous"):
            await calculator.calculate_partner_commission(
                partner_id=data["partner1"].partner_id,
                start_epoch=100,
                end_epoch=110,
            )

    @pytest.mark.asyncio
    async def test_nonexistent_partner(self, test_session, setup_test_data):
        """Test that nonexistent partner raises error."""
        calculator = CommissionCalculator(test_session)

        fake_partner_id = UUID("00000000-0000-0000-0000-000000000000")
        with pytest.raises(ValueError, match="Partner not found"):
            await calculator.calculate_partner_commission(
                partner_id=fake_partner_id,
                start_epoch=100,
                end_epoch=100,
            )

    @pytest.mark.asyncio
    async def test_epoch_details_structure(self, test_session, setup_test_data):
        """Test that epoch details contain correct information."""
        data = await setup_test_data
        calculator = CommissionCalculator(test_session)

        result = await calculator.calculate_partner_commission(
            partner_id=data["partner1"].partner_id,
            start_epoch=100,
            end_epoch=101,
            commission_rate=Decimal("0.10"),
        )

        assert len(result["epoch_details"]) == 2

        for detail in result["epoch_details"]:
            assert "epoch" in detail
            assert "total_active_stake_lamports" in detail
            assert "partner_stake_lamports" in detail
            assert "stake_percentage" in detail
            assert "total_staker_rewards_lamports" in detail
            assert "partner_rewards_lamports" in detail
            assert "commission_rate" in detail
            assert "partner_commission_lamports" in detail

            # Verify stake percentage calculation
            expected_pct = Decimal(str(detail["partner_stake_lamports"])) / Decimal(
                str(detail["total_active_stake_lamports"])
            )
            assert abs(detail["stake_percentage"] - expected_pct) < Decimal("0.0001")

    @pytest.mark.asyncio
    async def test_calculate_all_partners(self, test_session, setup_test_data):
        """Test calculating commissions for all partners."""
        calculator = CommissionCalculator(test_session)

        results = await calculator.calculate_all_partners_commission(
            start_epoch=100,
            end_epoch=100,
            commission_rate=Decimal("0.10"),
        )

        # Should have both test partners with stake
        assert len(results) >= 2

        partner_names = [r["partner_name"] for r in results]
        assert "Test Partner 1" in partner_names
        assert "Test Partner 2" in partner_names

    @pytest.mark.asyncio
    async def test_zero_stake_partner(self, test_session):
        """Test partner with no stake returns zero commission."""
        # Create partner with no wallets/stake
        partner = Partners(
            partner_name="No Stake Partner",
            contact_email="nostake@test.com",
            is_active=True,
        )
        test_session.add(partner)
        await test_session.commit()

        calculator = CommissionCalculator(test_session)

        result = await calculator.calculate_partner_commission(
            partner_id=partner.partner_id,
            start_epoch=100,
            end_epoch=100,
        )

        assert result["total_partner_stake_lamports"] == 0
        assert result["total_partner_rewards_lamports"] == 0
        assert result["total_commission_lamports"] == 0
