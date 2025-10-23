# Database Schema - Multi-Chain Validator P&L & Partner Commissions

## Schema Overview

This document defines the complete PostgreSQL database schema for the Multi-Chain Validator P&L & Partner Commissions platform. The schema is organized into five logical groups:

1. **Configuration & Registry** - Chain and provider configuration
2. **Staging Layer** - Raw ingestion data with full traceability
3. **Canonical Layer** - Normalized, provider-independent data
4. **Computation Layer** - Validator P&L and commission calculations
5. **User & Access Layer** - Authentication, authorization, and audit logging

## Schema Conventions

### Naming Conventions
- **Tables**: snake_case, plural for entities (e.g., `canonical_validator_fees`)
- **Columns**: snake_case (e.g., `chain_id`, `validator_key`)
- **Primary Keys**: `{entity}_id` or composite keys
- **Foreign Keys**: `{referenced_table}_id`
- **Timestamps**: `created_at`, `updated_at`, `{action}_at`

### Data Types
- **IDs**: `UUID` (default gen_random_uuid())
- **Amounts**: `NUMERIC(38, 18)` for native units (lamports, wei)
- **Percentages**: `INTEGER` (basis points, 1% = 100 bps)
- **Timestamps**: `TIMESTAMPTZ` (always with timezone)
- **JSON**: `JSONB` (indexed, queryable)
- **Enums**: Custom ENUM types for fixed value sets

### Indexing Strategy
- **Primary keys**: Automatic B-tree indexes
- **Foreign keys**: Explicit indexes for join performance
- **Composite indexes**: (chain_id, period_id, validator_key) for canonical tables
- **JSONB indexes**: GIN indexes for staging payload queries
- **Temporal queries**: Indexes on timestamp columns

---

## 1. Configuration & Registry

### chains

Defines supported blockchain networks and their characteristics.

```sql
CREATE TABLE chains (
    chain_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    period_type VARCHAR(20) NOT NULL CHECK (period_type IN ('EPOCH', 'BLOCK_WINDOW', 'SLOT_RANGE')),
    native_unit VARCHAR(20) NOT NULL,
    native_decimals INTEGER NOT NULL,
    finality_lag INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_chains_active ON chains (is_active);
```

**Key Columns**:
- `chain_id`: Unique identifier (e.g., "solana-mainnet", "ethereum-mainnet")
- `period_type`: How periods are defined (EPOCH for Solana, BLOCK_WINDOW for Ethereum)
- `finality_lag`: Periods to wait before considering data final
- `is_active`: Soft-delete flag for deprecated chains

---

### providers

External data providers and their configurations.

```sql
CREATE TABLE providers (
    provider_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_name VARCHAR(50) UNIQUE NOT NULL,
    provider_type VARCHAR(20) NOT NULL CHECK (provider_type IN ('FEES', 'MEV', 'REWARDS', 'META', 'RPC')),
    base_url TEXT,
    api_version VARCHAR(20),
    is_enabled BOOLEAN NOT NULL DEFAULT true,
    rate_limit_per_minute INTEGER,
    timeout_seconds INTEGER DEFAULT 30,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_providers_name ON providers (provider_name);
CREATE INDEX idx_providers_type ON providers (provider_type);
CREATE INDEX idx_providers_enabled ON providers (is_enabled);
```

**Key Columns**:
- `provider_name`: Human-readable name (e.g., "solanabeach", "jito")
- `provider_type`: Data category provided (FEES, MEV, REWARDS, META, RPC)
- `is_enabled`: Soft-enable/disable without deleting config

---

### chain_provider_mappings

Maps chains to their configured providers.

```sql
CREATE TABLE chain_provider_mappings (
    mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chain_id VARCHAR(50) NOT NULL REFERENCES chains (chain_id) ON DELETE CASCADE,
    provider_id UUID NOT NULL REFERENCES providers (provider_id) ON DELETE CASCADE,
    provider_role VARCHAR(20) NOT NULL CHECK (provider_role IN ('FEES', 'MEV', 'REWARDS', 'META', 'RPC')),
    priority INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (chain_id, provider_role, priority)
);

CREATE INDEX idx_chain_provider_chain ON chain_provider_mappings (chain_id);
CREATE INDEX idx_chain_provider_provider ON chain_provider_mappings (provider_id);
```

