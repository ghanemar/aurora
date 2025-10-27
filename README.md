# Aurora - Multi-Chain Validator P&L & Partner Commissions

Deterministic, auditable computation of validator revenue and partner commissions across multiple blockchain networks with provider-agnostic architecture.

## Overview

Aurora provides a comprehensive system for tracking validator performance and calculating partner commissions across multiple blockchain networks. The platform emphasizes deterministic calculations, full audit trails, and provider swappability.

**Current Phase:** Complete data layer with working database migrations
**MVP Target:** Solana support with ingestion adapters (in progress)
**Milestone 1:** Add Ethereum support

## Key Features

- ✅ **Complete ORM Data Layer** - All models implemented (chains, staging, canonical, computation)
- ✅ **Database Migrations** - Alembic configured with async SQLAlchemy support
- ✅ **Chain-agnostic Design** - Provider-independent data model ready for multi-chain support
- ✅ **Commission Engine Schema** - Ready for deterministic commission calculations
- 🚧 **Data Ingestion** - Blockchain adapter development (next phase)
- 🚧 **RBAC API** - Secure access control implementation (planned)

## Architecture

```
┌─────────────────┐
│  Data Ingestion │  ← Blockchain provider adapters (Solana, Ethereum)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Staging Layer  │  ← Raw data storage with full traceability
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Canonical Layer │  ← Normalized, provider-independent data
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│Computation Layer│  ← Validator P&L and partner commission calculations
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   API Layer     │  ← RBAC-enforced REST API (planned)
└─────────────────┘
```

## Prerequisites

- Python 3.11 or higher
- [Poetry](https://python-poetry.org/) for dependency management
- Docker and Docker Compose
- PostgreSQL 15+ (via Docker or native)

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd aurora
```

### 2. Environment Configuration

Copy the example environment file and configure:

```bash
cp .env.example .env
# Edit .env with your configuration
```

Key environment variables:
```bash
# Database
DATABASE_URL=postgresql+asyncpg://aurora:aurora_dev@localhost:5432/aurora

# Security
SECRET_KEY=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256

# Application
APP_ENV=development
LOG_LEVEL=INFO
```

### 3. Start Infrastructure

```bash
# Start PostgreSQL and Redis via Docker Compose
docker-compose up -d

# Verify containers are running
docker ps
```

### 4. Install Dependencies

```bash
# Install all dependencies including dev dependencies
poetry install

# Activate the virtual environment
poetry shell
```

### 5. Run Database Migrations

```bash
# Apply all migrations to create database schema
./scripts/migrate.sh upgrade

# Verify current migration version
./scripts/migrate.sh current
```

### 6. Verify Installation

```bash
# Run test suite
poetry run pytest

# Check code quality
poetry run mypy src/
poetry run ruff check src/
poetry run black --check src/
```

Expected output: 122 tests passing with 84% coverage

## Database Management

### Migration Commands

```bash
# Show current migration version
./scripts/migrate.sh current

# Apply all pending migrations
./scripts/migrate.sh upgrade

# Rollback one migration
./scripts/migrate.sh downgrade -1

# View migration history
./scripts/migrate.sh history

# Create new migration after model changes
./scripts/migrate.sh create "Add new field to chains"

# Complete database reset (dev only!)
./scripts/migrate.sh reset
```

See [Migration Guide](docs/migration-guide.md) for detailed documentation.

### Database Schema

The database consists of 18 tables organized into layers:

**Configuration & Registry (5 tables)**
- `chains` - Blockchain network definitions
- `providers` - External data provider configurations
- `chain_provider_mappings` - Chain-to-provider relationships
- `canonical_periods` - Time period definitions per chain
- `canonical_validator_identities` - Validator identity mappings

**Staging Layer (2 tables)**
- `ingestion_runs` - Data ingestion job tracking
- `staging_payloads` - Raw provider data with full traceability

**Canonical Layer (4 tables)**
- `canonical_validator_fees` - Normalized validator fee data
- `canonical_validator_mev` - Normalized MEV revenue data
- `canonical_stake_rewards` - Normalized staking rewards
- `canonical_validator_meta` - Validator metadata

**Computation Layer (7 tables)**
- `validator_pnl` - Validator profit & loss calculations
- `partners` - Partner organization definitions
- `agreements` - Partnership agreement contracts
- `agreement_versions` - Agreement version history
- `agreement_rules` - Chain-specific agreement rules
- `partner_commission_lines` - Detailed commission line items
- `partner_commission_statements` - Commission summary statements

See [Database Schema](docs/database-schema.md) for complete specifications.

## Project Structure

```
aurora/
├── alembic/                    # Database migrations
│   ├── versions/               # Migration files
│   └── env.py                  # Alembic async configuration
├── config/                     # Configuration files
│   ├── chains.yaml             # Blockchain network configurations
│   └── providers.yaml          # Data provider configurations
├── docs/                       # Documentation
│   ├── ai-context/             # AI agent context files
│   ├── database-schema.md      # Complete schema specification
│   └── migration-guide.md      # Database migration guide
├── scripts/                    # Utility scripts
│   └── migrate.sh              # Migration management script
├── src/                        # Source code
│   ├── config/                 # Configuration loaders
│   ├── core/                   # Core functionality
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── security.py         # Security utilities
│   │   └── logging.py          # Structured logging
│   └── db/                     # Database utilities
│       └── session.py          # Async session factory
├── tests/                      # Test suite
│   ├── unit/                   # Unit tests
│   └── conftest.py             # Pytest fixtures
├── docker-compose.yml          # Infrastructure definition
├── pyproject.toml              # Poetry configuration
└── README.md                   # This file
```

## Development Workflow

### 1. Making Model Changes

Edit ORM models in `src/core/models/`:

```python
# Example: Adding a new field
class Chain(BaseModel):
    # ... existing fields ...

    rpc_endpoint: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="Primary RPC endpoint"
    )
