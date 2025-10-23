# System Architecture - Multi-Chain Validator P&L & Partner Commissions

## Executive Summary

This document defines the complete system architecture for the Multi-Chain Validator P&L & Partner Commissions platform. The system computes per-period validator revenue and partner commissions across multiple blockchain networks (starting with Solana, expanding to EVM chains) while maintaining stable intermediary schemas and APIs regardless of data provider changes.

## Architectural Principles

### Core Design Principles
1. **Chain-Agnostic Core** - Business logic independent of specific blockchain implementations
2. **Provider Pluggability** - Data sources swappable without downstream impact
3. **Deterministic Computation** - All calculations reproducible from source data
4. **Audit Trail First** - Every operation logged with full traceability
5. **Security by Default** - RBAC enforced at all layers, partner data isolation
6. **On-Premise First** - Self-hosted deployment with enterprise control

### Technology Stack
- **Runtime**: Python 3.11+
- **Web Framework**: FastAPI with async/await support
- **Data Validation**: Pydantic v2 for schema validation
- **ORM**: SQLAlchemy 2.0+ with Alembic migrations
- **Database**: PostgreSQL 15+ (system of record)
- **Job Scheduling**: Prefect OSS / RQ / cron-based orchestration
- **Reverse Proxy**: Nginx with TLS termination
- **Authentication**: JWT tokens with RBAC enforcement
- **Observability**: Structured JSON logging, Prometheus/Grafana (future)

## System Components

### 1. Chain Registry & Configuration Loader

**Purpose**: Centralized chain definitions and provider mappings

**Responsibilities**:
- Load and validate `chains.yaml` and `providers.yaml`
- Expose chain capabilities (period types, native units, finality lag)
- Provide provider interface factories per chain
- Validate endpoint connectivity on startup

**Key Interfaces**:
```python
class ChainConfig:
    chain_id: str
    name: str
    period_type: PeriodType  # EPOCH, BLOCK_WINDOW, SLOT_RANGE
    native_unit: str
    native_decimals: int
    finality_lag: int
    providers: ProviderMap

class ProviderMap:
    fees: str          # Provider name for execution fees
    mev: str           # Provider name for MEV tips
    rewards: str       # Provider name for staking rewards
    meta: str          # Provider name for validator metadata
    rpc_url: str       # RPC endpoint
```

**Design Patterns**:
- Registry pattern for chain lookup
- Factory pattern for provider instantiation
- Lazy loading with caching for config

---

### 2. Data Source Adapters (Per Chain)

**Purpose**: Abstract data providers behind common interfaces

**Responsibilities**:
- Fetch period lists, fees, MEV tips, staking rewards, metadata
- Handle provider-specific pagination, rate limiting, retries
- Normalize provider responses to canonical formats
- Emit structured traceability metadata

**Provider Interface** (conceptual):
```python
class ChainDataProvider(ABC):
    @abstractmethod
    async def list_periods(self, start: datetime, end: datetime) -> List[Period]:
        """Return finalized periods in range"""

    @abstractmethod
    async def get_validator_period_fees(
        self, period: Period, validator_identity: str
    ) -> ValidatorFees:
        """Fetch execution fees for validator in period"""

    @abstractmethod
    async def get_validator_period_mev(
        self, period: Period, validator_identity: str
    ) -> ValidatorMEV:
        """Fetch MEV tips for validator in period"""

    @abstractmethod
    async def get_stake_rewards(
        self, period: Period, validator_identity: str
    ) -> StakeRewards:
        """Fetch staking rewards for validator in period"""

    @abstractmethod
    async def get_validator_meta(
        self, period: Period, validator_identity: str
    ) -> ValidatorMeta:
        """Fetch validator metadata (commission%, MEV client status)"""
```

**Adapter Implementations**:
- **Solana Adapters**: SolanaBeach (fees), Jito (MEV), RPC (rewards), Stakewiz (meta)
- **Ethereum Adapters**: BlockFees (execution), MEVRelay (PBS tips), ConsensusAPI (rewards), BeaconAPI (meta)

**Design Patterns**:
- Adapter pattern for provider normalization
- Template method for common retry/pagination logic
- Circuit breaker for provider failures

