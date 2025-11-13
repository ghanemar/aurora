# Milestone: GlobalStake Sample Data Seeding & Commission Testing

**Status**: Phases 1 & 2 Complete - Commission Calculation Implemented
**Priority**: High
**Target Branch**: `feature/milestone-sample-data-seeding`
**Estimated Effort**: ~9 hours
**Created**: 2025-11-07

---

## Executive Summary

Seed the Aurora database with real Solana validator data (61 epochs, 178 unique wallets) from `temp-data/globalstake-sample.xlsx` to validate the partner commission calculation engine with realistic data patterns. This milestone establishes a comprehensive test dataset including stake-weighted partner assignments and simulated epoch rewards (5% APY) to verify deterministic commission calculations.

### Key Objectives

1. **Import Real Data**: Load complete 61-epoch historical dataset (epochs 800-860) with 10,858 stake account records
2. **Partner Assignment**: Distribute 178 unique wallets across 2 partners based on stake weight (Partner 1: ~50%, Partner 2: ~45%, Unassigned: 2 wallets ~5%)
3. **Rewards Simulation**: Generate realistic epoch rewards using 5% APY assumption (~73 epochs/year on Solana)
4. **Commission Validation**: Calculate and verify deterministic partner commissions using withdrawer-based attribution
5. **Edge Case Testing**: Validate system handling of activating/deactivating stake and unassigned wallets

---

## Data Analysis Summary

### Source Data Structure

**File**: `temp-data/globalstake-sample.xlsx` (2 sheets)

#### Sheet 1: Validator Summary (Epoch-Level Aggregations)
- **Dimensions**: 62 rows × 14 columns (1 header + 61 data rows)
- **Grain**: One row per epoch for the validator
- **Primary Key**: Epoch (Column A)
- **Time Range**: Epochs 800-860 (61 epochs)
- **Key Columns**:
  - Validator Vote Pubkey: `FdGcvmbpebUwYA3vSywnagsaC3Tq3pAVmcR6VoxVcdV9`
  - Validator Node Pubkey: `BCeczqpTRPigndHVJu1KEzno1Uhb4hjrE7ttmAndrV1p`
  - Commission %: 5% (constant)
  - Total Delegated Stake: ~234.5K SOL (constant)
  - Total Active Stake: ~189-190K SOL (varies by epoch)
  - Total Stakers: 178 (constant)

#### Sheet 2: Stake Accounts (Granular Position Details)
- **Dimensions**: 10,859 rows × 11 columns (1 header + 10,858 data rows)
- **Grain**: One row per stake account per epoch
- **Composite Key**: (Validator Vote Pubkey, Epoch, Stake Account Pubkey)
- **Time Range**: Epochs 800-860 (61 epochs)
- **Distribution**: Exactly 178 stake accounts per epoch × 61 epochs = 10,858 rows
- **Key Columns**:
  - Stake Account Pubkey: Unique stake account address
  - **Staker Wallet**: Controls stake delegation
  - **Withdrawer Wallet**: Controls fund withdrawals (economic beneficiary) ⚠️ **USE FOR PARTNER ATTRIBUTION**
  - Stake Amount (SOL): Principal stake amount
  - Activation Epoch: When stake activated
  - Deactivation Epoch: When deactivation started (NULL if still active)

### Relationship Between Sheets

```sql
Validator Summary (Sheet 1) ←──[1:M]──→ Stake Accounts (Sheet 2)
    Epoch                                     Epoch
```

Each epoch in Sheet 1 has exactly 178 stake account records in Sheet 2.

### Wallet Attribution Decision

**Selected Approach**: **Withdrawer Wallet** for partner attribution

**Rationale**: In Solana staking, the withdrawer wallet is the economic beneficiary who can claim the stake principal + accumulated rewards. This makes it the appropriate identifier for partner commission tracking.

**Stake Account Mechanics**:
```
Stake Account (on-chain)
├─ Staker Authority: Can delegate/change validator
├─ Withdrawer Authority: Can withdraw principal + rewards ✅ ECONOMIC BENEFICIARY
└─ Balance: Original stake + accumulated rewards
```

---

## Implementation Phases

### Phase 1: Data Analysis & Wallet Distribution
**GitHub Issue**: #30
**Estimated Effort**: 1 hour
**Dependencies**: None