**Key Columns**:
- `provider_role`: Which data type this provider supplies
- `priority`: Source priority (1 = highest) when multiple providers exist

---

### canonical_periods

Period definitions per chain.

```sql
CREATE TABLE canonical_periods (
    period_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chain_id VARCHAR(50) NOT NULL REFERENCES chains (chain_id) ON DELETE CASCADE,
    period_identifier VARCHAR(50) NOT NULL,
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    is_finalized BOOLEAN NOT NULL DEFAULT false,
    finalized_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (chain_id, period_identifier)
);

CREATE INDEX idx_canonical_periods_chain ON canonical_periods (chain_id);
CREATE INDEX idx_canonical_periods_finalized ON canonical_periods (is_finalized);
CREATE INDEX idx_canonical_periods_range ON canonical_periods (chain_id, period_start, period_end);
```

**Key Columns**:
- `period_identifier`: Chain-specific period ID (e.g., "850" for Solana epoch)
- `is_finalized`: Whether period data is considered final (respects finality_lag)

---

### canonical_validator_identities

Chain-specific validator identity mappings.

```sql
CREATE TABLE canonical_validator_identities (
    identity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chain_id VARCHAR(50) NOT NULL REFERENCES chains (chain_id) ON DELETE CASCADE,
    validator_key VARCHAR(100) NOT NULL,
    vote_pubkey VARCHAR(100),
    node_pubkey VARCHAR(100),
    identity_pubkey VARCHAR(100),
    fee_recipient VARCHAR(100),
    display_name VARCHAR(200),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (chain_id, validator_key)
);

CREATE INDEX idx_validator_identities_chain ON canonical_validator_identities (chain_id);
CREATE INDEX idx_validator_identities_key ON canonical_validator_identities (validator_key);
```

**Key Columns**:
- `validator_key`: Canonical validator identifier (chain-specific primary key)
- `vote_pubkey`, `node_pubkey`, `identity_pubkey`: Solana-specific identities
- `fee_recipient`: Ethereum-specific fee recipient address

---

## 2. Staging Layer

### ingestion_runs

Tracks ingestion job executions.

```sql
CREATE TYPE ingestion_status AS ENUM ('PENDING', 'RUNNING', 'SUCCESS', 'FAILED', 'PARTIAL');

CREATE TABLE ingestion_runs (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chain_id VARCHAR(50) NOT NULL REFERENCES chains (chain_id) ON DELETE CASCADE,
    period_id UUID REFERENCES canonical_periods (period_id) ON DELETE SET NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status ingestion_status NOT NULL DEFAULT 'PENDING',
    error_message TEXT,
    records_fetched INTEGER DEFAULT 0,
    records_staged INTEGER DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ingestion_runs_chain ON ingestion_runs (chain_id);
CREATE INDEX idx_ingestion_runs_period ON ingestion_runs (period_id);
CREATE INDEX idx_ingestion_runs_status ON ingestion_runs (status);
CREATE INDEX idx_ingestion_runs_started ON ingestion_runs (started_at);
```

**Key Columns**:
- `status`: Current ingestion job status
- `records_fetched`: Total records fetched from providers
- `records_staged`: Records successfully written to staging
- `metadata`: Job configuration, provider versions, etc.

---

### staging_payloads

Raw provider responses with full traceability.