---

### 3. Ingestion Orchestrator

**Purpose**: Schedule and coordinate data ingestion across chains and periods

**Responsibilities**:
- Determine finalized periods per chain (respecting finality lag)
- Schedule provider fetches per chain/period/validator
- Write raw payloads to staging tables with full metadata
- Handle ingestion failures with exponential backoff
- Emit ingestion health metrics

**Orchestration Flow**:
```
1. Load chain configs → Discover finalized periods per chain
2. For each (chain, period):
   - Check if already ingested (idempotency)
   - Fetch data from all providers (fees, MEV, rewards, meta)
   - Write raw JSON payloads to staging with metadata:
     - chain_id, period_id, validator_key
     - provider_name, provider_version
     - fetch_timestamp, response_hash
     - raw_payload (JSONB)
3. Mark ingestion run complete with audit log entry
```

**Key Data Structures**:
```python
class IngestionRun:
    run_id: UUID
    chain_id: str
    period_start: datetime
    period_end: datetime
    started_at: datetime
    completed_at: Optional[datetime]
    status: IngestionStatus  # PENDING, RUNNING, SUCCESS, FAILED
    error_message: Optional[str]

class StagingPayload:
    payload_id: UUID
    run_id: UUID
    chain_id: str
    period_id: str
    validator_key: str
    provider_name: str
    provider_version: str
    data_type: DataType  # FEES, MEV, REWARDS, META
    fetch_timestamp: datetime
    response_hash: str
    raw_payload: dict  # JSONB
```

**Design Patterns**:
- Job queue pattern for scheduled tasks
- Idempotency keys for duplicate prevention
- Saga pattern for multi-provider coordination

---

### 4. Normalization & Reconciliation

**Purpose**: Transform staging data into canonical schema with consistency checks

**Responsibilities**:
- Map staging payloads to canonical entities
- Apply source priority when multiple providers exist
- Detect and report data drift/inconsistencies
- Produce reconciliation reports with deltas
- Emit normalization audit events

**Normalization Flow**:
```
1. For each ingestion run:
   - Group staging payloads by (chain, period, validator, data_type)
   - Apply transformation rules per provider adapter
   - Write to canonical tables (fees, mev, rewards, metadata)
   - Track source attribution (which provider, which payload)

2. Reconciliation:
   - Compare new canonical data vs. previous version
   - Flag significant deltas (> threshold)
   - Generate drift reports for manual review
   - Alert on missing expected data
```

**Canonical Entities**:
```python
class CanonicalValidatorFees:
    chain_id: str
    period_id: str
    validator_key: str
    total_fees_native: Decimal  # In native units (lamports, wei)
    fee_count: int
    source_provider: str
    source_payload_id: UUID
    normalized_at: datetime

class CanonicalValidatorMEV:
    chain_id: str
    period_id: str
    validator_key: str
    total_mev_native: Decimal
    tip_count: int
    source_provider: str
    source_payload_id: UUID
    normalized_at: datetime

class CanonicalStakeRewards:
    chain_id: str
    period_id: str
    validator_key: str
    staker_address: Optional[str]  # Aggregated if null
    rewards_native: Decimal
    commission_native: Decimal
    source_provider: str
    source_payload_id: UUID
    normalized_at: datetime

class CanonicalValidatorMeta:
    chain_id: str
    period_id: str
    validator_key: str
    commission_rate_bps: int  # Basis points
    is_mev_enabled: bool
    total_stake_native: Decimal
    source_provider: str
    source_payload_id: UUID
    normalized_at: datetime
```

**Design Patterns**:
- ETL pipeline pattern
- Data reconciliation with versioning
- Event sourcing for audit trail

---

### 5. Intermediary Canonical Data Layer

**Purpose**: Stable, chain-aware data layer independent of provider changes

**Characteristics**:
- **Stability**: Schema unchanged when providers swap
- **Traceability**: Every row links to source staging payload
- **Chain-Aware**: All tables partitioned/indexed by chain_id
- **Immutable Core**: Historical data never deleted (only marked superseded)
- **Audit Ready**: Full lineage from raw → canonical → computed

