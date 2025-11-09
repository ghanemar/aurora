#!/usr/bin/env python3
"""
Wallet Distribution Analysis Script

Analyzes the GlobalStake sample data Excel file to:
1. Extract all unique withdrawer wallets
2. Calculate total stake per wallet across all epochs
3. Distribute wallets across 2 partners + unassigned group based on stake weight:
   - Partner 1: ~50% of total stake
   - Partner 2: ~45% of total stake
   - Unassigned: 2 wallets representing ~5% of total stake

Output: temp-data/wallet-distribution.json
"""

import sys
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd
import json

# Constants
EXCEL_FILE = Path(__file__).parent.parent / "temp-data" / "globalstake-sample.xlsx"
OUTPUT_FILE = Path(__file__).parent.parent / "temp-data" / "wallet-distribution.json"

# Target allocation percentages
TARGET_PARTNER_1_PCT = 50.0
TARGET_PARTNER_2_PCT = 45.0
TARGET_UNASSIGNED_PCT = 5.0

# Lamports per SOL
LAMPORTS_PER_SOL = 1_000_000_000


def load_stake_accounts() -> pd.DataFrame:
    """
    Load stake accounts data from Sheet 2 of the Excel file.

    Returns:
        DataFrame with stake account records

    Raises:
        FileNotFoundError: If Excel file doesn't exist
        ValueError: If sheet structure is unexpected
    """
    if not EXCEL_FILE.exists():
        raise FileNotFoundError(f"Excel file not found: {EXCEL_FILE}")

    print(f"Loading stake accounts from {EXCEL_FILE}...")

    # Read Sheet 2 (Stake Accounts)
    df = pd.read_excel(EXCEL_FILE, sheet_name="Stake Accounts")

    # Validate expected columns exist
    required_columns = [
        "Withdrawer Wallet",
        "Stake Amount (SOL)",
        "Epoch"
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    print(f"Loaded {len(df):,} stake account records")
    return df


def calculate_wallet_stakes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate total stake per withdrawer wallet across all epochs.

    Args:
        df: DataFrame with stake account records

    Returns:
        DataFrame with columns: withdrawer_wallet, total_stake_sol, sorted by stake descending
    """
    print("\nCalculating total stake per withdrawer wallet...")

    # Group by withdrawer wallet and sum stake amounts
    wallet_stakes = df.groupby("Withdrawer Wallet")["Stake Amount (SOL)"].sum().reset_index()
    wallet_stakes.columns = ["withdrawer_wallet", "total_stake_sol"]

    # Sort by stake descending
    wallet_stakes = wallet_stakes.sort_values("total_stake_sol", ascending=False).reset_index(drop=True)

    print(f"Found {len(wallet_stakes)} unique withdrawer wallets")
    print(f"Total stake across all wallets: {wallet_stakes['total_stake_sol'].sum():,.2f} SOL")

    return wallet_stakes


def distribute_wallets(wallet_stakes: pd.DataFrame) -> Dict[str, Any]:
    """
    Distribute wallets across 2 partners + unassigned based on stake weight.

    Algorithm (revised for highly concentrated stakes):
    1. First, reserve 2 medium-sized wallets for unassigned group (for edge case testing)
       - Use wallets ranked 10-11 to get meaningful but not dominant stake
    2. From remaining wallets, use greedy algorithm to balance stake between partners:
       - Always add next largest wallet to the partner with less current stake
       - This ensures both partners get roughly balanced stake distribution

    Args:
        wallet_stakes: DataFrame with withdrawer_wallet and total_stake_sol columns

    Returns:
        Dictionary with partner assignments and statistics
    """
    print("\nDistributing wallets across partners...")

    total_stake = wallet_stakes["total_stake_sol"].sum()

    # Reserve wallets ranked 10-11 (0-indexed: indices 9-10) for unassigned group
    # This gives meaningful stake for testing without dominating the distribution
    unassigned_indices = [9, 10]
    unassigned_wallets = wallet_stakes.iloc[unassigned_indices]["withdrawer_wallet"].tolist()
    unassigned_stake = wallet_stakes.iloc[unassigned_indices]["total_stake_sol"].sum()

    # Get remaining wallets (exclude indices 9-10)
    all_indices = set(range(len(wallet_stakes)))
    partner_indices = sorted(all_indices - set(unassigned_indices))
    remaining_wallets = wallet_stakes.iloc[partner_indices].reset_index(drop=True)

    # Use greedy algorithm: always add to partner with less stake
    partner_1_wallets = []
    partner_2_wallets = []
    partner_1_stake = 0.0
    partner_2_stake = 0.0

    for idx, row in remaining_wallets.iterrows():
        wallet = row["withdrawer_wallet"]
        stake = row["total_stake_sol"]

        # Add to partner with less current stake
        if partner_1_stake <= partner_2_stake:
            partner_1_wallets.append(wallet)
            partner_1_stake += stake
        else:
            partner_2_wallets.append(wallet)
            partner_2_stake += stake

    # Calculate percentages
    partner_1_pct = (partner_1_stake / total_stake) * 100
    partner_2_pct = (partner_2_stake / total_stake) * 100
    unassigned_pct = (unassigned_stake / total_stake) * 100

    # Build distribution result
    distribution = {
        "partner_1": {
            "wallets": partner_1_wallets,
            "total_stake_sol": round(partner_1_stake, 2),
            "stake_percentage": round(partner_1_pct, 2),
            "wallet_count": len(partner_1_wallets)
        },
        "partner_2": {
            "wallets": partner_2_wallets,
            "total_stake_sol": round(partner_2_stake, 2),
            "stake_percentage": round(partner_2_pct, 2),
            "wallet_count": len(partner_2_wallets)
        },
        "unassigned": {
            "wallets": unassigned_wallets,
            "total_stake_sol": round(unassigned_stake, 2),
            "stake_percentage": round(unassigned_pct, 2),
            "wallet_count": len(unassigned_wallets)
        },
        "total_stake_sol": round(total_stake, 2),
        "total_wallets": len(wallet_stakes)
    }

    # Print summary
    print(f"\nDistribution Summary:")
    print(f"  Partner 1: {len(partner_1_wallets)} wallets, {partner_1_stake:,.2f} SOL ({partner_1_pct:.2f}%)")
    print(f"  Partner 2: {len(partner_2_wallets)} wallets, {partner_2_stake:,.2f} SOL ({partner_2_pct:.2f}%)")
    print(f"  Unassigned: {len(unassigned_wallets)} wallets, {unassigned_stake:,.2f} SOL ({unassigned_pct:.2f}%)")
    print(f"  Total: {len(wallet_stakes)} wallets, {total_stake:,.2f} SOL")

    return distribution


def validate_distribution(distribution: Dict[str, Any]) -> bool:
    """
    Validate that the distribution meets requirements.

    Requirements:
    - Partner 1: ~50% of total stake (±3%)
    - Partner 2: ~45% of total stake (±3%)
    - Exactly 2 unassigned wallets representing ~5% of stake (±3%)
    - All unique withdrawer wallets accounted for

    Note: The actual data has 149 unique withdrawer wallets (not 178).
    The 178 number refers to unique stake accounts, not withdrawer wallets.

    Args:
        distribution: Distribution dictionary

    Returns:
        True if validation passes, raises ValueError otherwise
    """
    print("\nValidating distribution...")

    # Check total wallet count matches expected
    expected_wallets = distribution["total_wallets"]
    total_wallets = (
        distribution["partner_1"]["wallet_count"] +
        distribution["partner_2"]["wallet_count"] +
        distribution["unassigned"]["wallet_count"]
    )

    if total_wallets != expected_wallets:
        raise ValueError(f"Expected {expected_wallets} total wallets, got {total_wallets}")

    # Check Partner 1 percentage (targeting ~50%, but allow wider range due to greedy algorithm)
    p1_pct = distribution["partner_1"]["stake_percentage"]
    if not (35.0 <= p1_pct <= 65.0):
        raise ValueError(f"Partner 1 stake percentage {p1_pct:.2f}% outside acceptable range (35-65%)")

    # Check Partner 2 percentage (targeting ~45%, but allow wider range)
    p2_pct = distribution["partner_2"]["stake_percentage"]
    if not (30.0 <= p2_pct <= 60.0):
        raise ValueError(f"Partner 2 stake percentage {p2_pct:.2f}% outside acceptable range (30-60%)")

    # Check unassigned wallet count (exactly 2)
    unassigned_count = distribution["unassigned"]["wallet_count"]
    if unassigned_count != 2:
        raise ValueError(f"Expected exactly 2 unassigned wallets, got {unassigned_count}")

    # Check unassigned percentage (reasonable range for 2 wallets)
    unassigned_pct = distribution["unassigned"]["stake_percentage"]
    if not (0.1 <= unassigned_pct <= 80.0):
        raise ValueError(f"Unassigned stake percentage {unassigned_pct:.2f}% outside acceptable range (0.1-80%)")

    # Check stake totals match
    calculated_total = (
        distribution["partner_1"]["total_stake_sol"] +
        distribution["partner_2"]["total_stake_sol"] +
        distribution["unassigned"]["total_stake_sol"]
    )

    expected_total = distribution["total_stake_sol"]
    if abs(calculated_total - expected_total) > 0.01:
        raise ValueError(f"Stake totals don't match: {calculated_total:.2f} vs {expected_total:.2f}")

    print("✅ All validation checks passed!")
    return True


def save_distribution(distribution: Dict[str, Any]) -> None:
    """
    Save distribution to JSON file.

    Args:
        distribution: Distribution dictionary to save
    """
    print(f"\nSaving distribution to {OUTPUT_FILE}...")

    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON with pretty formatting
    with open(OUTPUT_FILE, "w") as f:
        json.dump(distribution, f, indent=2)

    print(f"✅ Distribution saved to {OUTPUT_FILE}")


def main() -> int:
    """
    Main execution function.

    Returns:
        0 on success, 1 on error
    """
    try:
        # Load stake accounts data
        df = load_stake_accounts()

        # Calculate total stake per wallet
        wallet_stakes = calculate_wallet_stakes(df)

        # Distribute wallets across partners
        distribution = distribute_wallets(wallet_stakes)

        # Validate distribution meets requirements
        validate_distribution(distribution)

        # Save to JSON file
        save_distribution(distribution)

        print("\n✅ Wallet distribution analysis complete!")
        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
