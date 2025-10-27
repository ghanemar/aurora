# Aurora Project Structure

**AI agents MUST read this file to understand the complete technology stack and file organization before making any changes.**

## Technology Stack

### Backend Technologies
- **Python 3.11+** with **Poetry** - Dependency management and packaging
- **FastAPI 0.115.0+** - Async web framework with type hints and automatic API documentation
- **Uvicorn 0.32.0+** - ASGI server for production deployment
- **Pydantic 2.x** - Data validation and settings management with type annotations

### Database & ORM
- **PostgreSQL 15+** - Primary relational database via Docker Compose (system of record)
- **SQLAlchemy 2.0+** - Async ORM with connection pooling (size: 10, max_overflow: 20)
- **asyncpg** - High-performance async PostgreSQL adapter
- **Alembic** - Database migration management
- **Redis 7+** - Caching and session storage via Docker Compose

### Job Scheduling & Background Tasks
- **Prefect OSS / RQ** - Job orchestration and background task processing
- **APScheduler** - Cron-like scheduling for periodic ingestion

### Authentication & Security
- **python-jose** - JWT token creation and validation
- **passlib + bcrypt** - Password hashing
- **python-multipart** - Form data handling for OAuth2

### HTTP Clients & External APIs
- **httpx** - Async HTTP client for provider API calls
- **tenacity** - Retry logic with exponential backoff

### Development & Quality Tools
- **Black** - Code formatting (line length: 100)
- **Ruff** - Fast Python linter (replaces flake8, isort, pylint)
- **mypy** - Static type checking
- **pytest** - Testing framework with async support
- **pytest-cov** - Code coverage reporting
- **pytest-asyncio** - Async test support

### Infrastructure & Deployment
- **Nginx** - Reverse proxy with TLS termination
- **Docker + Docker Compose** - Containerization for consistent deployment
- **systemd** - Alternative to Docker for on-premise deployment

### Observability
- **structlog** - Structured JSON logging
- **Prometheus client** (future) - Metrics export
- **Grafana** (future) - Metrics visualization

### Frontend Technologies (Future)
- **React + TypeScript** - UI framework for admin and partner portals
- **React Query (TanStack Query)** - API data caching and state management
- **Material-UI or Tailwind CSS** - UI component library
- **Vite** - Build tool and development server

---

## Documentation Status Legend

This document uses status markers to distinguish between implemented and planned structure:

- **✅ Implemented** - Currently exists in the codebase and is ready to use
- **📋 Planned** - Architectural guidance for future implementation, create as needed

**AI Agent Principle**: Only create directories and files as needed for your specific task. The planned structure below provides organizational guidance, not mandatory scaffolding.

---

## Current Implementation Status

**Completed Setup (as of 2025-10-27)**:
- ✅ Python 3.11+ project with Poetry dependency management
- ✅ Configuration management (`src/config/`) with Pydantic Settings and YAML loaders
- ✅ Database infrastructure (`src/db/`) with async SQLAlchemy and connection pooling
- ✅ Docker Compose with PostgreSQL 15 and Redis 7
- ✅ Complete ORM data layer (`src/core/models/`) with chain registry, staging, canonical, and computation models
- ✅ Test framework with 122 passing tests and 84% coverage
- ✅ Type checking with mypy, linting with ruff and black
- ✅ Security infrastructure (`src/core/security.py`, `src/core/logging.py`)

**GitHub Issues Completed**: #1 (Python + Poetry), #2 (Config loaders), #3 (PostgreSQL + Docker), #6 (Chain registry ORM models), #7 (Staging layer ORM models), #8 (Canonical layer ORM models), #9 (Computation layer ORM models)