**Core Tables**:
- `canonical_periods` - Period definitions per chain
- `canonical_validator_fees` - Execution fees per validator/period
- `canonical_validator_mev` - MEV tips per validator/period
- `canonical_stake_rewards` - Staking rewards per validator/period
- `canonical_validator_meta` - Validator metadata per period
- `canonical_validator_identities` - Chain-specific identity mappings

**Indexing Strategy**:
- Primary: (chain_id, period_id, validator_key)
- Foreign keys to staging payloads
- Timestamps for temporal queries
- Hash indexes for source attribution

---

### 6. Commission Engine (Chain-Aware)

**Purpose**: Compute validator P&L and partner commission lines deterministically

**Responsibilities**:
- Aggregate canonical data into validator P&L per period
- Apply partner agreement rules to attribute revenue
- Compute commission amounts with floors/caps/tiers
- Generate commission lines with full audit trail
- Support re-computation for period ranges

**Computation Flow**:
```
1. Validator P&L Calculation (per chain, period, validator):
   - Total Revenue = Fees + MEV + Stake Rewards (post-commission)
   - Component Breakdown:
     - EXEC_FEES: canonical_validator_fees.total_fees_native
     - MEV_TIPS: canonical_validator_mev.total_mev_native
     - VOTE_REWARDS: canonical_stake_rewards.rewards_native (validator portion)
     - COMMISSION: canonical_stake_rewards.commission_native

2. Partner Commission Attribution:
   - Load active agreements for period
   - For each agreement:
     - Apply filters (chain, validator, revenue component)
     - Calculate attribution per method:
       - CLIENT_REVENUE: % of specific client's delegated stake revenue
       - STAKE_WEIGHT: % proportional to partner's introduced stake
       - FIXED_SHARE: Fixed % of total revenue component
     - Apply floors, caps, tier escalations
     - Generate commission line with pre-override amount

3. Override Application:
   - Load manual overrides for (agreement, period)
   - Apply override to commission line
   - Track override reason, user, timestamp

4. Final Commission:
   - Sum all commission lines per partner per period
   - Store final amount in partner_commission_statements
```

**Key Data Structures**:
```python
class ValidatorPnL:
    chain_id: str
    period_id: str
    validator_key: str
    exec_fees_native: Decimal
    mev_tips_native: Decimal
    vote_rewards_native: Decimal
    commission_native: Decimal
    total_revenue_native: Decimal
    computed_at: datetime

class PartnerCommissionLine:
    line_id: UUID
    agreement_id: UUID
    agreement_version: int
    chain_id: str
    period_id: str
    validator_key: Optional[str]  # Null if aggregated
    revenue_component: RevenueComponent
    attribution_method: AttributionMethod
    base_amount_native: Decimal
    commission_rate_bps: int
    pre_override_amount_native: Decimal
    override_amount_native: Optional[Decimal]
    override_reason: Optional[str]
    override_user_id: Optional[UUID]
    override_timestamp: Optional[datetime]
    final_amount_native: Decimal
    computed_at: datetime
```

**Design Patterns**:
- Strategy pattern for attribution methods
- Command pattern for re-computation jobs
- Event sourcing for commission history

---

### 7. User & Access Layer (RBAC)

**Purpose**: Centralized authentication, authorization, and audit logging

**Responsibilities**:
- Authenticate users via JWT tokens (OAuth2 password flow or SSO)
- Enforce role-based access control (Admin, Finance, Ops, Partner, Auditor)
- Scope partner users to their introductions and commissions
- Log all sensitive actions (agreement changes, overrides, exports)
- Provide audit trail queries

**RBAC Model**:
```python
class User:
    user_id: UUID
    username: str
    email: str
    role: UserRole  # ADMIN, FINANCE, OPS, PARTNER, AUDITOR
    introducer_id: Optional[UUID]  # Set for PARTNER role
    allowed_chain_ids: Optional[List[str]]  # Scope restriction
    allowed_validator_keys: Optional[List[str]]  # Scope restriction
    is_active: bool
    created_at: datetime

class UserRole(str, Enum):
    ADMIN = "admin"
    FINANCE = "finance"
    OPS = "ops"
    PARTNER = "partner"
    AUDITOR = "auditor"
```