```sql
CREATE TYPE data_type AS ENUM ('FEES', 'MEV', 'REWARDS', 'META');

CREATE TABLE staging_payloads (
    payload_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES ingestion_runs (run_id) ON DELETE CASCADE,
    chain_id VARCHAR(50) NOT NULL REFERENCES chains (chain_id) ON DELETE CASCADE,
    period_id UUID NOT NULL REFERENCES canonical_periods (period_id) ON DELETE CASCADE,
    validator_key VARCHAR(100) NOT NULL,
    provider_id UUID NOT NULL REFERENCES providers (provider_id) ON DELETE CASCADE,
    data_type data_type NOT NULL,
    fetch_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    response_hash VARCHAR(64) NOT NULL,
    raw_payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_staging_payloads_run ON staging_payloads (run_id);
CREATE INDEX idx_staging_payloads_chain_period ON staging_payloads (chain_id, period_id);
CREATE INDEX idx_staging_payloads_validator ON staging_payloads (validator_key);
CREATE INDEX idx_staging_payloads_provider ON staging_payloads (provider_id);
CREATE INDEX idx_staging_payloads_data_type ON staging_payloads (data_type);
CREATE INDEX idx_staging_payloads_raw_payload ON staging_payloads USING GIN (raw_payload);
```

**Key Columns**:
- `response_hash`: SHA-256 hash of raw_payload for idempotency and verification
- `raw_payload`: Unmodified JSON response from provider (JSONB for queryability)

---

## 3. Canonical Layer

### canonical_validator_fees

Normalized execution fees per validator/period.

```sql
CREATE TABLE canonical_validator_fees (
    fee_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chain_id VARCHAR(50) NOT NULL REFERENCES chains (chain_id) ON DELETE CASCADE,
    period_id UUID NOT NULL REFERENCES canonical_periods (period_id) ON DELETE CASCADE,
    validator_key VARCHAR(100) NOT NULL,
    total_fees_native NUMERIC(38, 18) NOT NULL,
    fee_count INTEGER NOT NULL DEFAULT 0,
    source_provider_id UUID NOT NULL REFERENCES providers (provider_id) ON DELETE RESTRICT,
    source_payload_id UUID NOT NULL REFERENCES staging_payloads (payload_id) ON DELETE RESTRICT,
    normalized_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (chain_id, period_id, validator_key)
);

CREATE INDEX idx_canonical_fees_chain_period_validator ON canonical_validator_fees (chain_id, period_id, validator_key);
CREATE INDEX idx_canonical_fees_source_provider ON canonical_validator_fees (source_provider_id);
CREATE INDEX idx_canonical_fees_source_payload ON canonical_validator_fees (source_payload_id);
```

**Key Columns**:
- `total_fees_native`: Total fees in native units (lamports for Solana, wei for Ethereum)
- `fee_count`: Number of fee-paying transactions/blocks
- `source_provider_id`, `source_payload_id`: Full traceability to source

---

### canonical_validator_mev

Normalized MEV tips per validator/period.

```sql
CREATE TABLE canonical_validator_mev (
    mev_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chain_id VARCHAR(50) NOT NULL REFERENCES chains (chain_id) ON DELETE CASCADE,
    period_id UUID NOT NULL REFERENCES canonical_periods (period_id) ON DELETE CASCADE,
    validator_key VARCHAR(100) NOT NULL,
    total_mev_native NUMERIC(38, 18) NOT NULL,
    tip_count INTEGER NOT NULL DEFAULT 0,
    source_provider_id UUID NOT NULL REFERENCES providers (provider_id) ON DELETE RESTRICT,
    source_payload_id UUID NOT NULL REFERENCES staging_payloads (payload_id) ON DELETE RESTRICT,
    normalized_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (chain_id, period_id, validator_key)
);

CREATE INDEX idx_canonical_mev_chain_period_validator ON canonical_validator_mev (chain_id, period_id, validator_key);
CREATE INDEX idx_canonical_mev_source_provider ON canonical_validator_mev (source_provider_id);
CREATE INDEX idx_canonical_mev_source_payload ON canonical_validator_mev (source_payload_id);
```

**Key Columns**:
- `total_mev_native`: Total MEV tips in native units
- `tip_count`: Number of MEV tip distributions

---

### canonical_stake_rewards

Normalized staking rewards per validator/period.

