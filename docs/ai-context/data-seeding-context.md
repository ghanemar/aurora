# AI Context: GlobalStake Sample Data Seeding

**Purpose**: This document provides AI-specific context for implementing the Sample Data Seeding milestone.

**⚠️ AI agents working on Issues #30-#35 MUST read this file before starting implementation.**

---

## Quick Reference

### Core Documents
1. **Milestone Spec**: `/docs/specs/milestone-sample-data-seeding.md` - Complete implementation plan
2. **Excel File**: `temp-data/globalstake-sample.xlsx` - Source data (2 sheets, 61 epochs, 178 wallets)
3. **Project Structure**: `/docs/ai-context/project-structure.md` - Tech stack and file organization

### Key Decisions
- **Wallet Attribution**: Use **withdrawer wallet** for partner identification (economic beneficiary)
- **Partner Distribution**: Stake-weighted (Partner 1: 50%, Partner 2: 45%, Unassigned: 5%)
- **Rewards Model**: Simulated 5% APY (~73 epochs/year on Solana)
- **Commission Basis**: Proportional to partner's share of total active stake

---

## Data Structure Understanding

### Excel File Structure

**Sheet 1: Validator Summary**
- 61 rows (epochs 800-860)
- Epoch-level aggregations (total stake, stakers count, etc.)
- Validator identity: vote_pubkey, node_pubkey, 5% commission

**Sheet 2: Stake Accounts**
- 10,858 rows (178 wallets × 61 epochs)
- Per-wallet, per-epoch stake positions
- **Critical columns**:
  - `Staker Wallet` (Column D): Controls delegation
  - `Withdrawer Wallet` (Column E): **USE THIS** for partner attribution
  - `Stake Amount (SOL)` (Column F): Convert to lamports (× 1e9)
  - `Activation Epoch` (Column H): When stake became active
  - `Deactivation Epoch` (Column I): NULL if still active

### Stake State Lifecycle

```
Inactive → Activating → Active → Deactivating → Deactivated
            (warmup)            (cooldown)

Rewards earned ONLY in "Active" state:
- activation_epoch < current_epoch
- deactivation_epoch IS NULL OR deactivation_epoch > current_epoch
```

---

## Implementation Guidelines

### Phase-by-Phase Context

#### Phase 1: Wallet Distribution Analysis

**Goal**: Distribute 178 unique withdrawer wallets across 2 partners + unassigned group

**Approach**:
1. Extract all unique `Withdrawer Wallet` addresses from Sheet 2
2. Sum total stake across all epochs for each wallet
3. Sort descending by total stake
4. Allocate top wallets to Partner 1 until ~50% of total stake reached
5. Allocate next wallets to Partner 2 until ~45% reached
6. Assign 2 largest remaining wallets to "unassigned" (~5%)

**Output**: `wallet-distribution.json` with structure:
```json
{
  "partner_1": {
    "wallets": ["ABC123...", "DEF456..."],
    "total_stake_sol": 117268.41,
    "stake_percentage": 50.0
  },
  "partner_2": { ... },
  "unassigned": { ... }
}
```

**Files to Create**:
- `scripts/analyze_wallet_distribution.py`

---

#### Phase 2: Database Schema

**Goal**: Extend Aurora schema to accommodate sample data

**Key Tables to Create**:

1. **`validator_epoch_summary`** - Epoch-level metrics
   - Links to `validators` table
   - Stores total stake, staker count per epoch
   - UNIQUE constraint on (validator_id, epoch)

2. **`stake_accounts`** - Per-wallet, per-epoch positions
   - Links to `validators`, `wallets` (staker + withdrawer)
   - Stores stake amount, activation/deactivation epochs
   - UNIQUE constraint on (stake_account_pubkey, epoch)

3. **`wallets`** - Wallet registry with partner assignments
   - Stores pubkey, chain_id, partner_id (nullable for unassigned)
   - Links to `partners` table

4. **`epoch_rewards`** - Simulated reward data
   - Stores total rewards, validator commission, staker rewards
   - `is_simulated` flag = TRUE
   - JSONB `simulation_params` for auditability

**Migration Strategy**:
- Use Alembic for schema changes
- Add indexes for query performance:
  - `stake_accounts(epoch)` - Time-series queries
  - `stake_accounts(withdrawer_wallet_id)` - Partner attribution
  - `stake_accounts(stake_account_pubkey)` - Unique lookups

**Files to Create**:
- `alembic/versions/<timestamp>_add_sample_data_tables.py`
- `src/core/models/sample_data.py` (ORM models)

---

#### Phase 3: Rewards Simulation

**Goal**: Generate realistic epoch rewards based on 5% APY assumption

**Formula**:
```python
ANNUAL_APY = 0.05  # 5% annual yield
EPOCHS_PER_YEAR = 73  # Approximate for Solana
VALIDATOR_COMMISSION_RATE = 0.05  # 5%

# Per-epoch calculation
epoch_rate = ANNUAL_APY / EPOCHS_PER_YEAR  # ≈ 0.0685% per epoch
total_epoch_rewards = active_stake_lamports * epoch_rate
validator_commission = total_epoch_rewards * 0.05
staker_rewards = total_epoch_rewards * 0.95
```