**Access Control Rules**:
- **Admin**: Full read/write access to all resources
- **Finance**: Read/write agreements, overrides; read all data
- **Ops**: Manage ingestion, recompute; read system health
- **Partner**: Read-only access scoped to `introducer_id` and mapped clients/validators
- **Auditor**: Read-only access to all data (time-boxed)

**Row-Level Security** (enforced in repository layer):
```python
async def get_partner_commissions(
    user: User,
    chain_id: str,
    introducer_id: UUID,
    period_range: PeriodRange
) -> List[PartnerCommissionLine]:
    # Enforce scoping
    if user.role == UserRole.PARTNER:
        if introducer_id != user.introducer_id:
            raise Forbidden("Access denied to other partner data")

    # Apply chain scoping if set
    if user.allowed_chain_ids and chain_id not in user.allowed_chain_ids:
        raise Forbidden(f"Access denied to chain {chain_id}")

    # Fetch with filters
    return await repo.get_commission_lines(
        chain_id=chain_id,
        introducer_id=introducer_id,
        period_range=period_range
    )
```

**Audit Logging**:
```python
class AuditLog:
    log_id: UUID
    user_id: UUID
    action: AuditAction  # CREATE_AGREEMENT, UPDATE_RULE, CREATE_OVERRIDE, etc.
    resource_type: str
    resource_id: str
    before_snapshot: Optional[dict]  # JSONB
    after_snapshot: Optional[dict]  # JSONB
    change_hash: str
    reason: Optional[str]
    timestamp: datetime
    correlation_id: UUID  # Request correlation ID
```

**Design Patterns**:
- RBAC with claims-based authorization
- Repository pattern with scoping mixins
- Append-only audit log (event sourcing)

---

### 8. Internal API (FastAPI)

**Purpose**: Chain-scoped REST API with RBAC enforcement

**Characteristics**:
- **Versioned**: All endpoints under `/v1/` namespace
- **Chain-Scoped**: Chain ID required for most operations
- **RBAC Enforced**: JWT middleware validates permissions before DB access
- **Paginated**: List endpoints support `limit`/`offset`
- **Consistent Responses**: Standardized JSON format

**Core Endpoints**:

**Chain Operations**:
```
GET /v1/chains
    → List all configured chains
    Response: { data: [ChainSummary], error: null }

GET /v1/chains/{chain_id}/periods?from=<date>&to=<date>
    → List finalized periods for chain
    Response: { data: [Period], error: null }
```

**Validator P&L**:
```
GET /v1/chains/{chain_id}/validators/{validator_key}/pnl?from=<period>&to=<period>
    → Validator P&L over period range
    RBAC: Partner sees only if scoped to this validator
    Response: { data: [ValidatorPnL], error: null }
```

**Partner Commissions**:
```
GET /v1/chains/{chain_id}/partners/{introducer_id}/commissions?from=<period>&to=<period>
    → Partner commission lines
    RBAC: Partner can only query self (introducer_id == token.introducer_id)
    Response: { data: [PartnerCommissionLine], error: null }

GET /v1/chains/{chain_id}/partners/{introducer_id}/statements/{period_id}
    → Monthly commission statement
    RBAC: Partner self-only; Finance/Admin all
    Response: { data: CommissionStatement, error: null }
```

**Agreements Management**:
```
GET /v1/agreements?introducer_id=<uuid>
    → List agreements (Finance/Admin only)
    Response: { data: [Agreement], error: null }

GET /v1/agreements/{id}
    → Agreement details
    RBAC: Finance/Admin

GET /v1/agreements/{id}/versions
    → Agreement version history
    RBAC: Finance/Admin

POST /v1/agreements
    → Create new agreement
    RBAC: Finance/Admin
    Body: AgreementCreate schema

PUT /v1/agreements/{id}
    → Update agreement (creates new version)
    RBAC: Finance/Admin
    Body: AgreementUpdate schema
```

**Overrides**:
```
POST /v1/overrides
    → Create commission override
    RBAC: Finance/Admin
    Body: { agreement_id, period_id, amount_native, reason }
```