```sql
CREATE TABLE canonical_stake_rewards (
    reward_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chain_id VARCHAR(50) NOT NULL REFERENCES chains (chain_id) ON DELETE CASCADE,
    period_id UUID NOT NULL REFERENCES canonical_periods (period_id) ON DELETE CASCADE,
    validator_key VARCHAR(100) NOT NULL,
    staker_address VARCHAR(100),
    rewards_native NUMERIC(38, 18) NOT NULL,
    commission_native NUMERIC(38, 18) NOT NULL DEFAULT 0,
    source_provider_id UUID NOT NULL REFERENCES providers (provider_id) ON DELETE RESTRICT,
    source_payload_id UUID NOT NULL REFERENCES staging_payloads (payload_id) ON DELETE RESTRICT,
    normalized_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_canonical_rewards_chain_period_validator ON canonical_stake_rewards (chain_id, period_id, validator_key);
CREATE INDEX idx_canonical_rewards_staker ON canonical_stake_rewards (staker_address);
CREATE INDEX idx_canonical_rewards_source_provider ON canonical_stake_rewards (source_provider_id);
CREATE INDEX idx_canonical_rewards_source_payload ON canonical_stake_rewards (source_payload_id);
```

**Key Columns**:
- `staker_address`: Specific staker address (null if aggregated validator-level)
- `rewards_native`: Staker rewards before commission
- `commission_native`: Commission earned by validator from this staker

---

### canonical_validator_meta

Normalized validator metadata per period.

```sql
CREATE TABLE canonical_validator_meta (
    meta_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chain_id VARCHAR(50) NOT NULL REFERENCES chains (chain_id) ON DELETE CASCADE,
    period_id UUID NOT NULL REFERENCES canonical_periods (period_id) ON DELETE CASCADE,
    validator_key VARCHAR(100) NOT NULL,
    commission_rate_bps INTEGER NOT NULL,
    is_mev_enabled BOOLEAN NOT NULL DEFAULT false,
    total_stake_native NUMERIC(38, 18) NOT NULL DEFAULT 0,
    active_stake_native NUMERIC(38, 18),
    delegator_count INTEGER,
    uptime_percentage NUMERIC(5, 2),
    source_provider_id UUID NOT NULL REFERENCES providers (provider_id) ON DELETE RESTRICT,
    source_payload_id UUID NOT NULL REFERENCES staging_payloads (payload_id) ON DELETE RESTRICT,
    normalized_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (chain_id, period_id, validator_key)
);

CREATE INDEX idx_canonical_meta_chain_period_validator ON canonical_validator_meta (chain_id, period_id, validator_key);
CREATE INDEX idx_canonical_meta_mev_enabled ON canonical_validator_meta (is_mev_enabled);
CREATE INDEX idx_canonical_meta_source_provider ON canonical_validator_meta (source_provider_id);
CREATE INDEX idx_canonical_meta_source_payload ON canonical_validator_meta (source_payload_id);
```

**Key Columns**:
- `commission_rate_bps`: Validator commission rate (basis points, 5% = 500)
- `is_mev_enabled`: Whether validator runs MEV client (Jito for Solana)
- `total_stake_native`, `active_stake_native`: Stake amounts

---

## 4. Computation Layer

### validator_pnl

Computed validator P&L per period.

```sql
CREATE TABLE validator_pnl (
    pnl_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chain_id VARCHAR(50) NOT NULL REFERENCES chains (chain_id) ON DELETE CASCADE,
    period_id UUID NOT NULL REFERENCES canonical_periods (period_id) ON DELETE CASCADE,
    validator_key VARCHAR(100) NOT NULL,
    exec_fees_native NUMERIC(38, 18) NOT NULL DEFAULT 0,
    mev_tips_native NUMERIC(38, 18) NOT NULL DEFAULT 0,
    vote_rewards_native NUMERIC(38, 18) NOT NULL DEFAULT 0,
    commission_native NUMERIC(38, 18) NOT NULL DEFAULT 0,
    total_revenue_native NUMERIC(38, 18) NOT NULL,
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (chain_id, period_id, validator_key)
);

CREATE INDEX idx_validator_pnl_chain_period ON validator_pnl (chain_id, period_id);
CREATE INDEX idx_validator_pnl_validator ON validator_pnl (validator_key);
CREATE INDEX idx_validator_pnl_computed ON validator_pnl (computed_at);
```

