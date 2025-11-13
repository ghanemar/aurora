"""Test commission calculator with real sample data."""

import asyncio
import sys
from decimal import Decimal
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.services.commission_calculator import CommissionCalculator
from src.db import async_session_factory


async def test_commission_calculation():
    """Test commission calculation with imported sample data."""
    from sqlalchemy import select
    from src.core.models import Partners

    async with async_session_factory() as session:
        calculator = CommissionCalculator(session)

        # Get partner IDs
        result = await session.execute(
            select(Partners).where(Partners.partner_name == "GlobalStake Partner 1")
        )
        partner1 = result.scalar_one_or_none()

        result = await session.execute(
            select(Partners).where(Partners.partner_name == "GlobalStake Partner 2")
        )
        partner2 = result.scalar_one_or_none()

        if not partner1 or not partner2:
            print("✗ Sample data partners not found. Run seed script first.")
            return

        print("=" * 70)
        print("Commission Calculator Test - GlobalStake Sample Data")
        print("=" * 70)
        print()

        # Test Partner 1 (1 whale wallet with ~60% stake)
        print("[Test 1] Partner 1 Commission - Epochs 800-805")
        print("-" * 70)
        try:
            result = await calculator.calculate_partner_commission(
                partner_id=partner1.partner_id,
                start_epoch=800,
                end_epoch=805,
                commission_rate=Decimal("0.10"),  # 10% commission
            )

            print(f"Partner: {result['partner_name']}")
            print(f"Epoch Range: {result['start_epoch']}-{result['end_epoch']} ({result['epoch_count']} epochs)")
            print(f"Total Stake: {result['total_partner_stake_lamports'] / 1e9:,.2f} SOL")
            print(f"Total Rewards: {result['total_partner_rewards_lamports'] / 1e9:,.2f} SOL")
            print(f"Commission Rate: {result['commission_rate'] * 100}%")
            print(f"Total Commission: {result['total_commission_lamports'] / 1e9:,.2f} SOL")
            print()

            # Show per-epoch details
            print("Per-Epoch Breakdown:")
            for detail in result['epoch_details'][:3]:  # Show first 3 epochs
                print(f"  Epoch {detail['epoch']}:")
                print(f"    Stake: {detail['partner_stake_lamports'] / 1e9:,.2f} SOL ({detail['stake_percentage'] * 100:.2f}%)")
                print(f"    Rewards: {detail['partner_rewards_lamports'] / 1e9:,.2f} SOL")
                print(f"    Commission: {detail['partner_commission_lamports'] / 1e9:,.2f} SOL")

            print()
            print("✓ Partner 1 calculation completed successfully")
            print()

        except Exception as e:
            print(f"✗ Error calculating Partner 1 commission: {e}")
            print()

        # Test Partner 2 (146 wallets with ~39% stake)
        print("[Test 2] Partner 2 Commission - Epochs 800-805")
        print("-" * 70)
        try:
            result = await calculator.calculate_partner_commission(
                partner_id=partner2.partner_id,
                start_epoch=800,
                end_epoch=805,
                commission_rate=Decimal("0.10"),
            )

            print(f"Partner: {result['partner_name']}")
            print(f"Epoch Range: {result['start_epoch']}-{result['end_epoch']} ({result['epoch_count']} epochs)")
            print(f"Total Stake: {result['total_partner_stake_lamports'] / 1e9:,.2f} SOL")
            print(f"Total Rewards: {result['total_partner_rewards_lamports'] / 1e9:,.2f} SOL")
            print(f"Commission Rate: {result['commission_rate'] * 100}%")
            print(f"Total Commission: {result['total_commission_lamports'] / 1e9:,.2f} SOL")
            print()
            print("✓ Partner 2 calculation completed successfully")
            print()

        except Exception as e:
            print(f"✗ Error calculating Partner 2 commission: {e}")
            print()

        # Test all partners for single epoch
        print("[Test 3] All Partners Commission - Epoch 800 Only")
        print("-" * 70)
        try:
            results = await calculator.calculate_all_partners_commission(
                start_epoch=800,
                end_epoch=800,
                commission_rate=Decimal("0.10"),
            )

            for result in results:
                print(f"{result['partner_name']}:")
                print(f"  Stake: {result['total_partner_stake_lamports'] / 1e9:,.2f} SOL")
                print(f"  Commission: {result['total_commission_lamports'] / 1e9:,.2f} SOL")
                print()

            print(f"✓ Calculated commissions for {len(results)} partners")
            print()

        except Exception as e:
            print(f"✗ Error calculating all partners: {e}")
            print()

        # Test long epoch range
        print("[Test 4] Partner 1 Commission - All 61 Epochs (800-860)")
        print("-" * 70)
        try:
            result = await calculator.calculate_partner_commission(
                partner_id=partner1.partner_id,
                start_epoch=800,
                end_epoch=860,
                commission_rate=Decimal("0.10"),
            )

            print(f"Partner: {result['partner_name']}")
            print(f"Epoch Count: {result['epoch_count']} epochs")
            print(f"Average Stake: {result['total_partner_stake_lamports'] / result['epoch_count'] / 1e9:,.2f} SOL")
            print(f"Total Rewards: {result['total_partner_rewards_lamports'] / 1e9:,.2f} SOL")
            print(f"Total Commission: {result['total_commission_lamports'] / 1e9:,.2f} SOL")
            print()
            print("✓ Long range calculation completed successfully")
            print()

        except Exception as e:
            print(f"✗ Error calculating long range: {e}")
            print()

        # Test invalid epoch range
        print("[Test 5] Invalid Epoch Range (Should Fail)")
        print("-" * 70)
        try:
            result = await calculator.calculate_partner_commission(
                partner_id=partner1.partner_id,
                start_epoch=800,
                end_epoch=900,  # Beyond available data
                commission_rate=Decimal("0.10"),
            )
            print("✗ Should have raised an error for discontinuous range!")
            print()

        except ValueError as e:
            print(f"✓ Correctly rejected invalid range: {e}")
            print()

        print("=" * 70)
        print("All Tests Completed")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_commission_calculation())