**Operations**:
```
POST /v1/recompute
    → Recompute P&L and commissions for period range
    RBAC: Finance/Admin/Ops
    Body: { chain_id, from_period, to_period }

GET /v1/ingestion/health
    → Ingestion health and lag metrics
    RBAC: Ops/Admin
    Response: { data: IngestionHealth, error: null }
```

**Middleware Stack**:
1. **Correlation ID Injection** - Generate/extract request correlation ID
2. **Authentication** - Validate JWT, extract user claims
3. **Authorization** - Verify role permissions for endpoint
4. **Request Logging** - Log all requests with correlation ID
5. **Error Handling** - Convert exceptions to standard error responses
6. **Response Formatting** - Wrap responses in `{ data, error }` envelope

**Design Patterns**:
- Dependency injection for services/repos
- Repository pattern with scoping
- DTO (Pydantic schemas) for validation

---

### 9. Internal UI

**Purpose**: Web-based dashboards for internal users and partners

**Components**:

**Admin/Finance/Ops Portal**:
- **Dashboard**: System health, ingestion status, recent activity
- **Chain Management**: Configure chains, providers, validator identities
- **Validator P&L Viewer**: Multi-chain P&L with filtering, CSV export
- **Partner Management**: View all partners, agreements, commissions
- **Agreement Editor**: Create/update agreements, manage rules, view versions
- **Override Workflow**: Create overrides with reason tracking
- **Audit Log Viewer**: Search and filter audit events
- **Ingestion Monitor**: View ingestion runs, reconciliation reports, drift alerts

**Partner Portal** (read-only):
- **Commission Summary**: Current and historical commissions per period
- **Client List**: View clients introduced (with attribution)
- **Statement Export**: Download monthly CSV/PDF statements
- **Agreement View**: Read-only access to own agreements

**Technology Stack** (recommended):
- **Framework**: React + TypeScript (or Next.js for SSR)
- **State Management**: React Query for API data caching
- **UI Library**: Material-UI or Tailwind CSS
- **Charts**: Recharts or Chart.js for P&L visualization
- **Authentication**: JWT stored in httpOnly cookies

**Design Patterns**:
- Component-based architecture
- API-first design (UI is thin client)
- Role-based view rendering

---

### 10. Ops & Observability

**Purpose**: System health monitoring, alerting, and operational tooling

**Observability Features**:

**Structured Logging**:
- All services log JSON with fields:
  - `timestamp`, `level`, `correlation_id`, `event`, `context`
- Log categories:
  - `ingestion.*` - Data fetching, staging writes
  - `normalization.*` - Canonical mapping, reconciliation
  - `computation.*` - P&L and commission calculations
  - `api.*` - HTTP request/response logs
  - `auth.*` - Authentication/authorization events

**Health Endpoints**:
```
GET /health
    → Liveness check (200 if server responding)

GET /health/ready
    → Readiness check (DB connectivity, critical services)

GET /health/ingestion
    → Ingestion lag per chain (latest period vs. expected)
    Response: {
        chain_id: {
            expected_period: "850",
            latest_ingested: "848",
            lag_periods: 2,
            last_success: "2025-01-20T10:00:00Z"
        }
    }
```

**Metrics (Prometheus format)**:
- `ingestion_runs_total{chain_id, status}` - Ingestion run counts
- `ingestion_duration_seconds{chain_id}` - Ingestion run duration
- `normalization_records_total{chain_id, data_type}` - Normalized record counts
- `commission_lines_total{chain_id, attribution_method}` - Commission line counts
- `api_requests_total{method, path, status}` - API request counts
- `api_request_duration_seconds{method, path}` - API latency

**Alerting** (future):
- Ingestion lag > threshold (e.g., 5 periods behind)
- Reconciliation drift > threshold (e.g., 10% delta)
- API error rate > threshold (e.g., 5% 5xx responses)
- Provider failures (circuit breaker tripped)

**Operational Tools**:
- **Backfill Script**: Backfill historical periods for chain
- **Recompute CLI**: Trigger recomputation from command line
- **Data Integrity Checker**: Verify canonical data completeness
- **Agreement Validator**: Validate agreement rule logic

**Design Patterns**:
- OpenTelemetry for observability (future)
- Circuit breaker for external dependencies
- Graceful degradation (serve cached data on provider failure)