**Key Columns**:
- `exec_fees_native`: Execution fees from canonical_validator_fees
- `mev_tips_native`: MEV tips from canonical_validator_mev
- `vote_rewards_native`: Validator portion of staking rewards
- `commission_native`: Commission earned from delegators
- `total_revenue_native`: Sum of all revenue components

---

### partners

Partner (introducer) entities.

```sql
CREATE TABLE partners (
    partner_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    partner_name VARCHAR(200) NOT NULL,
    legal_entity_name VARCHAR(200),
    contact_email VARCHAR(200) NOT NULL,
    contact_name VARCHAR(200),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_partners_active ON partners (is_active);
CREATE INDEX idx_partners_email ON partners (contact_email);
```

**Key Columns**:
- `partner_name`: Display name for partner organization
- `legal_entity_name`: Legal entity for contracts/invoicing
- `is_active`: Soft-delete flag

---

### agreements

Partner agreement contracts.

```sql
CREATE TYPE agreement_status AS ENUM ('DRAFT', 'ACTIVE', 'SUSPENDED', 'TERMINATED');

CREATE TABLE agreements (
    agreement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    partner_id UUID NOT NULL REFERENCES partners (partner_id) ON DELETE RESTRICT,
    agreement_name VARCHAR(200) NOT NULL,
    current_version INTEGER NOT NULL DEFAULT 1,
    status agreement_status NOT NULL DEFAULT 'DRAFT',
    effective_from TIMESTAMPTZ NOT NULL,
    effective_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agreements_partner ON agreements (partner_id);
CREATE INDEX idx_agreements_status ON agreements (status);
CREATE INDEX idx_agreements_effective ON agreements (effective_from, effective_until);
```

**Key Columns**:
- `current_version`: Tracks active version (agreements are versioned)
- `status`: Agreement lifecycle status
- `effective_from`, `effective_until`: Validity period

---

### agreement_versions

Historical versions of agreements.

```sql
CREATE TABLE agreement_versions (
    version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agreement_id UUID NOT NULL REFERENCES agreements (agreement_id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    effective_from TIMESTAMPTZ NOT NULL,
    effective_until TIMESTAMPTZ,
    terms_snapshot JSONB NOT NULL,
    created_by UUID REFERENCES users (user_id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (agreement_id, version_number)
);

CREATE INDEX idx_agreement_versions_agreement ON agreement_versions (agreement_id);
CREATE INDEX idx_agreement_versions_effective ON agreement_versions (effective_from, effective_until);
```

**Key Columns**:
- `version_number`: Sequential version number
- `terms_snapshot`: Full agreement terms at this version (JSONB)
- `created_by`: User who created this version

---

### agreement_rules

Commission calculation rules per agreement.

```sql
CREATE TYPE revenue_component AS ENUM ('EXEC_FEES', 'MEV_TIPS', 'VOTE_REWARDS', 'COMMISSION');
CREATE TYPE attribution_method AS ENUM ('CLIENT_REVENUE', 'STAKE_WEIGHT', 'FIXED_SHARE');

CREATE TABLE agreement_rules (
    rule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agreement_id UUID NOT NULL REFERENCES agreements (agreement_id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    rule_order INTEGER NOT NULL,
    chain_id VARCHAR(50) REFERENCES chains (chain_id) ON DELETE CASCADE,
    validator_key VARCHAR(100),
    revenue_component revenue_component NOT NULL,
    attribution_method attribution_method NOT NULL,
    commission_rate_bps INTEGER NOT NULL,
    floor_amount_native NUMERIC(38, 18),
    cap_amount_native NUMERIC(38, 18),
    tier_config JSONB,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (agreement_id, version_number) REFERENCES agreement_versions (agreement_id, version_number) ON DELETE CASCADE
);

CREATE INDEX idx_agreement_rules_agreement ON agreement_rules (agreement_id);
CREATE INDEX idx_agreement_rules_chain ON agreement_rules (chain_id);
CREATE INDEX idx_agreement_rules_validator ON agreement_rules (validator_key);
CREATE INDEX idx_agreement_rules_active ON agreement_rules (is_active);
```