```

### 2. Generate and Apply Migration

```bash
# Generate migration from model changes
./scripts/migrate.sh create "Add RPC endpoint to chains"

# Review generated migration file
cat alembic/versions/<new_revision>_*.py

# Apply migration
./scripts/migrate.sh upgrade

# Test rollback
./scripts/migrate.sh downgrade -1
./scripts/migrate.sh upgrade
```

### 3. Running Tests

```bash
# Run all tests with coverage
poetry run pytest

# Run with verbose output
poetry run pytest -v

# Run specific test file
poetry run pytest tests/unit/test_models_chains.py

# Run with coverage report
poetry run pytest --cov=src --cov-report=term-missing
```

### 4. Code Quality Checks

```bash
# Format code with black
poetry run black src/ tests/

# Lint with ruff
poetry run ruff check src/ tests/

# Fix auto-fixable issues
poetry run ruff check --fix src/ tests/

# Type check with mypy
poetry run mypy src/

# Run all quality gates
poetry run black src/ tests/ && \
poetry run ruff check src/ tests/ && \
poetry run mypy src/ && \
poetry run pytest
```

## Technology Stack

### Core Framework
- **FastAPI** - High-performance async web framework
- **SQLAlchemy 2.0** - Async ORM with type hints
- **Alembic** - Database migration management
- **Pydantic v2** - Data validation and settings

### Database & Caching
- **PostgreSQL 15** - Primary database with NUMERIC precision
- **asyncpg** - High-performance async PostgreSQL driver
- **Redis 7** - Caching and session storage

### Security & Authentication
- **python-jose** - JWT token generation and validation
- **passlib[bcrypt]** - Password hashing
- **structlog** - Structured logging with PII filtering

### Development Tools
- **pytest** - Testing framework with async support
- **pytest-asyncio** - Async test support
- **pytest-cov** - Coverage reporting
- **black** - Code formatting
- **ruff** - Fast Python linter
- **mypy** - Static type checking

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Poetry** - Dependency management

## Testing

### Test Organization

```
tests/
├── unit/                       # Unit tests
│   ├── test_models_chains.py
│   ├── test_models_staging.py
│   ├── test_models_canonical.py
│   └── test_models_computation.py
├── integration/                # Integration tests (planned)
└── conftest.py                 # Shared fixtures
```

### Test Coverage

Current coverage: **84%** (122 passing tests)
- ORM models: 100%
- Configuration loaders: 96-100%
- Database session: 44% (async utilities)
- Security/Logging: 0% (no sensitive logic yet)

### Running Specific Test Suites

```bash
# Run only model tests
poetry run pytest tests/unit/test_models_*.py

