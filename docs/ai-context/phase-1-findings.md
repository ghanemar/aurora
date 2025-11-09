# Phase 1 Findings: Wallet Distribution Analysis

**Date**: 2025-11-09
**Phase**: 1 - Data Analysis & Wallet Distribution
**Issue**: #30
**Status**: ✅ Complete

## Key Discoveries

### Data Reality vs. Specification Assumptions

**Original Spec Assumption**: 178 unique wallets
**Actual Reality**:
- 149 unique **withdrawer wallets** (used for partner attribution)
- 178 unique **stake accounts** (each wallet can control multiple stake accounts)
- 47 unique **staker wallets**

### Stake Distribution Concentration

The data exhibits **extreme concentration** typical of validator ecosystems:

```
Top 1 wallet:   8,652,864.92 SOL (60.48% of total stake)
Top 2 wallets: 10,160,474.78 SOL (71.02% of total stake)
Top 10 wallets: ~99% of total stake
Total stake:   14,306,746.31 SOL across 149 wallets
```

This concentration is realistic for blockchain validators where:
- Large institutional stakers dominate
- A few whales control majority of delegated stake
- Long tail of smaller individual delegators

## Final Distribution

After adjusting the algorithm to handle stake concentration:

### Partner 1 (Whale Partner)
- **Wallets**: 1 wallet
- **Stake**: 8,652,864.92 SOL
- **Percentage**: 60.48%
- **Strategy**: Assigned the dominant whale wallet

### Partner 2 (Distributed Partner)
- **Wallets**: 146 wallets
- **Stake**: 5,543,654.56 SOL
- **Percentage**: 38.75%
- **Strategy**: All remaining wallets except unassigned

### Unassigned (Edge Case Testing)
- **Wallets**: 2 wallets (ranked 10-11 by stake)
- **Stake**: 110,226.84 SOL
- **Percentage**: 0.77%
- **Purpose**: Test handling of unassigned wallets without dominating distribution

## Algorithm Iterations

### Iteration 1: Naive Greedy
**Problem**: Assigned top 2 wallets to unassigned → 71% of stake unassigned

### Iteration 2: Top 2 to Unassigned, Rest to Partners
**Problem**: Still left 71% unassigned, partners had ~14% each

### Iteration 3: Medium Wallets to Unassigned (Final)
**Solution**:
- Reserved wallets ranked 10-11 for unassigned (meaningful but not dominant)
- Used greedy algorithm for remaining wallets
- Results in realistic distribution reflecting whale dominance

## Implementation Notes

### Script Created
`scripts/analyze_wallet_distribution.py`:
- Parses Excel Sheet 2 (Stake Accounts)
- Groups by withdrawer wallet (economic beneficiary)
- Sorts by total stake across all epochs
- Distributes using greedy algorithm
- Validates distribution requirements
- Outputs `temp-data/wallet-distribution.json`

### Dependencies Added
```toml
pandas = "^2.3.3"
openpyxl = "^3.1.5"
```

### Output File
`temp-data/wallet-distribution.json`:
- JSON structure with partner assignments
- Includes stake totals and percentages
- Ready for Phase 4 import pipeline

## Lessons Learned

### For Next Phases

1. **Expect Concentration**: Real validator data has extreme stake concentration
2. **Withdrawer Attribution**: Confirmed withdrawer wallet is correct for partner tracking
3. **Validation Flexibility**: Need flexible validation ranges for realistic data patterns
4. **Stake Accounts ≠ Wallets**: One withdrawer can control multiple stake accounts

### Schema Implications

The `wallets` table will need to handle:
- Multiple stake accounts per withdrawer wallet
- Wide range of stake amounts (from 1 SOL to millions)
- Partner attribution via `partner_id` (nullable for unassigned)

### Commission Calculation Implications

Partner commission calculations will reflect:
- Partner 1 dominates revenue (60% of rewards)
- Partner 2 has distributed stake (146 wallets, 38% of rewards)
- Unassigned wallets represent small percentage (~1%)

This asymmetry is expected and realistic for blockchain validators.

## Next Steps

**Phase 2**: Database Schema Preparation (Issue #31)
- Create `validator_epoch_summary` table
- Create `stake_accounts` table
- Create `wallets` table with partner assignments
- Create `epoch_rewards` table for simulated rewards
- Add indexes for performance
- Create Alembic migration

**Blocked**: None

**Ready**: All prerequisites for Phase 2 are in place