**Key Columns**:
- `rule_order`: Execution order for multi-rule agreements
- `chain_id`, `validator_key`: Optional filters (null = applies to all)
- `revenue_component`: Which P&L component this rule applies to
- `attribution_method`: How to calculate commission
- `commission_rate_bps`: Commission percentage (basis points)
- `floor_amount_native`, `cap_amount_native`: Min/max commission per period
- `tier_config`: Optional tier escalations (JSONB)

---

### partner_commission_lines

Computed commission lines per agreement/period.

```sql
CREATE TABLE partner_commission_lines (
    line_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agreement_id UUID NOT NULL REFERENCES agreements (agreement_id) ON DELETE RESTRICT,
    agreement_version INTEGER NOT NULL,
    rule_id UUID NOT NULL REFERENCES agreement_rules (rule_id) ON DELETE RESTRICT,
    partner_id UUID NOT NULL REFERENCES partners (partner_id) ON DELETE RESTRICT,
    chain_id VARCHAR(50) NOT NULL REFERENCES chains (chain_id) ON DELETE CASCADE,
    period_id UUID NOT NULL REFERENCES canonical_periods (period_id) ON DELETE CASCADE,
    validator_key VARCHAR(100),
    revenue_component revenue_component NOT NULL,
    attribution_method attribution_method NOT NULL,
    base_amount_native NUMERIC(38, 18) NOT NULL,
    commission_rate_bps INTEGER NOT NULL,
    pre_override_amount_native NUMERIC(38, 18) NOT NULL,
    override_amount_native NUMERIC(38, 18),
    override_reason TEXT,
    override_user_id UUID REFERENCES users (user_id) ON DELETE SET NULL,
    override_timestamp TIMESTAMPTZ,
    final_amount_native NUMERIC(38, 18) NOT NULL,
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_commission_lines_agreement ON partner_commission_lines (agreement_id);
CREATE INDEX idx_commission_lines_partner ON partner_commission_lines (partner_id);
CREATE INDEX idx_commission_lines_chain_period ON partner_commission_lines (chain_id, period_id);
CREATE INDEX idx_commission_lines_validator ON partner_commission_lines (validator_key);
CREATE INDEX idx_commission_lines_computed ON partner_commission_lines (computed_at);
```

**Key Columns**:
- `base_amount_native`: Revenue amount this commission is based on
- `pre_override_amount_native`: Calculated commission before manual override
- `override_amount_native`, `override_reason`: Manual adjustments with justification
- `final_amount_native`: Final commission amount (pre_override or override if set)

---

### partner_commission_statements

Aggregated monthly commission statements.

```sql
CREATE TYPE statement_status AS ENUM ('DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'RELEASED', 'PAID');

CREATE TABLE partner_commission_statements (
    statement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    partner_id UUID NOT NULL REFERENCES partners (partner_id) ON DELETE RESTRICT,
    chain_id VARCHAR(50) NOT NULL REFERENCES chains (chain_id) ON DELETE CASCADE,
    period_id UUID NOT NULL REFERENCES canonical_periods (period_id) ON DELETE CASCADE,
    total_commission_native NUMERIC(38, 18) NOT NULL,
    line_count INTEGER NOT NULL,
    status statement_status NOT NULL DEFAULT 'DRAFT',
    approved_by UUID REFERENCES users (user_id) ON DELETE SET NULL,
    approved_at TIMESTAMPTZ,
    released_by UUID REFERENCES users (user_id) ON DELETE SET NULL,
    released_at TIMESTAMPTZ,
    paid_at TIMESTAMPTZ,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (partner_id, chain_id, period_id)
);

CREATE INDEX idx_statements_partner ON partner_commission_statements (partner_id);
CREATE INDEX idx_statements_chain_period ON partner_commission_statements (chain_id, period_id);
CREATE INDEX idx_statements_status ON partner_commission_statements (status);
```

