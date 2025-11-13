# Service Layer Documentation

*This file documents the business logic services within the Aurora application.*

## Service Architecture

The service layer orchestrates business logic between repositories, external adapters, and domain operations:

- **Layer Position**: Between API routes and database repositories
- **Responsibility**: Business logic, calculations, orchestration
- **Pattern**: Stateless services with dependency injection
- **Database Access**: Via repositories only, never direct SQLAlchemy queries

## Commission Calculation Services

### CommissionCalculator (`commission_calculator.py`)

**Purpose**: Calculate partner commissions from validator epoch data

**Key Method**: `calculate_partner_commission(partner_id, epoch_start, epoch_end, commission_rate)`

**Commission Model**:
- **Source**: Validator commission (5% of epoch rewards), NOT staker rewards (95%)
- **Attribution**: Withdrawer-based wallet ownership (economic beneficiary)
- **Distribution**: Stake-weighted proportional allocation among partners
- **Default Rate**: 50% (0.50) of validator commission allocated to partners

**Formula**:
```python
# Per epoch calculation
epoch_rewards = active_stake * (0.05 APY / 73 epochs_per_year)
validator_commission = epoch_rewards * 0.05  # 5% of epoch rewards
partner_stake_ratio = partner_stake / total_validator_stake
partner_commission = validator_commission * partner_stake_ratio * commission_rate  # Default 0.50
```

**Database Dependencies**:
- `sample_validator_epoch_summary` - Validator data with validator_name, commission_rate_bps
- `sample_stake_accounts` - Stake positions with withdrawer_wallet attribution
- `partner_wallets` - Partner wallet assignments

**Return Structure**:
- `ValidatorSummary` - Validator metadata (name, vote_pubkey, total_stake, partner_stake, percentage, commission)
- `List[EpochCommissionDetail]` - Per-epoch breakdown with 8 detailed metrics

### RewardsSimulator (`rewards_simulator.py`)

**Purpose**: Simulate epoch rewards for testing and validation

**Assumptions**:
- **APY**: 5% annual percentage yield
- **Epochs per Year**: ~73 (Solana average)
- **Validator Commission**: 5% of epoch rewards
- **Staker Rewards**: 95% of epoch rewards

**Usage**: Sample data seeding and commission validation testing

## Integration Patterns

### API to Service Flow
```
API Router (sample_commissions.py)
    ↓
CommissionCalculator.calculate_partner_commission()
    ↓
[For each epoch]:
    Fetch sample_validator_epoch_summary
    Fetch partner stake from sample_stake_accounts
    Calculate validator commission (5%)
    Calculate partner share (stake-weighted)
    Apply commission rate (default 50%)
    Build EpochCommissionDetail
    ↓
Aggregate results and build ValidatorSummary
    ↓
Return CommissionCalculationResult
```

## Key Design Decisions

### Why Validator Commission (5%) Instead of Staker Rewards (95%)?
**Rationale**: Partners are compensated from validator revenue (commission), not from staker returns. Validators earn commission on delegated stake; partners receive a share of that commission based on stake they introduce.

### Why Withdrawer-Based Attribution?
**Rationale**: In Solana staking, the withdrawer authority controls fund withdrawals (principal + rewards) and is the economic beneficiary. This makes it the correct identifier for partner revenue attribution.

**Stake Account Authorities**:
- **Staker Authority**: Can delegate/change validators (operational control)
- **Withdrawer Authority**: Can withdraw funds (economic ownership) ✅ Used for attribution

### Why Default 50% Partner Rate?
**Rationale**: Represents a 50/50 revenue share between validator and partner for stake introduced by the partner. This is a business decision that can be adjusted per partner agreement.

**Calculation Example**:
- Validator earns 5% commission on 100 SOL stake = 5 SOL
- Partner introduced 50% of stake = 50 SOL
- Partner's portion of commission = 5 SOL * (50/100) = 2.5 SOL
- Partner commission (50% rate) = 2.5 SOL * 0.50 = 1.25 SOL