**Next Phase**: Database migrations with Alembic (Issue #10), then data ingestion adapters (Issues #11-14)

---

## Target Project Structure

**Legend**: ✅ = Implemented | 📋 = Planned (create as needed)

```
aurora/
├── ✅ README.md                        # Project overview and setup instructions
├── ✅ CLAUDE.md                        # Master AI context file
├── 📋 MCP-ASSISTANT-RULES.md          # MCP server AI assistant context
├── ✅ pyproject.toml                   # Poetry package configuration
├── ✅ poetry.lock                      # Locked dependencies
├── ✅ .gitignore                       # Git ignore patterns
├── ✅ .env.example                     # Environment variable template
├── ✅ conftest.py                      # Root pytest configuration
├── ✅ docker-compose.yml               # Docker services (PostgreSQL, Redis)
├── 📋 Makefile                        # Common development tasks
├── 📋 alembic.ini                     # Alembic migration configuration
├── ✅ chains.yaml                      # Chain registry configuration
├── ✅ providers.yaml                   # Data provider configuration
├── 📋 rbac_policy.md                  # RBAC policy matrix
│
├── src/                                # Source code
│   ├── ✅ __init__.py
│   ├── 📋 py.typed                    # PEP 561 type checking marker
│   ├── 📋 main.py                     # FastAPI application entry point (create when implementing API)
│   │
│   ├── ✅ config/                      # Configuration management (IMPLEMENTED)
│   │   ├── ✅ __init__.py
│   │   ├── ✅ settings.py              # Pydantic settings from environment
│   │   ├── ✅ models.py                # Configuration data models
│   │   ├── ✅ chains.py                # Chain configuration loader
│   │   └── ✅ providers.py             # Provider configuration loader
│   │
│   ├── ✅ db/                          # Database management (IMPLEMENTED)
│   │   ├── ✅ __init__.py
│   │   └── ✅ session.py               # Async SQLAlchemy session factory
│   │
│   ├── ✅ core/                        # Core business logic (PARTIALLY IMPLEMENTED)
│   │   ├── ✅ __init__.py
│   │   ├── ✅ models/                  # SQLAlchemy ORM models (PARTIALLY IMPLEMENTED)
│   │   │   ├── ✅ __init__.py
│   │   │   ├── ✅ base.py              # Base model with common timestamp fields
│   │   │   ├── ✅ chains.py            # Chain, Provider, ChainProviderMapping, CanonicalPeriod, CanonicalValidatorIdentity
│   │   │   ├── ✅ staging.py           # IngestionRun, StagingPayload, IngestionStatus, DataType
│   │   │   ├── ✅ canonical.py         # CanonicalValidatorFees, CanonicalValidatorMEV, CanonicalStakeRewards, CanonicalValidatorMeta
│   │   │   └── 📋 ... (computation.py, agreements.py, users.py)
│   │   │
│   │   ├── 📋 schemas/                 # Pydantic request/response schemas (create when implementing API)
│   │   │   └── 📋 ... (chains.py, validators.py, commissions.py, agreements.py, auth.py, common.py)
│   │   │
│   │   ├── 📋 services/                # Business logic services (create when implementing features)
│   │   │   └── 📋 ... (ingestion.py, normalization.py, commission_engine.py, etc.)
│   │   │
│   │   ├── 📋 repositories/            # Database access layer (create when implementing data access)
│   │   │   └── 📋 ... (base.py, chains.py, staging.py, canonical.py, etc.)
│   │   │
│   │   └── 📋 utils/                   # Core utilities (create as needed)
│   │       └── 📋 ... (logging.py, validation.py, decimals.py, hashing.py)
│   │
│   ├── 📋 adapters/                    # External data provider adapters (create when implementing ingestion)
│   │   ├── 📋 base.py                  # Base adapter interface
│   │   ├── 📋 solana/                  # Solana-specific adapters
│   │   └── 📋 ethereum/                # Ethereum-specific adapters (M1)
│   │
│   ├── 📋 api/                         # FastAPI routes and middleware (create when implementing API)
│   │   ├── 📋 deps.py                  # Dependency injection (DB, auth, etc.)
│   │   ├── 📋 middleware/              # API middleware
│   │   └── 📋 v1/                      # API v1 endpoints
│   │
│   └── 📋 jobs/                        # Background job definitions (create when implementing background tasks)
│       └── 📋 ... (ingestion.py, normalization.py, computation.py, scheduler.py)
│
├── ✅ tests/                           # Test suite
│   ├── ✅ conftest.py                  # Pytest fixtures and async database session
│   ├── ✅ unit/                        # Unit tests
│   │   ├── ✅ test_config/             # Configuration module tests
│   │   │   ├── ✅ __init__.py
│   │   │   ├── ✅ test_chains.py       # Chain registry tests
│   │   │   ├── ✅ test_models.py       # Configuration model tests
│   │   │   └── ✅ test_providers.py    # Provider registry tests
│   │   ├── ✅ test_models_chains.py    # ORM model tests for chain registry
│   │   ├── ✅ test_models_staging.py   # ORM model tests for staging layer
│   │   └── ✅ test_models_canonical.py # ORM model tests for canonical layer
│   ├── 📋 integration/                 # Integration tests (create when implementing API)
│   └── 📋 fixtures/                    # Shared test data (create as needed)
│
└── ✅ docs/                            # Documentation
    ├── ✅ README.md                    # Documentation index
    ├── ✅ system-architecture.md       # Complete system architecture
    ├── ✅ database-schema.md           # Database schema documentation
    ├── ✅ api-specification.md         # API specification with examples
    ├── ✅ design-summary.md            # Design summary
    ├── ✅ github-issues-plan.md        # GitHub issues and milestones
    ├── 📋 rbac_policy.md               # RBAC policy matrix (create when implementing RBAC)
    │
    ├── ✅ ai-context/                  # AI-specific documentation
    │   ├── ✅ project-structure.md     # This file
    │   ├── ✅ docs-overview.md         # Documentation architecture guide
    │   ├── ✅ system-integration.md    # Cross-component integration patterns
    │   ├── ✅ deployment-infrastructure.md # Infrastructure and deployment
    │   └── ✅ HANDOFF.md               # Task management and session continuity
    │
    ├── ✅ specs/                       # Feature specifications
    │   ├── ✅ example-feature-specification.md
    │   └── ✅ example-api-integration-spec.md
    │
    ├── ✅ open-issues/                 # Issue tracking
    │   └── ✅ example-api-performance-issue.md
    │
    └── 📋 CONTEXT-*.md                 # Tier 2/3 component documentation (create as features are built)
```

---

## AI Agent Guidance

### Architectural Principles for Implementation

When implementing features, AI agents should follow these organizational principles:

**1. Create Structure As Needed**
- Only create directories and files required for your specific task
- The 📋 Planned structure above is guidance, not mandatory scaffolding
- If your task needs a new file in `src/core/services/`, create just that file (not all service files)

**2. Respect Architectural Layers**
This project follows a layered architecture. Always place code in the appropriate layer:

```
┌─────────────────────────────────────────┐
│  API Layer (src/api/)                   │  ← FastAPI routes, middleware, dependencies
├─────────────────────────────────────────┤
│  Service Layer (src/core/services/)     │  ← Business logic orchestration
├─────────────────────────────────────────┤
│  Repository Layer (src/core/repositories/)│ ← Database access, query abstraction
├─────────────────────────────────────────┤
│  Model Layer (src/core/models/)         │  ← SQLAlchemy ORM models
├─────────────────────────────────────────┤
│  Adapter Layer (src/adapters/)          │  ← External provider integrations
├─────────────────────────────────────────┤
│  Infrastructure (src/db/, src/config/)  │  ← Database sessions, configuration
└─────────────────────────────────────────┘
```

**3. Layer Interaction Rules**
- ✅ **DO**: API → Service → Repository → Model
- ✅ **DO**: Service → Adapter (for external data)
- ❌ **DON'T**: API → Repository directly (bypass service layer)
- ❌ **DON'T**: Model → Service (models should be data-only)

**4. File Organization Patterns**
- **Models**: Group related entities (e.g., `chains.py` has Chain, Provider, Period models)
- **Services**: One service per business domain (e.g., `ingestion.py`, `commission_engine.py`)
- **Repositories**: Mirror model files (e.g., `chains.py` repository for `chains.py` models)
- **Schemas**: Mirror API endpoints (e.g., `validators.py` DTOs for `/validators` endpoint)

**5. When to Create New Structure**
- **Models**: When implementing new database tables
- **Schemas**: When implementing new API endpoints
- **Services**: When implementing new business logic
- **Repositories**: When models need database access
- **Adapters**: When integrating new external data providers
- **Utils**: When creating shared utilities used across multiple modules

**6. Testing Conventions**
- Create test files in `tests/unit/` or `tests/integration/` mirroring source structure
- Test file names: `test_<module>.py` (e.g., `test_ingestion.py` for `ingestion.py`)
- Place shared test fixtures in `tests/fixtures/`

### Implementation Workflow Example

**Task**: "Implement validator P&L endpoint"

```
Step 1: Identify layers needed
  - Model: src/core/models/computation.py (ValidatorPnL)
  - Schema: src/core/schemas/validators.py (ValidatorPnLResponse)
  - Repository: src/core/repositories/validators.py (ValidatorRepository)
  - Service: src/core/services/validator_pnl.py (ValidatorPnLService)
  - API: src/api/v1/validators.py (GET /validators/{key}/pnl)

Step 2: Create only what's needed
  - If ValidatorPnL model already exists, skip model creation
  - If other computation models exist, add to existing computation.py
  - Create new files only if starting a new domain

Step 3: Implement bottom-up
  - Model → Repository → Service → Schema → API
  - Test each layer as you create it
```

---

## Key Directories Explained

### ✅ Implemented Directories

These directories currently exist in the codebase with working implementations:

#### `/src/config/` ✅
**Purpose**: Configuration management layer using Pydantic Settings and YAML loaders

**Files**:
- `settings.py` - Application settings from environment variables (database, Redis, JWT, API)
- `models.py` - Configuration data models (ChainConfig, ProviderConfig, ProviderMap)
- `chains.py` - Chain registry loader from chains.yaml
- `providers.py` - Provider registry loader from providers.yaml

**Current State**: Fully implemented with comprehensive test coverage (97%)

#### `/src/db/` ✅
**Purpose**: Database session management and connection handling

**Files**:
- `session.py` - Async SQLAlchemy engine with connection pooling (pool_size=10, max_overflow=20)
- `__init__.py` - Exports engine, async_session_factory, Base, get_db, check_db_connection

**Features**:
- Provides `get_db()` dependency for FastAPI routes
- Implements health check and connection validation
- Connection pooling with automatic recycling and pre-ping

**Current State**: Fully implemented with ORM models integrated

#### `/src/core/models/` ✅
**Purpose**: SQLAlchemy ORM models representing database tables across all data layers

**Files**:
- `base.py` - Base model with common timestamp fields (created_at, updated_at)
- `chains.py` - Chain registry and configuration models:
  - Chain - Blockchain network definitions (chain_id, name, period_type, native_unit, finality_lag)
  - Provider - External data provider configurations (provider_name, provider_type, base_url, rate_limit)
  - ChainProviderMapping - Chain-to-provider relationships with role-based priorities
  - CanonicalPeriod - Period definitions with finalization tracking
  - CanonicalValidatorIdentity - Chain-specific validator identities (Solana/Ethereum support)
- `staging.py` - Staging layer models for data ingestion:
  - IngestionRun - Job execution tracking with status, timestamps, error handling (run_id, chain_id, status, records_fetched/staged)
  - StagingPayload - Raw provider data storage with JSONB payload and full traceability (payload_id, run_id, validator_key, raw_payload, response_hash)
  - IngestionStatus - Enum (PENDING, RUNNING, SUCCESS, FAILED, PARTIAL)
  - DataType - Enum (FEES, MEV, REWARDS, META)
- `canonical.py` - Canonical layer models for normalized validator data:
  - CanonicalValidatorFees - Normalized execution fees per validator/period with NUMERIC(38,18) precision (fee_id, chain_id, period_id, validator_key, total_fees_native, fee_count, source traceability)
  - CanonicalValidatorMEV - Normalized MEV tips per validator/period with full traceability (mev_id, total_mev_native, tip_count, source attribution)
  - CanonicalStakeRewards - Normalized staking rewards supporting both aggregated and per-staker detail (reward_id, staker_address nullable, rewards_native, commission_native)
  - CanonicalValidatorMeta - Validator metadata per period (meta_id, commission_rate_bps 0-10000, is_mev_enabled, total/active stake, delegator_count, uptime_percentage 0-100)

**Features**:
- All check constraints, indexes, and foreign keys from database schema
- Bidirectional relationships between models across layers
- Cascade delete behavior for referential integrity (CASCADE for chain/period, RESTRICT for provider/staging)
- GIN index on JSONB payload for efficient querying (staging layer)
- NUMERIC(38,18) for blockchain-native amounts (lamports, wei) in canonical layer
- Unique constraints preventing duplicate canonical data per (chain_id, period_id, validator_key)
- TYPE_CHECKING imports to avoid circular dependencies
- Support for both Solana (vote_pubkey, node_pubkey) and Ethereum (fee_recipient) validators
- Full audit trail with source_provider_id and source_payload_id in canonical models

**Testing**: 42 comprehensive unit tests (20 chain registry + 11 staging layer + 11 canonical layer) with 100% code coverage for canonical.py, covering model creation, NUMERIC precision, constraints, relationships, and unique constraint enforcement

**Current State**: Chain registry, staging layer, and canonical layer implemented. Computation and user models pending.

---

### 📋 Planned Directories

These directories represent the target architecture. Create them as needed for your tasks:

#### `/src/core/schemas/` 📋
**Purpose**: Pydantic models for API request/response validation (DTOs)

**Organization Pattern**: Mirror API endpoint structure
- Example: `validators.py` contains DTOs for `/validators` endpoints
- Example: `commissions.py` contains DTOs for commission-related endpoints

**Why Separate from Models**: Clean API boundaries, independent of database schema evolution

**When to Create**: When implementing API endpoints

#### `/src/core/services/` 📋
**Purpose**: Business logic orchestration layer

**Organization Pattern**: One service per business domain
- Example: `ingestion.py` - Orchestrates data fetching from providers
- Example: `commission_engine.py` - Computes commissions from P&L
- Example: `validator_pnl.py` - Aggregates canonical data into validator P&L

**Layer Rules**: Services coordinate between repositories, adapters, and domain logic. No direct database access (use repositories).

**When to Create**: When implementing business logic features

#### `/src/core/repositories/` 📋
**Purpose**: Database access layer with query abstraction

**Organization Pattern**: Mirror model files
- Example: `chains.py` repository provides access to Chain, Provider, Period models
- `base.py` provides shared repository functionality (scoping, pagination)

**Features**: Enforce row-level scoping for RBAC, provide consistent query interface

**When to Create**: When models need database access from services

#### `/src/adapters/` 📋
**Purpose**: External data provider integrations

**Organization Pattern**: Chain-specific subdirectories
- `base.py` defines common adapter interface
- `solana/` contains Solana-specific adapters (SolanaBeach, Jito, RPC, Stakewiz)
- `ethereum/` contains Ethereum-specific adapters (M1 milestone)

**Design**: Adapter pattern for provider swappability without downstream changes

**When to Create**: When implementing data ingestion from external providers

#### `/src/api/` 📋
**Purpose**: FastAPI routes, middleware, and API infrastructure

**Structure**:
- `deps.py` - Dependency injection (database sessions, current user, etc.)
- `middleware/` - Authentication, RBAC, logging, correlation ID, error handling
- `v1/` - API version 1 endpoint handlers

**Organization Pattern**: One file per resource type (chains.py, validators.py, partners.py)

**When to Create**: When implementing REST API endpoints

#### `/src/jobs/` 📋
**Purpose**: Background job definitions using Prefect/RQ

**Examples**:
- `ingestion.py` - Scheduled data ingestion workflows
- `normalization.py` - Data transformation jobs
- `computation.py` - P&L and commission calculation jobs

**When to Create**: When implementing background tasks and scheduled operations

---

## Environment Variables

**Required** (see `.env.example` for template):

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/aurora
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Authentication
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=43200  # 30 days

# External Providers
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
SOLANABEACH_API_KEY=your-key
JITO_API_KEY=your-key
STAKEWIZ_API_KEY=your-key

ETH_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/your-key
BEACON_API_URL=https://beaconcha.in/api/v1

# Application
ENVIRONMENT=development  # development, staging, production
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Job Scheduler
PREFECT_API_URL=http://localhost:4200
REDIS_URL=redis://localhost:6379/0
```

---

## Development Commands

**Setup**:
```bash
make setup          # Install dependencies with Poetry
make migrate        # Run database migrations
make seed           # Seed development data
```

**Development**:
```bash
make dev            # Run development server with hot reload
make test           # Run test suite with coverage
make lint           # Run linters (black, ruff, mypy)
make format         # Format code with black
```

**Database**:
```bash
make migration MSG="description"  # Create new Alembic migration
make migrate        # Apply pending migrations
make migrate-down   # Rollback last migration
```

**Docker**:
```bash
make docker-build   # Build Docker image
make docker-up      # Start all services (app, db, redis)
make docker-down    # Stop all services
make docker-logs    # Tail service logs
```

---

## Key Design Patterns

### Adapter Pattern
External data providers abstracted behind common interface in `/src/adapters/base.py`. Providers swappable via config without code changes.

### Repository Pattern
All database access through repositories in `/src/core/repositories/`. Repositories enforce RBAC scoping and provide consistent query interface.

### Service Layer
Business logic in `/src/core/services/` orchestrates between repositories, adapters, and domain logic. Services are stateless and testable.

### Dependency Injection
FastAPI's dependency system injects database sessions, current user, and services into route handlers via `/src/api/deps.py`.

### Strategy Pattern
Commission attribution methods (CLIENT_REVENUE, STAKE_WEIGHT, FIXED_SHARE) implemented as strategies in commission engine.

### Event Sourcing
Audit log captures immutable before/after snapshots of all sensitive operations for full traceability.

---

## Testing Strategy

### Unit Tests (`tests/unit/`)
- Test individual functions/methods in isolation
- Mock external dependencies (database, HTTP clients)
- Fast execution (<1s total)

### Integration Tests (`tests/integration/`)
- Test API endpoints end-to-end
- Use test database (PostgreSQL in Docker)
- Test RBAC enforcement, validation, error handling

### Fixtures (`tests/fixtures/`)
- Shared test data (chains, providers, staging payloads)
- Database fixtures via pytest fixtures in `conftest.py`

**Coverage Target**: >80% for MVP

---

## Deployment Strategy

### On-Premise (MVP)
- **Docker Compose**: ✅ **Implemented** - PostgreSQL 15 + Redis 7 services configured with health checks
  - PostgreSQL container with persistent volume and connection validation
  - Redis container for caching and session storage
  - Custom bridge network for service communication
  - See `docker-compose.yml` and `.env.example` for configuration
- **Systemd**: Alternative native deployment on Linux servers (future)
- **Nginx**: Reverse proxy with TLS termination, static file serving (future)

### CI/CD Pipeline (Future)
1. **Build**: Docker image build, dependency caching
2. **Test**: Run unit + integration tests, coverage check
3. **Lint**: Black, Ruff, mypy validation
4. **Deploy**: Push to registry, deploy to staging/production
5. **Verify**: Health check, smoke tests

---

**Document Version**: 1.5
**Last Updated**: 2025-10-27
**Status**: Active
**Recent Changes (v1.5 - 2025-10-27)**:
- Added canonical layer ORM models (`src/core/models/canonical.py`) with CanonicalValidatorFees, CanonicalValidatorMEV, CanonicalStakeRewards, CanonicalValidatorMeta
- Updated file tree with canonical.py and test_models_canonical.py
- Expanded test suite to 100 tests (42 ORM model tests, 79% coverage)
- Updated Current Implementation Status with completed Issue #8
- Documented NUMERIC(38,18) precision for blockchain-native amounts, unique constraints, and source traceability patterns
- Documented bidirectional relationships between canonical, staging, and chain registry models

**Previous Changes (v1.4 - 2025-10-26)**:
- Added staging layer ORM models (`src/core/models/staging.py`) with IngestionRun, StagingPayload, and enums
- Updated file tree with staging.py and test_models_staging.py
- Expanded test suite to 89 tests (31 ORM model tests, 75% coverage)
- Updated Current Implementation Status with completed Issue #7
- Documented bidirectional relationships between staging and chain registry models
