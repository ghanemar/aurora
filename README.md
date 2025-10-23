# Aurora - Multi-Chain Validator P&L & Partner Commissions

Deterministic, auditable computation of validator revenue and partner commissions across multiple blockchain networks with provider-agnostic architecture.

## Overview

Aurora provides a comprehensive system for tracking validator performance and calculating partner commissions across multiple blockchain networks. The platform emphasizes deterministic calculations, full audit trails, and provider swappability.

**Current Phase:** Initial design and architecture planning
**MVP Target:** Solana support
**Milestone 1:** Add Ethereum support

## Key Architecture

- **Chain-agnostic ingestion** → normalization → canonical data layer
- **Commission engine** with deterministic calculations
- **RBAC-enforced API** for secure access control
- **Provider swappability** for flexibility and resilience
- **Full audit trail** for compliance and verification

## Prerequisites

- Python 3.11 or higher
- [Poetry](https://python-poetry.org/) for dependency management
- PostgreSQL 14+ (for production use)

## Quick Start

### 1. Install Poetry

If you haven't installed Poetry yet:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### 2. Clone and Setup

```bash
git clone <repository-url>
cd aurora
```

### 3. Install Dependencies

```bash
# Install all dependencies including dev dependencies
poetry install

# Activate the virtual environment
poetry shell
```

### 4. Verify Installation

```bash
# Check Python version
poetry run python --version

# Test FastAPI import
poetry run python -c "import fastapi; print('FastAPI:', fastapi.__version__)"
```

## Project Structure

```
aurora/
├── src/
│   └── aurora/          # Main application package
│       └── __init__.py
├── tests/               # Test suite
├── docs/                # Documentation
├── pyproject.toml       # Poetry configuration
├── .python-version      # Python version specification
└── README.md            # This file
```

## Development

### Running Tests

```bash
# Run all tests with coverage
poetry run pytest

# Run with verbose output
poetry run pytest -v

# Run specific test file
poetry run pytest tests/test_example.py
```

### Code Quality

```bash
# Format code with black
poetry run black src/ tests/

# Lint with ruff
poetry run ruff check src/ tests/

# Type check with mypy
poetry run mypy src/
```

### Running the API Server

```bash
# Development server with auto-reload
poetry run uvicorn aurora.main:app --reload

# Production server
poetry run uvicorn aurora.main:app --host 0.0.0.0 --port 8000
```

## Technology Stack

- **Framework:** FastAPI for high-performance async API
- **ORM:** SQLAlchemy 2.0 with async support
- **Database:** PostgreSQL with asyncpg driver
- **Migration:** Alembic for database schema management
- **Validation:** Pydantic v2 for data validation
- **Authentication:** python-jose with JWT tokens
- **Logging:** structlog for structured logging
- **Testing:** pytest with async support

## Environment Configuration

Create a `.env` file in the project root:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/aurora

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API
API_V1_PREFIX=/api/v1
DEBUG=true
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests and quality checks
4. Submit a pull request

### Code Standards

- Follow PEP 8 style guide
- Use type hints for all functions
- Write docstrings for public functions
- Maintain test coverage above 80%
- Run black, ruff, and mypy before committing

## License

Proprietary - All rights reserved

## Support

For questions or issues, please contact the development team.