#### Tasks
1. Parse `temp-data/globalstake-sample.xlsx` using pandas/openpyxl
2. Extract all unique withdrawer wallets from Sheet 2
3. Calculate total stake per withdrawer wallet across all epochs
4. Sort wallets by total stake (descending)
5. Allocate wallets to partners based on stake weight:
   - **Partner 1**: Top wallets totaling ~50% of total stake
   - **Partner 2**: Next wallets totaling ~45% of total stake
   - **Unassigned**: 2 largest remaining wallets (~5% stake) for edge case testing
6. Generate `wallet-distribution.json` with assignments

#### Acceptance Criteria
- [ ] All 178 unique withdrawer wallets identified
- [ ] Stake weight calculated correctly for each wallet
- [ ] Partner 1 has ~50% of total stake
- [ ] Partner 2 has ~45% of total stake
- [ ] Exactly 2 unassigned wallets representing ~5% of stake
- [ ] `wallet-distribution.json` created with structure:
  ```json
  {
    "partner_1": {
      "wallets": ["wallet_address_1", "wallet_address_2", ...],
      "total_stake_sol": 117268.41,
      "stake_percentage": 50.0
    },
    "partner_2": {
      "wallets": ["wallet_address_N", ...],
      "total_stake_sol": 105541.57,
      "stake_percentage": 45.0
    },
    "unassigned": {
      "wallets": ["wallet_address_X", "wallet_address_Y"],
      "total_stake_sol": 11726.84,
      "stake_percentage": 5.0
    },
    "total_stake_sol": 234536.82,
    "total_wallets": 178
  }
  ```

#### Files to Create
- `scripts/analyze_wallet_distribution.py` - Wallet analysis and distribution script
- `temp-data/wallet-distribution.json` - Output file with partner assignments

---

### Phase 2: Database Schema Preparation
**GitHub Issue**: #31
**Estimated Effort**: 1 hour
**Dependencies**: None (can run parallel with Phase 1)

#### Tasks
1. Review existing Aurora schema against sample data requirements
2. Identify schema gaps and required new tables
3. Create/verify tables:
   - `validators` - Already exists, verify compatibility
   - `wallets` - Create for wallet tracking (pubkey, partner_id, wallet_type)
   - `partners` - Already exists, verify compatibility
   - `validator_epoch_summary` - Create for epoch-level aggregations
   - `stake_accounts` - Create for per-epoch stake positions
   - `epoch_rewards` - Create for simulated rewards data
4. Add indexes:
   - `stake_accounts(epoch)` for time-series queries
   - `stake_accounts(withdrawer_wallet_id)` for partner attribution
   - `stake_accounts(stake_account_pubkey)` for unique lookups
5. Create Alembic migration script

#### Schema Specifications

**`validator_epoch_summary` Table**:
```sql
CREATE TABLE validator_epoch_summary (
    summary_id SERIAL PRIMARY KEY,
    validator_id INTEGER NOT NULL REFERENCES validators(validator_id),
    epoch INTEGER NOT NULL,
    rpc_activated_stake_lamports BIGINT,
    total_delegated_stake_lamports BIGINT NOT NULL,
    total_active_stake_lamports BIGINT NOT NULL,
    total_activating_stake_lamports BIGINT,
    total_deactivating_stake_lamports BIGINT,
    total_stakers INTEGER NOT NULL,
    last_vote BIGINT,
    root_slot BIGINT,
    epoch_vote_account INTEGER,
    is_delinquent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (validator_id, epoch)
);
```

**`stake_accounts` Table**:
```sql
CREATE TABLE stake_accounts (
    stake_account_id SERIAL PRIMARY KEY,
    stake_account_pubkey VARCHAR(44) NOT NULL,
    validator_id INTEGER NOT NULL REFERENCES validators(validator_id),
    epoch INTEGER NOT NULL,
    staker_wallet_id INTEGER NOT NULL REFERENCES wallets(wallet_id),
    withdrawer_wallet_id INTEGER NOT NULL REFERENCES wallets(wallet_id),
    stake_lamports BIGINT NOT NULL,
    activation_epoch INTEGER NOT NULL,
    deactivation_epoch INTEGER,
    rent_exempt_reserve BIGINT NOT NULL DEFAULT 2282880,
    credits_observed BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (stake_account_pubkey, epoch)
);

CREATE INDEX idx_stake_accounts_epoch ON stake_accounts(epoch);
CREATE INDEX idx_stake_accounts_validator ON stake_accounts(validator_id);
CREATE INDEX idx_stake_accounts_withdrawer ON stake_accounts(withdrawer_wallet_id);
```