**Key Columns**:
- `total_commission_native`: Sum of all commission lines for this partner/period
- `line_count`: Number of commission lines included
- `status`: Statement lifecycle (Draft → Approval → Release → Paid)
- `approved_by`, `released_by`: Workflow tracking with user attribution

---

## 5. User & Access Layer

### users

System users (internal and partner).

```sql
CREATE TYPE user_role AS ENUM ('ADMIN', 'FINANCE', 'OPS', 'PARTNER', 'AUDITOR');

CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(200) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role user_role NOT NULL,
    partner_id UUID REFERENCES partners (partner_id) ON DELETE SET NULL,
    allowed_chain_ids VARCHAR(50)[],
    allowed_validator_keys VARCHAR(100)[],
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_username ON users (username);
CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_users_role ON users (role);
CREATE INDEX idx_users_partner ON users (partner_id);
CREATE INDEX idx_users_active ON users (is_active);
```

**Key Columns**:
- `role`: RBAC role (ADMIN, FINANCE, OPS, PARTNER, AUDITOR)
- `partner_id`: Set for PARTNER role to scope data access
- `allowed_chain_ids`, `allowed_validator_keys`: Optional additional scoping
- `password_hash`: bcrypt hashed password (never plaintext)

---

### audit_log

Immutable audit trail for sensitive operations.

```sql
CREATE TYPE audit_action AS ENUM (
    'CREATE_AGREEMENT', 'UPDATE_AGREEMENT', 'DELETE_AGREEMENT',
    'CREATE_RULE', 'UPDATE_RULE', 'DELETE_RULE',
    'CREATE_OVERRIDE', 'UPDATE_OVERRIDE',
    'APPROVE_STATEMENT', 'RELEASE_STATEMENT',
    'RECOMPUTE', 'INGESTION_RUN', 'NORMALIZATION_RUN'
);

CREATE TABLE audit_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users (user_id) ON DELETE SET NULL,
    action audit_action NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(100),
    before_snapshot JSONB,
    after_snapshot JSONB,
    change_hash VARCHAR(64) NOT NULL,
    reason TEXT,
    correlation_id UUID NOT NULL,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_log_user ON audit_log (user_id);
CREATE INDEX idx_audit_log_action ON audit_log (action);
CREATE INDEX idx_audit_log_resource ON audit_log (resource_type, resource_id);
CREATE INDEX idx_audit_log_timestamp ON audit_log (timestamp);
CREATE INDEX idx_audit_log_correlation ON audit_log (correlation_id);
```

**Key Columns**:
- `before_snapshot`, `after_snapshot`: State before/after change (JSONB)
- `change_hash`: SHA-256 of (user_id || action || resource_id || timestamp) for tamper detection
- `reason`: User-provided justification for action
- `correlation_id`: Request correlation ID for distributed tracing

---

## Data Integrity Constraints

### Referential Integrity
- **ON DELETE CASCADE**: Configuration changes propagate (chains, periods)
- **ON DELETE RESTRICT**: Cannot delete referenced entities (providers, agreements)
- **ON DELETE SET NULL**: Soft references (user deletions in audit log)

### Check Constraints
- **Positive amounts**: All `*_native` columns have `CHECK (amount >= 0)`
- **Valid percentages**: `commission_rate_bps CHECK (commission_rate_bps >= 0 AND commission_rate_bps <= 10000)`
- **Date ranges**: `CHECK (period_start < period_end)`, `CHECK (effective_from < effective_until)`

### Unique Constraints
- **Canonical data**: (chain_id, period_id, validator_key) prevents duplicates
- **Staging idempotency**: (run_id, chain_id, period_id, validator_key, data_type) prevents duplicate ingestion
- **Agreement versions**: (agreement_id, version_number) enforces version sequence

---

## Partitioning Strategy (Future)

For scalability, consider partitioning large tables:

### Range Partitioning by Period
- `staging_payloads` partitioned by `created_at` (monthly partitions)
- `canonical_validator_fees`, `canonical_validator_mev`, `canonical_stake_rewards` partitioned by `period_id` (yearly partitions)
- `partner_commission_lines` partitioned by `period_id` (yearly partitions)