# Run with specific markers
poetry run pytest -m "not slow"

# Run with specific keyword
poetry run pytest -k "test_chain"
```

## Docker Infrastructure

### Services

```yaml
services:
  postgres:
    image: postgres:15-alpine
    ports: 5432:5432
    volumes: ./data/postgres

  redis:
    image: redis:7-alpine
    ports: 6379:6379
```

### Useful Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f postgres

# Stop all services
docker-compose down

# Reset database (removes all data!)
docker-compose down -v
docker-compose up -d
./scripts/migrate.sh upgrade
```

## Development Status

### Completed (Issues #1-10)
- ✅ Project foundation and infrastructure setup
- ✅ Chain registry ORM models
- ✅ Staging layer ORM models
- ✅ Canonical layer ORM models
- ✅ Computation layer ORM models
- ✅ Alembic migrations with async support

### In Progress (Issues #11-14)
- 🚧 Data ingestion adapters (Solana, Ethereum)
- 🚧 Provider API client abstraction
- 🚧 Ingestion orchestration

### Planned (Issues #15+)
- 📋 Commission calculation service
- 📋 Authentication & RBAC
- 📋 REST API implementation
- 📋 API documentation (OpenAPI/Swagger)

## Contributing

### Code Standards

- **Type Hints** - Required for all functions
- **Docstrings** - Google-style for public functions
- **Test Coverage** - Maintain >80% overall coverage
- **Quality Gates** - All must pass: mypy, ruff, black, pytest

### Commit Convention

Commits should follow conventional commit format:
```
feat: Add new feature
fix: Bug fix
docs: Documentation changes
test: Test additions or changes
refactor: Code refactoring
chore: Maintenance tasks
```

All commits are signed by "AG and his AI Crew"

### Pull Request Process

1. Create feature branch from `main`
2. Make changes with tests
3. Run quality gates (all must pass)
4. Update documentation as needed
5. Submit PR with clear description

## Documentation

- **[Project Structure](docs/ai-context/project-structure.md)** - Complete architecture overview
- **[Database Schema](docs/database-schema.md)** - Full schema specification
- **[Migration Guide](docs/migration-guide.md)** - Database migration workflows
- **[API Specification](docs/api-specification.md)** - API design (planned)
- **[Development Workflow](docs/github-issues-plan.md)** - GitHub issues roadmap

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker ps | grep aurora-postgres

# View PostgreSQL logs
docker logs aurora-postgres

# Test connection
docker exec aurora-postgres psql -U aurora -d aurora -c "SELECT 1"
```

### Migration Issues

```bash
# Check current migration state
./scripts/migrate.sh current

# View migration history
./scripts/migrate.sh history

# Reset database (dev only - destructive!)
./scripts/migrate.sh reset
```

### Test Failures

```bash
# Run tests with verbose output
poetry run pytest -vv

# Run single test for debugging
poetry run pytest tests/unit/test_models_chains.py::test_create_chain -vv

# Check test database
docker exec aurora-postgres psql -U aurora -d aurora -c "\dt"
```

## License

Proprietary - All rights reserved

## Support

For questions or issues:
- Check documentation in `docs/`
- Review GitHub issues for known problems
- Contact the development team

---

**Status**: Active development - Data layer complete, ingestion adapters in progress