**`wallets` Table** (if not exists):
```sql
CREATE TABLE wallets (
    wallet_id SERIAL PRIMARY KEY,
    pubkey VARCHAR(44) UNIQUE NOT NULL,
    chain_id VARCHAR(50) NOT NULL,
    wallet_type VARCHAR(20) NOT NULL, -- 'staker', 'withdrawer', 'both'
    partner_id INTEGER REFERENCES partners(partner_id),
    introduced_date DATE,
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**`epoch_rewards` Table**:
```sql
CREATE TABLE epoch_rewards (
    reward_id SERIAL PRIMARY KEY,
    validator_id INTEGER NOT NULL REFERENCES validators(validator_id),
    epoch INTEGER NOT NULL,
    total_epoch_rewards_lamports BIGINT NOT NULL,
    validator_commission_lamports BIGINT NOT NULL,
    staker_rewards_lamports BIGINT NOT NULL,
    active_stake_lamports BIGINT NOT NULL,
    is_simulated BOOLEAN DEFAULT FALSE,
    simulation_params JSONB, -- Store APY, epochs_per_year, etc.
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (validator_id, epoch)
);
```

#### Acceptance Criteria
- [ ] All required tables created via Alembic migration
- [ ] All indexes created for performance
- [ ] Foreign key constraints properly defined
- [ ] Migration tested (upgrade + downgrade)
- [ ] Schema documented in migration file comments
- [ ] No breaking changes to existing tables

#### Files to Create/Modify
- `alembic/versions/<timestamp>_add_sample_data_tables.py` - Migration script
- `src/core/models/sample_data.py` - ORM models for new tables

---

### Phase 3: Rewards Simulation Engine
**GitHub Issue**: #32
**Estimated Effort**: 1.5 hours
**Dependencies**: None (can run parallel with Phases 1-2)

#### Tasks
1. Create `rewards_simulator.py` module with simulation logic
2. Implement `simulate_epoch_rewards()` function:
   - Input: `active_stake_lamports`, `epoch`
   - Calculate: `epoch_rewards = active_stake * (0.05 / 73)`
   - Note: ~73 epochs per year on Solana, 5% APY assumption
   - Output: `epoch_rewards_lamports`
3. Apply validator commission (5%):
   - `validator_commission = epoch_rewards * 0.05`
   - `staker_rewards = epoch_rewards * 0.95`
4. Calculate per-wallet rewards:
   ```python
   wallet_rewards = (wallet_stake / total_active_stake) * staker_rewards
   ```
5. Store simulated rewards in `epoch_rewards` table with:
   - `is_simulated = TRUE`
   - `simulation_params = {"apy": 0.05, "epochs_per_year": 73}`
6. Add validation to ensure rewards sum correctly

#### Simulation Formula

```python
# Per-epoch rewards calculation
ANNUAL_APY = 0.05  # 5% annual percentage yield
EPOCHS_PER_YEAR = 73  # Approximate Solana epochs per year
VALIDATOR_COMMISSION_RATE = 0.05  # 5% validator commission

def simulate_epoch_rewards(active_stake_lamports: int, epoch: int) -> dict:
    """
    Simulate epoch rewards based on 5% APY assumption.

    Args:
        active_stake_lamports: Total active stake for the validator
        epoch: Epoch number for tracking

    Returns:
        dict with total_rewards, validator_commission, staker_rewards
    """
    # Calculate epoch rewards (annual rate / epochs per year)
    epoch_rate = ANNUAL_APY / EPOCHS_PER_YEAR
    total_epoch_rewards = int(active_stake_lamports * epoch_rate)

    # Split between validator commission and staker rewards
    validator_commission = int(total_epoch_rewards * VALIDATOR_COMMISSION_RATE)
    staker_rewards = total_epoch_rewards - validator_commission

    return {
        "total_epoch_rewards_lamports": total_epoch_rewards,
        "validator_commission_lamports": validator_commission,
        "staker_rewards_lamports": staker_rewards,
        "active_stake_lamports": active_stake_lamports,
        "is_simulated": True,
        "simulation_params": {
            "apy": ANNUAL_APY,
            "epochs_per_year": EPOCHS_PER_YEAR,
            "validator_commission_rate": VALIDATOR_COMMISSION_RATE
        }
    }