**Per-Wallet Rewards**:
```python
wallet_share = wallet_stake / total_active_stake
wallet_rewards = staker_rewards * wallet_share
```

**Implementation**:
- Create `rewards_simulator.py` module
- Store results in `epoch_rewards` table with `is_simulated=TRUE`
- Track simulation parameters in JSONB for transparency

**Files to Create**:
- `src/core/services/rewards_simulator.py`
- `tests/unit/test_rewards_simulator.py`

---

#### Phase 4: Data Import Pipeline

**Goal**: Parse Excel → Transform → Load into Aurora database

**Workflow**:
1. **Read Excel**: Use pandas to load both sheets
2. **Validate**: Check row counts (61 epochs, 10,858 stake accounts)
3. **Import Validator**: Create single validator record
4. **Import Wallets**: Create all unique staker + withdrawer wallets
5. **Link Partners**: Apply assignments from `wallet-distribution.json`
6. **Import Summaries**: Transform Sheet 1 → `validator_epoch_summary`
7. **Import Stakes**: Transform Sheet 2 → `stake_accounts`
8. **Generate Rewards**: Use Phase 3 simulator for all 61 epochs
9. **Validate**: Verify totals, foreign keys, uniqueness

**Critical Conversions**:
- SOL to lamports: `lamports = sol_amount * 1_000_000_000`
- Handle NULL `deactivation_epoch` correctly (still active)

**Transaction Safety**:
- Wrap entire import in async transaction
- Rollback on any validation failure
- Report progress (e.g., "Importing epoch 820/860...")

**Files to Create**:
- `scripts/seed_globalstake_sample.py`
- `scripts/load_wallet_distribution.py`
- `scripts/validate_import.py`

---

#### Phase 5: Commission Calculation

**Goal**: Calculate partner commissions using withdrawer-based attribution

**Commission Model**:
```python
# For each epoch and partner:
partner_active_stake = SUM(stake_lamports)
    FROM stake_accounts sa
    JOIN wallets w ON sa.withdrawer_wallet_id = w.wallet_id
    WHERE w.partner_id = ?
      AND sa.epoch = ?
      AND (sa.deactivation_epoch IS NULL OR sa.deactivation_epoch > sa.epoch)

stake_proportion = partner_active_stake / total_active_stake
partner_share_of_rewards = staker_rewards * stake_proportion
partner_commission = partner_share_of_rewards * partner_commission_rate
```

**Validation**:
- Run calculation twice
- Compare results byte-for-byte (determinism check)
- Generate comprehensive validation report

**Unassigned Wallets**:
- 2 wallets have `partner_id = NULL`
- Calculate their rewards separately
- Report as "unassigned revenue" in validation report

**Files to Create**:
- `scripts/calculate_commissions.py`
- `scripts/generate_validation_report.py`
- `temp-data/commission-validation-report.json` (output)

---

#### Phase 6: Edge Case Testing

**Goal**: Validate system handles real-world stake state complexities

**Test Scenarios**:

1. **Activating Stake (Warmup)**:
   - Find: `activation_epoch = current_epoch`
   - Assert: Excluded from active stake (no rewards yet)
   - Query: `WHERE activation_epoch < current_epoch`

2. **Deactivating Stake (Cooldown)**:
   - Find: `deactivation_epoch = current_epoch`
   - Assert: Included in active stake (earns last epoch rewards)
   - Query: `WHERE deactivation_epoch IS NULL OR deactivation_epoch > current_epoch`

3. **Unassigned Wallets**:
   - Find: `partner_id IS NULL`
   - Assert: Commission calculation doesn't fail
   - Verify: Tracked separately in reports

4. **Stake Transitions**:
   - Find wallet that deactivates mid-range
   - Assert: Partner commission decreases after deactivation
   - Verify: Smooth transition without errors

5. **Epoch Range Consistency**:
   - For all 61 epochs:
     - Assert: Commission records exist
     - Verify: Stake totals balance

**Files to Create**:
- `tests/integration/test_sample_data_edge_cases.py`
- `scripts/run_edge_case_tests.py`
- `temp-data/edge-case-test-report.json`

---

## Common Pitfalls & Solutions

### Pitfall 1: Using Staker Wallet Instead of Withdrawer
**Problem**: Staker controls delegation, not rewards
**Solution**: Always use `withdrawer_wallet_id` for partner attribution
**Query**: `JOIN wallets w ON sa.withdrawer_wallet_id = w.wallet_id`

### Pitfall 2: Including Activating Stake in Rewards
**Problem**: Stake in warmup period doesn't earn yet
**Solution**: Filter `WHERE activation_epoch < current_epoch`

### Pitfall 3: Excluding Deactivating Stake from Rewards
**Problem**: Stake earns rewards during deactivation epoch
**Solution**: Include if `deactivation_epoch IS NULL OR deactivation_epoch > current_epoch`

