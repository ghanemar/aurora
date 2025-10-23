# Aurora Project Structure

**AI agents MUST read this file to understand the complete technology stack and file organization before making any changes.**

## Technology Stack

### Backend Technologies
- **Python 3.11+** with **Poetry** - Dependency management and packaging
- **FastAPI 0.115.0+** - Async web framework with type hints and automatic API documentation
- **Uvicorn 0.32.0+** - ASGI server for production deployment
- **Pydantic 2.x** - Data validation and settings management with type annotations

### Database & ORM
- **PostgreSQL 15+** - Primary relational database (system of record)
- **SQLAlchemy 2.0+** - Async ORM with type hints
- **Alembic** - Database migration management
- **psycopg3** - PostgreSQL adapter with async support

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

## Complete Project Structure

```
aurora/
├── README.md                           # Project overview and setup instructions
├── CLAUDE.md                           # Master AI context file
├── MCP-ASSISTANT-RULES.md              # MCP server AI assistant context
├── pyproject.toml                      # Poetry package configuration
├── poetry.lock                         # Locked dependencies
├── .gitignore                          # Git ignore patterns
├── .env.example                        # Environment variable template
├── Makefile                            # Common development tasks
├── docker-compose.yml                  # Docker services orchestration
├── Dockerfile                          # Application container image
├── alembic.ini                         # Alembic migration configuration
├── chains.yaml                         # Chain registry configuration
├── providers.yaml                      # Data provider configuration
├── rbac_policy.md                      # RBAC policy matrix
│
├── src/                                # Source code
│   ├── __init__.py
│   ├── main.py                         # FastAPI application entry point
│   │
│   ├── config/                         # Configuration management
│   │   ├── __init__.py
│   │   ├── settings.py                 # Pydantic settings from environment
│   │   ├── chains.py                   # Chain configuration loader
│   │   └── providers.py                # Provider configuration loader
│   │
│   ├── core/                           # Core business logic
│   │   ├── __init__.py
│   │   ├── models/                     # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── chains.py               # Chain, provider, period models
│   │   │   ├── staging.py              # Ingestion run, staging payload models
│   │   │   ├── canonical.py            # Canonical data models (fees, MEV, rewards, meta)
│   │   │   ├── computation.py          # Validator P&L, commission line models
│   │   │   ├── agreements.py           # Partner, agreement, rule models
│   │   │   └── users.py                # User, audit log models
│   │   │
│   │   ├── schemas/                    # Pydantic request/response schemas
│   │   │   ├── __init__.py
│   │   │   ├── chains.py               # Chain DTOs
│   │   │   ├── validators.py           # Validator P&L DTOs
│   │   │   ├── commissions.py          # Commission line DTOs
│   │   │   ├── agreements.py           # Agreement DTOs
│   │   │   ├── auth.py                 # Authentication DTOs
│   │   │   └── common.py               # Shared DTOs (pagination, error responses)
│   │   │
│   │   ├── services/                   # Business logic services
│   │   │   ├── __init__.py
│   │   │   ├── ingestion.py            # Ingestion orchestration service
│   │   │   ├── normalization.py        # Normalization and reconciliation service
│   │   │   ├── commission_engine.py    # Commission computation service
│   │   │   ├── agreement_service.py    # Agreement management service
│   │   │   └── validator_pnl.py        # Validator P&L computation service
│   │   │
│   │   ├── repositories/               # Database access layer
│   │   │   ├── __init__.py
│   │   │   ├── base.py                 # Base repository with scoping mixin
│   │   │   ├── chains.py               # Chain repository
│   │   │   ├── staging.py              # Staging repository
│   │   │   ├── canonical.py            # Canonical data repository
│   │   │   ├── commissions.py          # Commission repository
│   │   │   ├── agreements.py           # Agreement repository
│   │   │   └── users.py                # User repository
│   │   │
│   │   └── utils/                      # Core utilities
│   │       ├── __init__.py
│   │       ├── logging.py              # Structured logging setup
│   │       ├── validation.py           # Common validation logic
│   │       ├── decimals.py             # Decimal/native unit conversions
│   │       └── hashing.py              # Hash generation utilities
│   │
│   ├── adapters/                       # External data provider adapters
│   │   ├── __init__.py
│   │   ├── base.py                     # Base adapter interface
│   │   ├── solana/                     # Solana-specific adapters
│   │   │   ├── __init__.py
│   │   │   ├── solana_beach.py         # SolanaBeach fees adapter
│   │   │   ├── jito.py                 # Jito MEV adapter
│   │   │   ├── rpc.py                  # Solana RPC rewards adapter
│   │   │   └── stakewiz.py             # Stakewiz metadata adapter
│   │   └── ethereum/                   # Ethereum-specific adapters (M1)
│   │       ├── __init__.py
│   │       ├── block_fees.py           # Execution fee adapter
│   │       ├── mev_relay.py            # MEV relay adapter
│   │       ├── consensus_api.py        # Consensus rewards adapter
│   │       └── beacon_api.py           # Beacon metadata adapter
│   │
│   ├── api/                            # FastAPI routes and middleware
│   │   ├── __init__.py
│   │   ├── deps.py                     # Dependency injection (DB, auth, etc.)
│   │   ├── middleware/                 # API middleware
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                 # JWT authentication middleware
│   │   │   ├── rbac.py                 # Role-based authorization
│   │   │   ├── logging.py              # Request/response logging
│   │   │   ├── correlation_id.py       # Correlation ID injection
│   │   │   └── error_handler.py        # Global error handling
│   │   │
│   │   └── v1/                         # API v1 endpoints
│   │       ├── __init__.py
│   │       ├── auth.py                 # POST /auth/login, /auth/refresh
│   │       ├── chains.py               # GET /chains, /chains/{id}/periods
│   │       ├── validators.py           # GET /chains/{chain}/validators/{key}/pnl
│   │       ├── partners.py             # GET /chains/{chain}/partners/{id}/commissions
│   │       ├── agreements.py           # CRUD /agreements
│   │       ├── overrides.py            # POST /overrides
│   │       └── operations.py           # POST /recompute, GET /ingestion/health
│   │
│   ├── jobs/                           # Background job definitions
│   │   ├── __init__.py
│   │   ├── ingestion.py                # Ingestion job workflows
│   │   ├── normalization.py            # Normalization job workflows
│   │   ├── computation.py              # Computation job workflows
│   │   └── scheduler.py                # Job scheduling configuration
│   │
│   └── db/                             # Database management
│       ├── __init__.py
│       ├── session.py                  # Async database session factory
│       └── migrations/                 # Alembic migrations
│           ├── env.py                  # Alembic environment config
│           ├── script.py.mako          # Migration template
│           └── versions/               # Migration version files
│               ├── 001_initial_schema.py
│               ├── 002_add_ethereum.py
│               └── 003_add_tier_config.py
│
├── tests/                              # Test suite
│   ├── __init__.py
│   ├── conftest.py                     # Pytest fixtures and configuration
│   ├── unit/                           # Unit tests
│   │   ├── test_services.py            # Service unit tests
│   │   ├── test_repositories.py        # Repository unit tests
│   │   ├── test_adapters.py            # Adapter unit tests
│   │   └── test_utils.py               # Utility function tests
│   ├── integration/                    # Integration tests
│   │   ├── test_api_chains.py          # Chain API tests
│   │   ├── test_api_validators.py      # Validator API tests
│   │   ├── test_api_partners.py        # Partner API tests
│   │   ├── test_api_agreements.py      # Agreement API tests
│   │   └── test_commission_engine.py   # End-to-end commission tests
│   └── fixtures/                       # Test data fixtures
│       ├── chains.json                 # Chain test data
│       ├── providers.json              # Provider test data
│       └── staging_payloads.json       # Sample staging payloads
│
├── scripts/                            # Automation scripts
│   ├── setup.sh                        # Environment setup script
│   ├── seed_dev_data.py                # Seed development database
│   ├── backfill.py                     # Historical data backfill
│   ├── validate_agreements.py          # Agreement rule validation
│   └── maintenance/                    # Maintenance scripts
│       ├── check_data_integrity.py     # Data integrity checker
│       └── export_statements.py        # Bulk statement export
│
├── docs/                               # Documentation
│   ├── README.md                       # Documentation index
│   ├── system-architecture.md          # Complete system architecture
│   ├── database-schema.md              # Database schema documentation
│   ├── api-specification.md            # API specification with examples
│   ├── rbac_policy.md                  # RBAC policy matrix
│   │
│   ├── ai-context/                     # AI-specific documentation
│   │   ├── project-structure.md        # This file
│   │   ├── docs-overview.md            # Documentation architecture guide
│   │   ├── system-integration.md       # Cross-component integration patterns
│   │   ├── deployment-infrastructure.md # Infrastructure and deployment
│   │   └── HANDOFF.md                  # Task management and session continuity
│   │
│   ├── specs/                          # Feature specifications
│   │   └── example-feature-specification.md
│   │
│   ├── open-issues/                    # Issue tracking
│   │   └── example-api-performance-issue.md
│   │
│   └── runbooks/                       # Operational runbooks
│       ├── deployment.md               # Deployment procedures
│       ├── backup-restore.md           # Backup and restore procedures
│       └── troubleshooting.md          # Common troubleshooting guides
│
├── frontend/                           # Frontend application (future)
│   ├── package.json                    # NPM dependencies
│   ├── tsconfig.json                   # TypeScript configuration
│   ├── vite.config.ts                  # Vite build configuration
│   ├── src/                            # Frontend source code
│   │   ├── main.tsx                    # Application entry point
│   │   ├── App.tsx                     # Root component
│   │   ├── components/                 # UI components
│   │   │   ├── admin/                  # Admin portal components
│   │   │   └── partner/                # Partner portal components
│   │   ├── pages/                      # Page components
│   │   │   ├── dashboard.tsx           # Dashboard page
│   │   │   ├── validators.tsx          # Validator P&L page
│   │   │   ├── partners.tsx            # Partner commissions page
│   │   │   └── agreements.tsx          # Agreement management page
│   │   ├── api/                        # API client
│   │   │   ├── client.ts               # HTTP client setup
│   │   │   └── endpoints/              # API endpoint definitions
│   │   └── utils/                      # Frontend utilities
│   └── tests/                          # Frontend tests
│
└── nginx/                              # Nginx configuration
    ├── nginx.conf                      # Main Nginx config
    ├── ssl/                            # TLS certificates
    └── sites-available/                # Site configurations
        └── aurora.conf                 # Aurora site config
```