```

#### Per-Wallet Reward Calculation

```python
def calculate_wallet_rewards(
    wallet_stake_lamports: int,
    total_active_stake_lamports: int,
    staker_rewards_lamports: int
) -> int:
    """
    Calculate proportional rewards for a wallet based on its stake.

    Args:
        wallet_stake_lamports: Individual wallet's stake amount
        total_active_stake_lamports: Total active stake across all wallets
        staker_rewards_lamports: Total staker rewards to distribute

    Returns:
        Wallet's proportional share of staker rewards in lamports
    """
    if total_active_stake_lamports == 0:
        return 0

    stake_proportion = wallet_stake_lamports / total_active_stake_lamports
    wallet_rewards = int(staker_rewards_lamports * stake_proportion)

    return wallet_rewards
```

#### Acceptance Criteria
- [ ] `rewards_simulator.py` module created
- [ ] `simulate_epoch_rewards()` function implemented with correct formula
- [ ] Validator commission calculation matches 5% rate
- [ ] Per-wallet reward calculation distributes proportionally
- [ ] Rewards sum validation ensures no lamports lost in rounding
- [ ] Unit tests cover all calculation functions
- [ ] Documentation includes formula derivation and assumptions

#### Files to Create
- `src/core/services/rewards_simulator.py` - Simulation engine
- `tests/unit/test_rewards_simulator.py` - Unit tests

---

### Phase 4: Data Import Pipeline
**GitHub Issue**: #33
**Estimated Effort**: 2 hours
**Dependencies**: Phases 1, 2, 3

#### Tasks
1. Create `seed_globalstake_sample.py` script in `scripts/`
2. Parse Excel file using pandas:
   - Read Sheet 1 (Validator Summary)
   - Read Sheet 2 (Stake Accounts)
   - Validate data integrity (61 epochs, 178 wallets per epoch)
3. Import validator identity:
   - Create validator record with vote_pubkey, node_pubkey, commission
   - Store in `validators` table
4. Import wallet identities:
   - Extract all unique staker and withdrawer wallets from Sheet 2
   - Create wallet records in `wallets` table
   - Link wallets to partners using `wallet-distribution.json` from Phase 1
5. Import epoch summaries:
   - Transform Sheet 1 rows → `validator_epoch_summary` records
   - Convert SOL to lamports (multiply by 1e9)
6. Import stake accounts:
   - Transform Sheet 2 rows → `stake_accounts` records
   - Link to wallet_id via staker_wallet and withdrawer_wallet lookups
   - Handle NULL deactivation_epoch correctly
7. Generate simulated rewards for all 61 epochs using Phase 3 engine
8. Implement transaction rollback on validation failures
9. Add progress reporting (e.g., "Importing epoch 820/860...")

#### Import Workflow

```python
async def seed_globalstake_sample():
    """
    Seed database with GlobalStake sample data.

    Workflow:
    1. Load and validate Excel file
    2. Create validator record
    3. Load wallet distribution assignments
    4. Import all unique wallets (staker + withdrawer)
    5. Link wallets to partners
    6. Import validator epoch summaries (61 epochs)
    7. Import stake accounts (10,858 records)
    8. Generate simulated rewards (61 epochs)
    9. Validate data integrity
    """
    # Pseudo-code outline
    df_summary = pd.read_excel("temp-data/globalstake-sample.xlsx", sheet_name="Validator Summary")
    df_stakes = pd.read_excel("temp-data/globalstake-sample.xlsx", sheet_name="Stake Accounts")

    # Validate
    assert len(df_summary) == 61, "Expected 61 epochs"
    assert len(df_stakes) == 10858, "Expected 10,858 stake account records"

    async with async_session_factory() as session:
        # 1. Create validator
        validator = await create_validator(session, vote_pubkey="...", ...)

        # 2. Load partner assignments
        assignments = load_wallet_distribution("temp-data/wallet-distribution.json")

        # 3. Import wallets
        wallet_map = await import_wallets(session, df_stakes, assignments)

        # 4. Import epoch summaries
        await import_epoch_summaries(session, df_summary, validator.validator_id)

        # 5. Import stake accounts
        await import_stake_accounts(session, df_stakes, validator.validator_id, wallet_map)

        # 6. Generate simulated rewards
        await generate_simulated_rewards(session, validator.validator_id, epochs=range(800, 861))

        # 7. Validate
        await validate_import(session, validator.validator_id)

        await session.commit()