### Pitfall 4: Lamport Conversion Errors
**Problem**: Excel shows SOL, database stores lamports
**Solution**: Always multiply by 1e9, use BIGINT for storage

### Pitfall 5: Forgetting Unassigned Wallets
**Problem**: Commission calculation fails for NULL partner_id
**Solution**: Handle unassigned gracefully, track separately

---

## Testing Strategy

### Unit Tests
- Rewards simulation formulas
- Lamport conversion functions
- Stake state filtering logic
- Partner attribution queries

### Integration Tests
- Full data import pipeline
- Commission calculation across epochs
- Edge case scenarios (activating/deactivating)
- Determinism validation

### Validation Tests
- Excel row counts match database
- Stake totals reconcile (summary vs details)
- All foreign keys valid
- Unique constraints enforced
- Commission totals match expected proportions

---

## Performance Considerations

### Import Optimization
- Use bulk inserts for stake accounts (10,858 rows)
- Batch wallet creation (178 wallets)
- Create indexes AFTER import (faster bulk load)

### Query Optimization
- Index on `stake_accounts(epoch)` for time-series
- Index on `stake_accounts(withdrawer_wallet_id)` for attribution
- Use `SUM()` aggregations efficiently
- Consider materialized views for frequent queries

### Memory Management
- Stream Excel parsing if file size grows
- Process epochs in batches if needed
- Use async operations for database writes

---

## Debugging Tips

### Validation Failures
```python
# Check row counts
assert len(df_summary) == 61, "Expected 61 epochs"
assert len(df_stakes) == 10858, "Expected 10,858 stake accounts"

# Verify wallet distribution
total_stake = sum(partner1_stake + partner2_stake + unassigned_stake)
assert abs(total_stake - 234536.82) < 0.01, "Stake totals don't match"

# Check foreign keys
orphaned = await session.execute(
    select(StakeAccount).where(StakeAccount.withdrawer_wallet_id.is_(None))
)
assert orphaned.scalars().first() is None, "Found orphaned stake accounts"
```

### Commission Calculation Issues
```python
# Verify active stake filtering
active_stakes = await session.execute(
    select(StakeAccount)
    .where(StakeAccount.epoch == 820)
    .where(StakeAccount.activation_epoch < 820)
    .where(
        or_(
            StakeAccount.deactivation_epoch.is_(None),
            StakeAccount.deactivation_epoch > 820
        )
    )
)

# Check stake totals
summary = await get_epoch_summary(session, 820)
calculated_total = sum(stake.stake_lamports for stake in active_stakes)
assert abs(summary.total_active_stake_lamports - calculated_total) < 1000
```

### Edge Case Debugging
```python
# Find activating stakes
activating = await session.execute(
    select(StakeAccount)
    .where(StakeAccount.epoch == 810)
    .where(StakeAccount.activation_epoch == 810)
)
print(f"Found {len(list(activating))} activating stakes at epoch 810")

# Find deactivating stakes
deactivating = await session.execute(
    select(StakeAccount)
    .where(StakeAccount.epoch == 850)
    .where(StakeAccount.deactivation_epoch == 850)
)
print(f"Found {len(list(deactivating))} deactivating stakes at epoch 850")
```

---

## Success Metrics

### Data Integrity
- [ ] 61 epochs imported (800-860)
- [ ] 10,858 stake account records
- [ ] 178 unique wallets (both staker + withdrawer roles)
- [ ] All foreign keys valid
- [ ] No orphaned records

### Partner Distribution
- [ ] Partner 1: ~50% of total stake
- [ ] Partner 2: ~45% of total stake
- [ ] Unassigned: 2 wallets with ~5% stake

### Commission Accuracy
- [ ] Withdrawer-based attribution working
- [ ] Stake-weighted distribution correct
- [ ] Deterministic results (identical on re-run)
- [ ] Unassigned wallets tracked separately

### Edge Case Handling
- [ ] Activating stake excluded from rewards
- [ ] Deactivating stake included in rewards
- [ ] Unassigned wallets don't break calculations
- [ ] Stake transitions handled smoothly
- [ ] All 61 epochs consistent

---

## Next Agent Handoff

When completing this milestone and handing off to next session:

1. **Update HANDOFF.md**:
   - Mark completed phases
   - Document any deviations from spec
   - Note any issues encountered
   - List next steps

2. **Commit Work**:
   - Branch: `feature/milestone-sample-data-seeding`
   - Commit message: "feat: [Phase N] - [Phase Name]"
   - Push to remote

3. **Provide Summary**:
   - What was completed
   - What's remaining
   - Any blockers or concerns
   - Recommended next actions

---

## Related Documents

- **Milestone Spec**: `/docs/specs/milestone-sample-data-seeding.md`
- **Project Structure**: `/docs/ai-context/project-structure.md`
- **Database Schema**: `/docs/database-schema.md`
- **HANDOFF Template**: `/docs/ai-context/HANDOFF.md`

---

**Document Version**: 1.0
**Last Updated**: 2025-11-07
**For Issues**: #30, #31, #32, #33, #34, #35
**Branch**: `feature/milestone-sample-data-seeding`