---

## Key Directories Explained

### `/src/core/models/`
SQLAlchemy ORM models representing database tables. Each file groups related entities:
- `chains.py` - Chain registry and provider mappings
- `staging.py` - Raw ingestion data
- `canonical.py` - Normalized data layer
- `computation.py` - Computed P&L and commissions
- `agreements.py` - Partner agreements and rules
- `users.py` - User management and audit logs

### `/src/core/schemas/`
Pydantic models for API request/response validation. DTOs (Data Transfer Objects) separate from database models for clean API boundaries.

### `/src/core/services/`
Business logic layer. Services orchestrate between repositories, adapters, and external systems. Each service has a single responsibility:
- `ingestion.py` - Orchestrates data fetching from providers
- `normalization.py` - Transforms staging → canonical
- `commission_engine.py` - Computes commissions from P&L
- `validator_pnl.py` - Aggregates canonical → validator P&L

### `/src/core/repositories/`
Data access layer. Repositories abstract database queries and enforce row-level scoping for RBAC. All database access goes through repositories (never direct SQL in services).

### `/src/adapters/`
Provider-specific implementations of data fetching. Each adapter implements common interface from `base.py`. Swapping providers requires only adapter changes, no downstream impact.

### `/src/api/v1/`
FastAPI route handlers. Each file handles one resource type (chains, validators, partners, etc.). All routes enforce RBAC via middleware before reaching handler.

### `/src/jobs/`
Background job definitions using Prefect/RQ. Jobs handle async operations like ingestion, normalization, and recomputation.

### `/docs/`
All project documentation including architecture, database schema, API specs, and operational runbooks.

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
- **Docker Compose**: Multi-container deployment (app, db, redis, nginx)
- **Systemd**: Alternative native deployment on Linux servers
- **Nginx**: Reverse proxy with TLS termination, static file serving

### CI/CD Pipeline (Future)
1. **Build**: Docker image build, dependency caching
2. **Test**: Run unit + integration tests, coverage check
3. **Lint**: Black, Ruff, mypy validation
4. **Deploy**: Push to registry, deploy to staging/production
5. **Verify**: Health check, smoke tests

---

**Document Version**: 1.0
**Last Updated**: 2025-10-22
**Status**: Draft