```

#### Acceptance Criteria
- [ ] Excel file parsed successfully with pandas
- [ ] Validator record created with correct vote_pubkey and commission
- [ ] All 178 unique wallets imported (both staker and withdrawer roles)
- [ ] Partner assignments applied from `wallet-distribution.json`
- [ ] All 61 epoch summaries imported (epochs 800-860)
- [ ] All 10,858 stake account records imported
- [ ] Simulated rewards generated for all 61 epochs
- [ ] Data validation passes:
  - Total stake matches between summary and detail
  - Wallet counts per epoch = 178
  - No orphaned records
  - All foreign keys valid
- [ ] Transaction rollback works on validation failure
- [ ] Progress reporting shows import status

#### Files to Create
- `scripts/seed_globalstake_sample.py` - Main import script
- `scripts/load_wallet_distribution.py` - Helper to load JSON assignments
- `scripts/validate_import.py` - Data integrity validation

---

### Phase 5: Commission Calculation & Validation
**GitHub Issue**: #34
**Estimated Effort**: 2 hours
**Dependencies**: Phase 4

#### Tasks
1. Create partner records for Partner 1 and Partner 2
2. For each epoch (800-860):
   - Retrieve simulated epoch rewards
   - Calculate active stake per partner (withdrawer-based):
     ```sql
     SELECT p.partner_id, SUM(sa.stake_lamports) AS partner_stake
     FROM stake_accounts sa
     JOIN wallets w ON sa.withdrawer_wallet_id = w.wallet_id
     WHERE w.partner_id = p.partner_id
       AND sa.epoch = ?
       AND (sa.deactivation_epoch IS NULL OR sa.deactivation_epoch > sa.epoch)
     GROUP BY p.partner_id
     ```
   - Calculate partner commission:
     ```python
     partner_commission = (partner_stake / total_active_stake) * staker_rewards * partner_rate
     ```
   - Store in `partner_commissions` table
3. Generate validation report showing:
   - Total validator revenue across 61 epochs
   - Partner 1 total commission (sum of all epochs)
   - Partner 2 total commission
   - Unassigned wallet rewards (should appear as unattributed)
   - Commission per epoch for trending analysis
4. Verify determinism:
   - Run calculation twice
   - Compare results byte-for-byte
   - Assert identical outputs

#### Commission Calculation Logic

```python
async def calculate_partner_commissions(
    session: AsyncSession,
    validator_id: int,
    epochs: list[int],
    partner_commission_rate: float = 0.50  # Default: 50% of validator commission
):
    """
    Calculate partner commissions for given epochs.

    Commission Model:
    - Based on partner's share of total active stake
    - Applied to VALIDATOR COMMISSION (5% of epoch rewards), NOT staker rewards
    - Attributed via withdrawer wallet

    Args:
        session: Database session
        validator_id: Validator to calculate commissions for
        epochs: List of epochs to process
        partner_commission_rate: Partner's commission rate (e.g., 0.50 for 50%)
    """
    for epoch in epochs:
        # Get epoch reward data
        rewards = await get_epoch_rewards(session, validator_id, epoch)
        validator_commission = rewards.validator_commission_lamports  # 5% of epoch rewards
        total_active_stake = rewards.active_stake_lamports

        # Calculate each partner's commission
        for partner_id in [1, 2]:
            # Sum partner's active stake (withdrawer-based attribution)
            partner_stake = await get_partner_active_stake(
                session, partner_id, epoch
            )

            # Calculate proportional share of validator commission
            stake_proportion = partner_stake / total_active_stake
            partner_share_of_validator_commission = validator_commission * stake_proportion
            commission = int(partner_share_of_validator_commission * partner_commission_rate)

            # Store commission record
            await create_partner_commission(
                session,
                partner_id=partner_id,
                validator_id=validator_id,
                epoch=epoch,
                partner_stake_lamports=partner_stake,
                partner_share_of_validator_commission_lamports=partner_share_of_validator_commission,
                commission_lamports=commission
            )