---

## Data Flow Architecture

### End-to-End Flow (Solana Example)

```
1. INGESTION (Epoch 850):
   ChainRegistry → Load Solana config
   IngestionOrchestrator → Check finality (epoch 850 finalized?)
   ↓
   SolanaBeachAdapter.get_fees(epoch=850) → raw JSON to staging
   JitoAdapter.get_mev(epoch=850) → raw JSON to staging
   RPCAdapter.get_rewards(epoch=850) → raw JSON to staging
   StakewizAdapter.get_meta(epoch=850) → raw JSON to staging
   ↓
   Mark IngestionRun complete with audit log

2. NORMALIZATION:
   NormalizationEngine → Load staging payloads for epoch 850
   ↓
   Transform to canonical entities:
     - canonical_validator_fees (validator=ABC, fees=1.5 SOL)
     - canonical_validator_mev (validator=ABC, mev=0.8 SOL)
     - canonical_stake_rewards (validator=ABC, rewards=2.0 SOL, commission=0.1 SOL)
     - canonical_validator_meta (validator=ABC, commission_rate=5%, is_mev=true)
   ↓
   Reconciliation: Compare vs. epoch 849 data, flag deltas
   ↓
   Mark NormalizationRun complete with audit log

3. COMPUTATION:
   CommissionEngine → Compute P&L for epoch 850
   ↓
   Validator ABC P&L:
     - Exec Fees: 1.5 SOL
     - MEV Tips: 0.8 SOL
     - Vote Rewards: 2.0 SOL (validator portion)
     - Commission: 0.1 SOL (from delegator stakes)
     - Total Revenue: 4.4 SOL
   ↓
   Apply partner agreements:
     - Agreement A (Introducer=Partner-123):
       - Rule: CLIENT_REVENUE, 10% of client XYZ's stake rewards
       - Client XYZ delegated 1M SOL, earned 0.5 SOL rewards
       - Commission: 0.5 * 10% = 0.05 SOL
     - Agreement B (Introducer=Partner-456):
       - Rule: FIXED_SHARE, 5% of all MEV tips
       - Commission: 0.8 * 5% = 0.04 SOL
   ↓
   Generate commission lines with audit metadata
   ↓
   Mark ComputationRun complete with audit log

4. API ACCESS:
   Partner-123 calls:
   GET /v1/chains/solana-mainnet/partners/{partner-123}/commissions?from=850&to=850
   ↓
   API Middleware:
     - Authenticate JWT → Extract user_id, role=PARTNER, introducer_id=Partner-123
     - Authorize: Check introducer_id == Partner-123 ✓
   ↓
   Repository Layer:
     - Query commission_lines WHERE introducer_id=Partner-123 AND period=850
     - Apply row-level scoping (already filtered by introducer_id)
   ↓
   Response: { data: [CommissionLine(amount=0.05 SOL)], error: null }
```

### Cross-Chain Extension (Ethereum)

When Ethereum is added:
1. **Chain Registry**: Add `ethereum-mainnet` with `BLOCK_WINDOW` period type
2. **Adapters**: Implement EVM-specific adapters (BlockFees, MEVRelay, ConsensusAPI, BeaconAPI)
3. **Normalization**: EVM normalizer maps wei → Decimal, handles fee_recipient → validator_key
4. **Commission Engine**: Extend to handle Ethereum reward semantics (proposer + attestation rewards)
5. **API**: Same endpoints, just with `chain_id=ethereum-mainnet`
6. **RBAC**: Partner scoping works identically across chains

**Key Invariant**: Canonical schema and API remain unchanged; only adapters and engine know chain specifics.

---

## Deployment Architecture

### On-Premise Deployment (MVP)

**Infrastructure Components**:
```
[Internet] → [Nginx (TLS, reverse proxy)]
              ↓
              [FastAPI App (multiple workers)]
              ↓
              [PostgreSQL 15+ (primary DB)]
              ↓
              [Job Scheduler (Prefect/RQ/cron)]
```

