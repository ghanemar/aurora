# Frontend Pages Documentation

*This file documents the React page components and their data integration patterns.*

## Page Organization

- `DashboardPage.tsx` - Dashboard with statistics and navigation
- `ValidatorsPage.tsx` - Validator registry management
- `PartnersPage.tsx` - Partner CRUD with wallet management
- `AgreementsPage.tsx` - Agreement listing
- `SampleCommissionsPage.tsx` - Commission calculation and display
- `PartnerWalletsPage.tsx` - Partner wallet management

## SampleCommissionsPage.tsx

**Purpose**: Partner commission calculation and analysis interface

**UI Structure**:
1. **Configure Calculation Panel**:
   - Partner selection (autocomplete dropdown)
   - Commission rate input (default 0.50 = 50%)
   - Start epoch selector
   - End epoch selector
   - Calculate button

2. **Commission Summary Section**:
   - Total Commission (SOL)
   - Wallets Brought (count)
   - Validators (count)
   - Epoch Range with chip

3. **Validator Breakdown Section**:
   - Validator name
   - Total Stake (Average, SOL)
   - Partner Stake (Average, SOL)
   - Partner Share (percentage)
   - Commission from Validator (SOL)

4. **Per-Epoch Breakdown Table** (8 columns):
   - Epoch
   - Validator (name)
   - Total Stake (SOL)
   - Partner Stake (SOL)
   - Partner %
   - Validator Commission (SOL)
   - Staker Rewards (SOL)
   - Partner Commission (SOL)

**Data Flow**:
```
User configures filters → Click "Calculate"
    ↓
sampleCommissionsService.calculatePartnerCommission()
    ↓
GET /api/v1/sample-commissions/partners/{id}
    ↓
Receive SampleCommissionCalculation response
    ↓
Display validator_summaries in breakdown cards
    ↓
Map epoch_details to table rows
```

**Dependencies**:
- `services/sampleCommissions.ts` - API client
- `types/index.ts` - TypeScript interfaces
- Material-UI components (Autocomplete, TextField, Button, Grid, Paper, Chip)
- React Query for data fetching