```

#### Validation Report Structure

```json
{
  "validation_timestamp": "2025-11-07T12:00:00Z",
  "epochs_analyzed": 61,
  "epoch_range": [800, 860],
  "validator": {
    "vote_pubkey": "FdGcvmbpebUwYA3vSywnagsaC3Tq3pAVmcR6VoxVcdV9",
    "total_revenue_lamports": 1234567890,
    "total_revenue_sol": 1.23456789
  },
  "partners": [
    {
      "partner_id": 1,
      "partner_name": "Partner 1",
      "wallet_count": 88,
      "total_stake_lamports": 117268410000000,
      "total_stake_sol": 117268.41,
      "stake_percentage": 50.0,
      "total_commission_lamports": 567890123,
      "total_commission_sol": 0.567890123,
      "avg_commission_per_epoch_sol": 0.00931
    },
    {
      "partner_id": 2,
      "partner_name": "Partner 2",
      "wallet_count": 88,
      "total_stake_lamports": 105541570000000,
      "total_stake_sol": 105541.57,
      "stake_percentage": 45.0,
      "total_commission_lamports": 510201111,
      "total_commission_sol": 0.510201111,
      "avg_commission_per_epoch_sol": 0.00837
    }
  ],
  "unassigned": {
    "wallet_count": 2,
    "total_stake_lamports": 11726840000000,
    "total_stake_sol": 11726.84,
    "stake_percentage": 5.0,
    "total_rewards_lamports": 56544444,
    "total_rewards_sol": 0.056544444
  },
  "determinism_check": {
    "run_1_checksum": "abc123...",
    "run_2_checksum": "abc123...",
    "identical": true
  }
}
```

#### Acceptance Criteria
- [ ] Partner 1 and Partner 2 records created
- [ ] Commissions calculated for all 61 epochs
- [ ] Withdrawer wallet used for partner attribution
- [ ] Stake-weighted commission distribution correct
- [ ] Validation report generated with all metrics
- [ ] Unassigned wallet revenue tracked separately
- [ ] Determinism verified (identical results on re-run)
- [ ] Commission totals match expected stake proportions

#### Files to Create
- `scripts/calculate_commissions.py` - Commission calculation script
- `scripts/generate_validation_report.py` - Report generation
- `temp-data/commission-validation-report.json` - Output report

---

### Phase 6: Test Cases & Edge Case Validation
**GitHub Issue**: #35
**Estimated Effort**: 1.5 hours
**Dependencies**: Phase 5

#### Tasks
1. Create test suite for edge cases
2. Test scenarios:
   - **Activating Stake**: Wallet with `activation_epoch = current_epoch`
     - Assert: Should NOT earn rewards yet (warmup period)
     - Verify: Excluded from active stake calculation
   - **Deactivating Stake**: Wallet with `deactivation_epoch = current_epoch`
     - Assert: Should still earn rewards for this epoch
     - Verify: Included in active stake calculation
   - **Unassigned Wallets**: 2 test wallets not assigned to any partner
     - Assert: Commission calculation succeeds
     - Verify: Rewards tracked separately as "unassigned"
   - **Partner Stake Changes**: Wallet switches from active to deactivating
     - Assert: Commission adjusts automatically
     - Verify: Partner stake decreases in subsequent epochs
   - **Full Epoch Range**: Verify consistency across all 61 epochs
     - Assert: No calculation errors or missing epochs
     - Verify: Stake totals balance across all epochs
3. Implement assertions with clear failure messages
4. Generate test report with pass/fail status

#### Test Scenarios

```python
# Test 1: Activating Stake (Warmup Period)
async def test_activating_stake_no_rewards():
    """Stake in warmup period should not earn rewards."""
    # Find stake account where activation_epoch == current_epoch
    stake = await find_activating_stake(session, epoch=820)

    # Verify it's excluded from active stake
    active_stake = await calculate_active_stake(session, epoch=820)
    assert stake.stake_account_pubkey not in active_stake.accounts

    # Verify partner commission doesn't include this stake
    partner_stake = await get_partner_active_stake(
        session, partner_id=stake.partner_id, epoch=820
    )
    assert stake.stake_lamports not in partner_stake

# Test 2: Deactivating Stake (Still Earning)
async def test_deactivating_stake_earns_rewards():
    """Stake in deactivation epoch still earns rewards."""
    # Find stake account where deactivation_epoch == current_epoch
    stake = await find_deactivating_stake(session, epoch=850)

    # Verify it's included in active stake
    active_stake = await calculate_active_stake(session, epoch=850)
    assert stake.stake_account_pubkey in active_stake.accounts

    # Verify partner commission includes this stake
    partner_stake = await get_partner_active_stake(
        session, partner_id=stake.partner_id, epoch=850
    )
    assert stake.stake_lamports in partner_stake