**Server Layout**:
- **Web Server**: Nginx (port 443) → FastAPI (port 8000)
- **Database**: PostgreSQL (port 5432, localhost-only)
- **Job Scheduler**: Prefect/RQ workers (internal)
- **Monitoring**: File-based logs → (future) Prometheus/Grafana

**Security Measures**:
- TLS certificates (Let's Encrypt or internal CA)
- JWT tokens with rotation policy (30-day expiry)
- PostgreSQL: Row-level security (RLS) for partner data isolation
- Firewall: Only port 443 exposed externally
- Environment secrets via `.env` file (not in git)

**Backup Strategy**:
- Nightly base backups (pg_basebackup)
- WAL archiving for point-in-time recovery
- Retention: 30 days base backups, 7 days WAL
- Off-site backup copy (S3-compatible storage)

**Scaling Strategy** (future):
- Horizontal: Add FastAPI workers behind Nginx load balancer
- Vertical: Increase PostgreSQL resources (CPU, RAM)
- Read Replicas: For heavy read queries (partner dashboards)
- ClickHouse: For analytics/reporting (post-MVP)

---

## Security & Compliance

### Authentication & Authorization
- **AuthN**: OAuth2 Password flow (username/password → JWT) or SSO (OIDC/SAML)
- **AuthZ**: RBAC enforced at API and repository layers
- **Token Claims**: `user_id`, `role`, `introducer_id`, `allowed_chain_ids`, `allowed_validator_keys`
- **Token Rotation**: 30-day expiry, refresh tokens for long-lived sessions

### Data Protection
- **PII Minimization**: Only store partner contact + legal entities; no sensitive client PII
- **Encryption**: TLS in transit, disk encryption at rest (LUKS or cloud-native)
- **Access Logs**: All access to partner data logged with correlation IDs
- **Data Isolation**: Partner users cannot query other partners' data (enforced via RLS)

### Audit Trail
- **Immutable Log**: All mutating actions (agreements, overrides, recomputes) logged to `audit_log` table
- **Snapshot Capture**: Before/after snapshots for agreement changes
- **Hash Verification**: Change hashes prevent tampering
- **Retention**: Audit logs retained indefinitely (regulatory compliance)

### Compliance Controls
- **Dual Approval** (optional): Require two Finance users to approve monthly statement releases
- **Audit Log Queries**: Auditors can query full audit trail (read-only)
- **Backup & DR**: Documented restore procedures, tested quarterly

---

## Scalability & Performance

### Performance Targets (MVP)
- **API Latency**: <300ms p95 for typical queries on local dataset
- **Ingestion Throughput**: Backfill 100 epochs in <1 hour (Solana)
- **Recomputation**: Recompute 1 month of data (<10 periods) in <5 minutes
- **Concurrent Users**: Support 50 concurrent API users

### Optimization Strategies
- **Indexing**: Composite indexes on (chain_id, period_id, validator_key)
- **Caching**: Redis/in-memory cache for chain configs, provider metadata (future)
- **Batch Processing**: Bulk inserts for staging/canonical data
- **Async I/O**: FastAPI async handlers, httpx for provider calls
- **Connection Pooling**: SQLAlchemy connection pool (min=5, max=20)

### Horizontal Scaling (Future)
- **API Layer**: Stateless FastAPI workers behind load balancer
- **Job Layer**: Distributed task queue (Celery, RQ) with multiple workers
- **Database**: Read replicas for heavy analytics queries
- **Analytics DB**: ClickHouse for aggregated reporting (offload from PostgreSQL)

---

## Glossary

- **Period**: Time window for rewards computation (epoch, block range, slot range)
- **Finality Lag**: Number of periods to wait before considering data final
- **Canonical Data**: Normalized, provider-independent data in stable schema
- **Staging Payload**: Raw JSON response from external provider
- **Attribution Method**: Algorithm for assigning revenue to partners (CLIENT_REVENUE, STAKE_WEIGHT, FIXED_SHARE)
- **Commission Line**: Single computed commission amount for agreement + period
- **Override**: Manual adjustment to computed commission with reason tracking
- **RBAC**: Role-Based Access Control
- **RLS**: Row-Level Security (database-enforced data isolation)

---

**Document Version**: 1.0
**Last Updated**: 2025-10-22
**Status**: Draft