### List Partitioning by Chain
- All canonical tables can be sub-partitioned by `chain_id` for chain isolation

**Example**:
```sql
CREATE TABLE canonical_validator_fees (
    -- columns as defined above
) PARTITION BY RANGE (period_start);

CREATE TABLE canonical_validator_fees_2024 PARTITION OF canonical_validator_fees
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

CREATE TABLE canonical_validator_fees_2025 PARTITION OF canonical_validator_fees
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
```

---

## Materialized Views (Performance Optimization)

### mv_partner_commissions_summary

Monthly commission totals per partner/chain.

```sql
CREATE MATERIALIZED VIEW mv_partner_commissions_summary AS
SELECT
    partner_id,
    chain_id,
    period_id,
    SUM(final_amount_native) AS total_commission_native,
    COUNT(*) AS line_count,
    MAX(computed_at) AS last_computed_at
FROM partner_commission_lines
GROUP BY partner_id, chain_id, period_id;

CREATE UNIQUE INDEX idx_mv_partner_summary ON mv_partner_commissions_summary (partner_id, chain_id, period_id);
```

**Refresh Strategy**: Refresh after each commission computation run.

---

### mv_validator_revenue_summary

Total revenue per validator/chain/period.

```sql
CREATE MATERIALIZED VIEW mv_validator_revenue_summary AS
SELECT
    chain_id,
    period_id,
    validator_key,
    total_revenue_native,
    exec_fees_native,
    mev_tips_native,
    vote_rewards_native,
    commission_native,
    computed_at
FROM validator_pnl;

CREATE UNIQUE INDEX idx_mv_validator_revenue ON mv_validator_revenue_summary (chain_id, period_id, validator_key);
```

**Refresh Strategy**: Refresh after each P&L computation run.

---

## Schema Migration Strategy

### Alembic Migrations
- All schema changes managed via Alembic migration scripts
- Migrations are reversible (downgrade supported)
- Migration scripts include data migrations when needed

### Migration Workflow
1. **Development**: Create migration script, test against dev DB
2. **Staging**: Apply migration to staging, validate data integrity
3. **Production**: Schedule maintenance window, apply migration, verify

### Example Migration Structure
```
migrations/
├── versions/
│   ├── 001_initial_schema.py
│   ├── 002_add_ethereum_support.py
│   ├── 003_add_tier_config.py
│   └── 004_partition_canonical_tables.py
```

---

## Backup & Recovery

### Backup Strategy
- **Full Backups**: Nightly pg_basebackup (retain 30 days)
- **WAL Archiving**: Continuous WAL archiving (retain 7 days)
- **Point-in-Time Recovery**: Supported via WAL replay

### Recovery Procedures
1. **Restore from base backup**: `pg_restore` from nightly backup
2. **Replay WAL**: Apply WAL segments to reach desired point-in-time
3. **Verify data integrity**: Run validation queries, check audit log continuity

---

## Database Security

### Access Control
- **Application User**: `aurora_app` role with SELECT/INSERT/UPDATE/DELETE on all tables
- **Read-Only User**: `aurora_readonly` role with SELECT only
- **Migration User**: `aurora_migrate` role with DDL permissions (used only for migrations)

### Row-Level Security (RLS)

Enable RLS on sensitive tables to enforce partner scoping:

```sql
ALTER TABLE partner_commission_lines ENABLE ROW LEVEL SECURITY;

CREATE POLICY partner_commission_lines_policy ON partner_commission_lines
    FOR SELECT
    USING (
        partner_id = current_setting('app.current_partner_id')::UUID
        OR current_setting('app.current_role') IN ('ADMIN', 'FINANCE', 'AUDITOR')
    );
```

**Application sets session variables**:
```sql
SET app.current_partner_id = '123e4567-e89b-12d3-a456-426614174000';
SET app.current_role = 'PARTNER';
```

---

**Document Version**: 1.0
**Last Updated**: 2025-01-22
**Status**: Draft