# Test 3: Unassigned Wallets
async def test_unassigned_wallet_commission():
    """Unassigned wallets should be tracked separately."""
    # Get unassigned wallets from distribution
    unassigned = load_unassigned_wallets()
    assert len(unassigned) == 2

    # Verify they have no partner_id
    for wallet_pubkey in unassigned:
        wallet = await get_wallet(session, wallet_pubkey)
        assert wallet.partner_id is None

    # Verify commission calculation succeeds
    commissions = await calculate_partner_commissions(session, epoch=830)
    assert commissions  # Should not fail

    # Verify unassigned rewards tracked
    validation_report = await generate_validation_report(session)
    assert validation_report["unassigned"]["wallet_count"] == 2
    assert validation_report["unassigned"]["total_rewards_lamports"] > 0

# Test 4: Stake State Transitions
async def test_stake_state_transitions():
    """Commission adjusts when stake transitions between states."""
    # Find wallet that transitions from active to deactivating
    wallet = await find_transitioning_wallet(session)

    # Get partner commissions before and after transition
    epoch_before = wallet.deactivation_epoch - 1
    epoch_after = wallet.deactivation_epoch + 1

    commission_before = await get_partner_commission(
        session, partner_id=wallet.partner_id, epoch=epoch_before
    )
    commission_after = await get_partner_commission(
        session, partner_id=wallet.partner_id, epoch=epoch_after
    )

    # Verify commission decreased after deactivation
    assert commission_after.partner_stake_lamports < commission_before.partner_stake_lamports

# Test 5: Epoch Range Consistency
async def test_epoch_range_consistency():
    """Verify consistency across all 61 epochs."""
    epochs = range(800, 861)

    for epoch in epochs:
        # Verify commission calculation exists
        commissions = await get_partner_commissions(session, epoch=epoch)
        assert len(commissions) >= 0  # Should not fail

        # Verify stake totals balance
        summary = await get_epoch_summary(session, epoch=epoch)
        stake_accounts_total = await sum_stake_accounts(session, epoch=epoch)
        assert abs(summary.total_active_stake_lamports - stake_accounts_total) < 1000  # Allow small rounding
```

#### Test Report Structure

```json
{
  "test_run_timestamp": "2025-11-07T14:00:00Z",
  "total_tests": 5,
  "passed": 5,
  "failed": 0,
  "test_results": [
    {
      "test_name": "test_activating_stake_no_rewards",
      "status": "PASSED",
      "duration_ms": 45,
      "message": "Activating stake correctly excluded from active stake calculation"
    },
    {
      "test_name": "test_deactivating_stake_earns_rewards",
      "status": "PASSED",
      "duration_ms": 38,
      "message": "Deactivating stake correctly included in epoch rewards"
    },
    {
      "test_name": "test_unassigned_wallet_commission",
      "status": "PASSED",
      "duration_ms": 52,
      "message": "Unassigned wallets tracked separately with 2 wallets and 11726.84 SOL"
    },
    {
      "test_name": "test_stake_state_transitions",
      "status": "PASSED",
      "duration_ms": 67,
      "message": "Partner commission correctly adjusted for stake state transitions"
    },
    {
      "test_name": "test_epoch_range_consistency",
      "status": "PASSED",
      "duration_ms": 231,
      "message": "All 61 epochs processed consistently with balanced stake totals"
    }
  ]
}
```

#### Acceptance Criteria
- [ ] All 5 test scenarios implemented
- [ ] Activating stake test passes (excluded from rewards)
- [ ] Deactivating stake test passes (included in rewards)
- [ ] Unassigned wallets test passes (separate tracking)
- [ ] Stake transition test passes (commission adjustment)
- [ ] Epoch range consistency test passes (all 61 epochs)
- [ ] Test report generated with pass/fail status
- [ ] All assertions have clear failure messages

#### Files to Create
- `tests/integration/test_sample_data_edge_cases.py` - Test suite
- `scripts/run_edge_case_tests.py` - Test runner
- `temp-data/edge-case-test-report.json` - Test report

---

## Success Criteria

### Data Import Success
- [ ] All 61 epochs imported (epochs 800-860)
- [ ] All 10,858 stake account records imported
- [ ] All 178 unique wallets identified and imported
- [ ] Partner 1 has ~50% of total stake
- [ ] Partner 2 has ~45% of total stake
- [ ] 2 unassigned wallets represent ~5% of stake

### Rewards Simulation Success
- [ ] Simulated rewards generated for all 61 epochs
- [ ] 5% APY assumption applied correctly (~73 epochs/year)
- [ ] Validator commission (5%) calculated correctly
- [ ] Per-wallet rewards distributed proportionally

### Commission Calculation Success
- [ ] Partner commissions calculated for all 61 epochs
- [ ] Withdrawer-based attribution working correctly
- [ ] Stake-weighted distribution accurate
- [ ] Unassigned wallet revenue tracked separately
- [ ] Deterministic results (identical on re-run)

### Validation Success
- [ ] All edge case tests pass
- [ ] Activating stake excluded from rewards (warmup period)
- [ ] Deactivating stake included in rewards (cooldown starts after)
- [ ] Unassigned wallets handled gracefully
- [ ] Stake transitions tracked correctly
- [ ] Consistency verified across all 61 epochs

### Documentation Success
- [ ] Validation report generated with comprehensive metrics
- [ ] Test report shows all tests passing
- [ ] Wallet distribution documented in JSON
- [ ] Commission calculations auditable with full trail

---

## Dependencies & Prerequisites

### External Data
- [ ] `temp-data/globalstake-sample.xlsx` file available
- [ ] Excel file validated (2 sheets, 61 epochs, 178 wallets)

### Database
- [ ] PostgreSQL database accessible
- [ ] Alembic migrations functional
- [ ] Existing Aurora schema compatible

### Software
- [ ] Python 3.11+ with Poetry
- [ ] pandas library for Excel parsing
- [ ] openpyxl library for .xlsx support
- [ ] SQLAlchemy 2.0+ async support

### Configuration
- [ ] Database connection configured in `.env`
- [ ] Partner records created (Partner 1, Partner 2)

---

## Implementation Order

```
Phase 1: Data Analysis & Wallet Distribution (1h)
    ↓
