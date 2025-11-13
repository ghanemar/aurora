"""Seed Aurora database with GlobalStake sample data.

This script imports real Solana validator data from temp-data/globalstake-sample.xlsx
and generates simulated rewards for testing the commission calculation engine.

Data includes:
- 61 epochs (800-860) of historical validator data
- 149 unique withdrawer wallets
- 10,858 stake account records
- Simulated 5% APY rewards

Usage:
    python scripts/seed_globalstake_sample.py [--dry-run]
"""

import asyncio
import json
import sys
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.models import Partners, PartnerWallet
from src.core.models.sample_data import (
    SampleEpochReward,
    SampleStakeAccount,
    SampleValidatorEpochSummary,
)
from src.core.services.rewards_simulator import RewardsSimulator
from src.db import async_session_factory

# Constants from the sample data
VALIDATOR_VOTE_PUBKEY = "FdGcvmbpebUwYA3vSywnagsaC3Tq3pAVmcR6VoxVcdV9"
VALIDATOR_NODE_PUBKEY = "BCeczqpTRPigndHVJu1KEzno1Uhb4hjrE7ttmAndrV1p"
VALIDATOR_COMMISSION = 5  # 5% commission
CHAIN_ID = "solana-mainnet"

# File paths
EXCEL_FILE = Path("temp-data/globalstake-sample.xlsx")
WALLET_DISTRIBUTION_FILE = Path("temp-data/wallet-distribution.json")


