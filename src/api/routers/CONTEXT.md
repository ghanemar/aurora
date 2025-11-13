# API Routers Documentation

*This file documents the REST API endpoint routers and their patterns.*

## Router Organization

Each router file handles a specific resource domain:

- `validators.py` - Validator registry CRUD and statistics
- `partners.py` - Partner CRUD operations
- `agreements.py` - Agreement and rules management
- `sample_commissions.py` - Sample data commission calculation (current)
- `partner_wallets.py` - Partner wallet CRUD, bulk upload, export

## Commission Routers

### sample_commissions.py

**Purpose**: Commission calculation using sample data seeding (epochs 800-860)

**Endpoints**:
- `GET /api/v1/sample-commissions/epochs` - List available epochs
- `GET /api/v1/sample-commissions/partners/{partner_id}` - Calculate partner commission
- `GET /api/v1/sample-commissions/all` - Calculate all partners' commissions

**Query Parameters** (for partner-specific endpoint):
- `start_epoch` (required) - Start of epoch range (inclusive)
- `end_epoch` (required) - End of epoch range (inclusive)
- `commission_rate` (optional, default=0.50) - Partner commission rate as decimal

**Response Structure**:
```typescript
{
  partner_id: string,
  partner_name: string,
  wallet_count: number,
  validator_count: number,
  start_epoch: number,
  end_epoch: number,
  epoch_count: number,
  total_partner_stake_lamports: number,
  total_partner_rewards_lamports: number,
  commission_rate: string,
  total_commission_lamports: number,
  validator_summaries: [{
    validator_vote_pubkey: string,
    validator_name: string,
    total_stake_lamports: number,
    partner_stake_lamports: number,
    stake_percentage: string,
    partner_commission_lamports: number
  }],
  epoch_details: [{
    epoch: number,
    validator_vote_pubkey: string,
    validator_name: string,
    total_active_stake_lamports: number,
    partner_stake_lamports: number,
    stake_percentage: string,
    validator_commission_lamports: number,
    total_staker_rewards_lamports: number,
    partner_rewards_lamports: number,
    commission_rate: string,
    partner_commission_lamports: number
  }]
}
```

**Business Logic**:
- Commission calculated from validator 5% commission, NOT 95% staker rewards
- Default partner rate: 50% of validator commission
- Stake-weighted proportional distribution
- Withdrawer-based wallet attribution

**Frontend Integration**:
- Powers SampleCommissionsPage.tsx
- Displays validator breakdown section with per-validator cards
- Populates 8-column per-epoch details table
- Shows validator names from validator_name field