Phase 2: Database Schema Preparation (1h)  ← parallel → Phase 3: Rewards Simulation (1.5h)
    ↓
Phase 4: Data Import Pipeline (2h) [depends on Phases 1, 2, 3]
    ↓
Phase 5: Commission Calculation & Validation (2h) [depends on Phase 4]
    ↓
Phase 6: Test Cases & Edge Case Validation (1.5h) [depends on Phase 5]
```

**Total Estimated Effort**: ~9 hours

---

## Deliverables

### Code Artifacts
1. `scripts/analyze_wallet_distribution.py` - Wallet analysis script
2. `scripts/seed_globalstake_sample.py` - Main data import script
3. `src/core/services/rewards_simulator.py` - Rewards simulation engine
4. `src/core/models/sample_data.py` - ORM models for new tables
5. `alembic/versions/<timestamp>_add_sample_data_tables.py` - Migration script
6. `scripts/calculate_commissions.py` - Commission calculation
7. `tests/integration/test_sample_data_edge_cases.py` - Test suite

### Data Artifacts
1. `temp-data/wallet-distribution.json` - Partner wallet assignments
2. `temp-data/commission-validation-report.json` - Validation results
3. `temp-data/edge-case-test-report.json` - Test results

### Database Content
1. 1 validator record (GlobalStake validator)
2. 2 partner records (Partner 1, Partner 2)
3. 178 wallet records (all staker and withdrawer wallets)
4. 61 epoch summary records (epochs 800-860)
5. 10,858 stake account records
6. 61 simulated reward records
7. 122 partner commission records (2 partners × 61 epochs)

---

## Next Steps After Completion

1. **Review Commission Engine**: Validate commission calculation logic against real-world expectations
2. **UI Integration**: Display partner commissions in frontend dashboard
3. **Real Data Integration**: Adapt ingestion pipeline to fetch live data from providers
4. **Multi-Validator Support**: Extend to handle multiple validators simultaneously
5. **Ethereum Support**: Replicate data seeding process for Ethereum validators (M1 milestone)

---

## References

- Original data analysis: See comprehensive technical breakdown from brainstorming session
- Excel file location: `temp-data/globalstake-sample.xlsx`
- Solana staking mechanics: [Solana Documentation](https://docs.solana.com/staking)
- Commission attribution: Withdrawer-based approach (economic beneficiary)
- Rewards simulation: 5% APY assumption, ~73 epochs/year

---

**Document Version**: 1.0
**Last Updated**: 2025-11-07
**Status**: Planning
**Milestone Target**: Sample Data Seeding & Commission Testing
**Branch**: `feature/milestone-sample-data-seeding`