class DataImporter:
    """Handles the import of GlobalStake sample data."""

    def __init__(self, session: AsyncSession, dry_run: bool = False):
        """Initialize the data importer.

        Args:
            session: Database session
            dry_run: If True, only validate data without writing to database
        """
        self.session = session
        self.dry_run = dry_run
        self.simulator = RewardsSimulator()
        self.partner_wallet_map: dict[str, uuid.UUID] = {}  # wallet_pubkey -> partner_id
        self.wallet_id_map: dict[str, uuid.UUID] = {}  # wallet_pubkey -> wallet_id
        self.epoch_summary_map: dict[int, uuid.UUID] = {}  # epoch -> summary_id

    async def run(self) -> None:
        """Execute the full data import pipeline."""
        print("=" * 70)
        print("GlobalStake Sample Data Importer")
        print("=" * 70)
        print(f"Mode: {'DRY RUN (validation only)' if self.dry_run else 'LIVE IMPORT'}")
        print()

        try:
            # Step 1: Load and validate Excel file
            print("[1/8] Loading and validating Excel file...")
            df_summary, df_stakes = self.load_excel_file()
            print(f"  ✓ Loaded {len(df_summary)} epoch summaries")
            print(f"  ✓ Loaded {len(df_stakes)} stake account records")
            print()

            # Step 2: Load wallet distribution
            print("[2/8] Loading wallet distribution...")
            wallet_distribution = self.load_wallet_distribution()
            print(f"  ✓ Partner 1: {wallet_distribution['partner_1']['wallet_count']} wallets")
            print(f"  ✓ Partner 2: {wallet_distribution['partner_2']['wallet_count']} wallets")
            print(f"  ✓ Unassigned: {wallet_distribution['unassigned']['wallet_count']} wallets")
            print()

            if self.dry_run:
                print("DRY RUN MODE: Skipping database operations")
                print("✓ All validations passed!")
                return

            # Step 3: Create or get partners
            print("[3/8] Setting up partners...")
            partner1, partner2, unassigned_partner = await self.setup_partners()
            print(f"  ✓ Partner 1: {partner1.partner_name} (ID: {partner1.partner_id})")
            print(f"  ✓ Partner 2: {partner2.partner_name} (ID: {partner2.partner_id})")
            print(f"  ✓ Unassigned: {unassigned_partner.partner_name} (ID: {unassigned_partner.partner_id})")
            print()

            # Step 4: Import all unique wallets
            print("[4/8] Importing wallets...")
            await self.import_wallets(df_stakes, wallet_distribution, partner1, partner2, unassigned_partner)
            print(f"  ✓ Imported {len(self.wallet_id_map)} unique wallets")
            print()

            # Step 5: Import validator epoch summaries
            print("[5/8] Importing validator epoch summaries...")
            await self.import_epoch_summaries(df_summary)
            print(f"  ✓ Imported {len(df_summary)} epoch summaries")
            print()

            # Step 6: Import stake accounts
            print("[6/8] Importing stake accounts...")
            await self.import_stake_accounts(df_stakes)
            print(f"  ✓ Imported {len(df_stakes)} stake account records")
            print()

            # Step 7: Generate simulated rewards
            print("[7/8] Generating simulated rewards...")
            epochs = sorted(df_summary["Epoch"].unique())
            await self.generate_simulated_rewards(df_summary, epochs)
            print(f"  ✓ Generated rewards for {len(epochs)} epochs")
            print()

            # Step 8: Validate data integrity
            print("[8/8] Validating data integrity...")
            await self.validate_import(df_summary, df_stakes)
            print("  ✓ All integrity checks passed")
            print()

            await self.session.commit()
            print("=" * 70)
            print("✓ Import completed successfully!")
            print("=" * 70)

        except Exception as e:
            print(f"\n✗ Error during import: {e}")
            if not self.dry_run:
                await self.session.rollback()
                print("  Rolled back all changes")
            raise

    def load_excel_file(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Load and validate Excel file structure.

        Returns:
            Tuple of (summary_df, stakes_df)

        Raises:
            FileNotFoundError: If Excel file not found
            ValueError: If data structure is invalid
        """
        if not EXCEL_FILE.exists():
            raise FileNotFoundError(f"Excel file not found: {EXCEL_FILE}")

        # Load both sheets
        df_summary = pd.read_excel(EXCEL_FILE, sheet_name="Validator Summary")
        df_stakes = pd.read_excel(EXCEL_FILE, sheet_name="Stake Accounts")

        # Validate structure
        if len(df_summary) != 61:
            raise ValueError(f"Expected 61 epoch summaries, got {len(df_summary)}")

        if len(df_stakes) != 10858:
            raise ValueError(f"Expected 10,858 stake account records, got {len(df_stakes)}")

        # Validate columns exist
        required_summary_cols = ["Epoch", "Total Active Stake (SOL)", "Total Stakers"]
        for col in required_summary_cols:
            if col not in df_summary.columns:
                raise ValueError(f"Missing required column in summary: {col}")

        required_stakes_cols = [
            "Epoch",
            "Stake Account Pubkey",
            "Staker Wallet",
            "Withdrawer Wallet",
            "Stake Amount (SOL)",
        ]
        for col in required_stakes_cols:
            if col not in df_stakes.columns:
                raise ValueError(f"Missing required column in stakes: {col}")

        return df_summary, df_stakes

    def load_wallet_distribution(self) -> dict[str, Any]:
        """Load wallet distribution from JSON file.

        Returns:
            Wallet distribution dictionary

        Raises:
            FileNotFoundError: If distribution file not found
        """
        if not WALLET_DISTRIBUTION_FILE.exists():
            raise FileNotFoundError(
                f"Wallet distribution file not found: {WALLET_DISTRIBUTION_FILE}"
            )

        with open(WALLET_DISTRIBUTION_FILE) as f:
            return json.load(f)

    async def setup_partners(self) -> tuple[Partners, Partners, Partners]:
        """Create or get partner records.

        Returns:
            Tuple of (partner1, partner2, unassigned_partner)
        """
        # Check if partners already exist
        result = await self.session.execute(
            select(Partners).where(
                Partners.partner_name.in_([
                    "GlobalStake Partner 1",
                    "GlobalStake Partner 2",
                    "Unassigned"
                ])
            )
        )
        existing_partners = {p.partner_name: p for p in result.scalars()}

        # Create or get Partner 1
        if "GlobalStake Partner 1" in existing_partners:
            partner1 = existing_partners["GlobalStake Partner 1"]
        else:
            partner1 = Partners(
                partner_name="GlobalStake Partner 1",
                contact_email="partner1@globalstake.example.com",
                is_active=True,
            )
            self.session.add(partner1)
            await self.session.flush()

        # Create or get Partner 2
        if "GlobalStake Partner 2" in existing_partners:
            partner2 = existing_partners["GlobalStake Partner 2"]
        else:
            partner2 = Partners(
                partner_name="GlobalStake Partner 2",
                contact_email="partner2@globalstake.example.com",
                is_active=True,
            )
            self.session.add(partner2)
            await self.session.flush()

        # Create or get Unassigned partner (for wallets not attributed to partners)
        if "Unassigned" in existing_partners:
            unassigned_partner = existing_partners["Unassigned"]
        else:
            unassigned_partner = Partners(
                partner_name="Unassigned",
                contact_email="unassigned@globalstake.example.com",
                is_active=False,  # Mark as inactive since these are edge case wallets
            )
            self.session.add(unassigned_partner)
            await self.session.flush()

        return partner1, partner2, unassigned_partner

    async def import_wallets(
        self,
        df_stakes: pd.DataFrame,
        wallet_distribution: dict[str, Any],
        partner1: Partners,
        partner2: Partners,
        unassigned_partner: Partners,
    ) -> None:
        """Import all unique wallets with partner assignments.

        Args:
            df_stakes: Stake accounts dataframe
            wallet_distribution: Wallet distribution from Phase 1
            partner1: Partner 1 instance
            partner2: Partner 2 instance
            unassigned_partner: Unassigned partner for edge case wallets
        """
        # Build partner assignment map
        for wallet in wallet_distribution["partner_1"]["wallets"]:
            self.partner_wallet_map[wallet] = partner1.partner_id

        for wallet in wallet_distribution["partner_2"]["wallets"]:
            self.partner_wallet_map[wallet] = partner2.partner_id

        # Unassigned wallets go to the unassigned partner
        for wallet in wallet_distribution["unassigned"]["wallets"]:
            self.partner_wallet_map[wallet] = unassigned_partner.partner_id

        # Get all unique wallets (both staker and withdrawer)
        unique_stakers = df_stakes["Staker Wallet"].unique()
        unique_withdrawers = df_stakes["Withdrawer Wallet"].unique()
        all_unique_wallets = set(list(unique_stakers) + list(unique_withdrawers))

        # Import each unique wallet
        from datetime import date

        for wallet_pubkey in all_unique_wallets:
            # For wallets not in the distribution (like staker wallets),
            # assign them to the unassigned partner
            partner_id = self.partner_wallet_map.get(wallet_pubkey, unassigned_partner.partner_id)

            # Check if wallet already exists
            result = await self.session.execute(
                select(PartnerWallet).where(
                    PartnerWallet.wallet_address == wallet_pubkey,
                    PartnerWallet.chain_id == CHAIN_ID,
                )
            )
            existing_wallet = result.scalar_one_or_none()

            if existing_wallet:
                wallet_id = existing_wallet.wallet_id
            else:
                # Use epoch 800 as introduced_date (start of our data range)
                wallet = PartnerWallet(
                    wallet_address=wallet_pubkey,
                    chain_id=CHAIN_ID,
                    partner_id=partner_id,
                    introduced_date=date(2024, 1, 1),  # Placeholder date
                    is_active=True,
                )
                self.session.add(wallet)
                await self.session.flush()
                wallet_id = wallet.wallet_id

            self.wallet_id_map[wallet_pubkey] = wallet_id

    async def import_epoch_summaries(self, df_summary: pd.DataFrame) -> None:
        """Import validator epoch summaries.

        Args:
            df_summary: Epoch summaries dataframe
        """
        # Create a map of epoch -> summary_id for stake account FK references
        self.epoch_summary_map: dict[int, uuid.UUID] = {}

        for _, row in df_summary.iterrows():
            summary = SampleValidatorEpochSummary(
                epoch=int(row["Epoch"]),
                validator_vote_pubkey=VALIDATOR_VOTE_PUBKEY,
                validator_node_pubkey=VALIDATOR_NODE_PUBKEY,
                commission_bps=VALIDATOR_COMMISSION * 100,  # 5% -> 500 bps
                total_delegated_stake_lamports=int(row["Total Delegated Stake (SOL)"] * 1e9),
                total_active_stake_lamports=int(row["Total Active Stake (SOL)"] * 1e9),
                total_stakers=int(row["Total Stakers"]),
            )
            self.session.add(summary)
            await self.session.flush()  # Flush to get the summary_id

            # Store mapping for FK references
            self.epoch_summary_map[summary.epoch] = summary.summary_id

        await self.session.flush()

    async def import_stake_accounts(self, df_stakes: pd.DataFrame) -> None:
        """Import stake account records.

        Args:
            df_stakes: Stake accounts dataframe
        """
        for _, row in df_stakes.iterrows():
            epoch = int(row["Epoch"])
            staker_wallet = row["Staker Wallet"]
            withdrawer_wallet = row["Withdrawer Wallet"]

            # Get epoch summary ID for FK
            epoch_summary_id = self.epoch_summary_map.get(epoch)
            if not epoch_summary_id:
                raise ValueError(f"Epoch summary not found for epoch {epoch}")

            # Get wallet IDs for FKs
            staker_wallet_id = self.wallet_id_map.get(staker_wallet)
            withdrawer_wallet_id = self.wallet_id_map.get(withdrawer_wallet)

            if not staker_wallet_id:
                raise ValueError(f"Staker wallet not found: {staker_wallet}")
            if not withdrawer_wallet_id:
                raise ValueError(f"Withdrawer wallet not found: {withdrawer_wallet}")

            # Handle deactivation epoch (may be NULL/NaN)
            deactivation_epoch = None
            if pd.notna(row.get("Deactivation Epoch")):
                deactivation_epoch = int(row["Deactivation Epoch"])

            stake_account = SampleStakeAccount(
                epoch_summary_id=epoch_summary_id,
                epoch=epoch,
                validator_vote_pubkey=VALIDATOR_VOTE_PUBKEY,
                stake_account_pubkey=row["Stake Account Pubkey"],
                staker_wallet_id=staker_wallet_id,
                withdrawer_wallet_id=withdrawer_wallet_id,
                stake_lamports=int(row["Stake Amount (SOL)"] * 1e9),
                activation_epoch=int(row["Activation Epoch"]),
                deactivation_epoch=deactivation_epoch,
            )
            self.session.add(stake_account)

        await self.session.flush()

    async def generate_simulated_rewards(
        self, df_summary: pd.DataFrame, epochs: list[int]
    ) -> None:
        """Generate simulated rewards for all epochs.

        Args:
            df_summary: Epoch summaries dataframe
            epochs: List of epochs to generate rewards for
        """
        for epoch in epochs:
            # Get epoch summary ID for FK
            epoch_summary_id = self.epoch_summary_map.get(epoch)
            if not epoch_summary_id:
                raise ValueError(f"Epoch summary not found for epoch {epoch}")

            # Get active stake for this epoch
            epoch_data = df_summary[df_summary["Epoch"] == epoch].iloc[0]
            active_stake_lamports = int(epoch_data["Total Active Stake (SOL)"] * 1e9)

            # Simulate rewards using Phase 3 engine
            rewards_result = self.simulator.simulate_epoch_rewards(
                active_stake_lamports=active_stake_lamports, epoch=epoch
            )

            # Create epoch reward record
            epoch_reward = SampleEpochReward(
                epoch_summary_id=epoch_summary_id,
                epoch=epoch,
                validator_vote_pubkey=VALIDATOR_VOTE_PUBKEY,
                total_epoch_rewards_lamports=rewards_result["total_epoch_rewards_lamports"],
                validator_commission_lamports=rewards_result["validator_commission_lamports"],
                staker_rewards_lamports=rewards_result["staker_rewards_lamports"],
                active_stake_lamports=rewards_result["active_stake_lamports"],
                is_simulated=True,
                simulation_params=rewards_result["simulation_params"],
            )
            self.session.add(epoch_reward)

        await self.session.flush()

    async def validate_import(
        self, df_summary: pd.DataFrame, df_stakes: pd.DataFrame
    ) -> None:
        """Validate imported data integrity.

        Args:
            df_summary: Epoch summaries dataframe
            df_stakes: Stake accounts dataframe

        Raises:
            ValueError: If validation fails
        """
        # Check epoch summaries count
        result = await self.session.execute(
            select(SampleValidatorEpochSummary).where(
                SampleValidatorEpochSummary.validator_vote_pubkey == VALIDATOR_VOTE_PUBKEY
            )
        )
        summaries_count = len(list(result.scalars()))
        if summaries_count != len(df_summary):
            raise ValueError(
                f"Epoch summaries mismatch: expected {len(df_summary)}, got {summaries_count}"
            )

        # Check stake accounts count
        result = await self.session.execute(
            select(SampleStakeAccount).where(
                SampleStakeAccount.validator_vote_pubkey == VALIDATOR_VOTE_PUBKEY
            )
        )
        stakes_count = len(list(result.scalars()))
        if stakes_count != len(df_stakes):
            raise ValueError(
                f"Stake accounts mismatch: expected {len(df_stakes)}, got {stakes_count}"
            )

        # Check epoch rewards count
        result = await self.session.execute(
            select(SampleEpochReward).where(
                SampleEpochReward.validator_vote_pubkey == VALIDATOR_VOTE_PUBKEY
            )
        )
        rewards_count = len(list(result.scalars()))
        expected_rewards = len(df_summary["Epoch"].unique())
        if rewards_count != expected_rewards:
            raise ValueError(
                f"Epoch rewards mismatch: expected {expected_rewards}, got {rewards_count}"
            )

        print(f"  ✓ Epoch summaries: {summaries_count}")
        print(f"  ✓ Stake accounts: {stakes_count}")
        print(f"  ✓ Epoch rewards: {rewards_count}")


async def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Seed GlobalStake sample data")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate data without importing to database",
    )
    args = parser.parse_args()

    async with async_session_factory() as session:
        importer = DataImporter(session, dry_run=args.dry_run)
        await importer.run()


if __name__ == "__main__":
    asyncio.run(main())
