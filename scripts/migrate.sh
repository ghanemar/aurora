#!/usr/bin/env bash
# Migration management script for Aurora database
#
# Usage:
#   ./scripts/migrate.sh upgrade              # Upgrade to latest migration
#   ./scripts/migrate.sh downgrade [revision] # Downgrade to specific revision or -1
#   ./scripts/migrate.sh current              # Show current migration version
#   ./scripts/migrate.sh history              # Show migration history
#   ./scripts/migrate.sh create "message"     # Create new migration with autogenerate
#   ./scripts/migrate.sh reset                # Reset database (downgrade all + upgrade all)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
error() {
    echo -e "${RED}ERROR: $1${NC}" >&2
    exit 1
}

success() {
    echo -e "${GREEN}$1${NC}"
}

info() {
    echo -e "${YELLOW}$1${NC}"
}

# Check if poetry is available
command -v poetry >/dev/null 2>&1 || error "Poetry is not installed"

# Check if .env file exists (optional - can also use environment variables)
if [ -f .env ]; then
    info "Using .env file for configuration"
elif [ -z "${DATABASE_URL:-}" ]; then
    error ".env file not found and DATABASE_URL environment variable not set"
fi

# Main command handling
case "${1:-}" in
    upgrade)
        info "Upgrading database to latest migration..."
        poetry run alembic upgrade head
        success "Database upgraded successfully!"
        poetry run alembic current
        ;;

    downgrade)
        REVISION="${2:--1}"
        info "Downgrading database to revision: $REVISION"
        poetry run alembic downgrade "$REVISION"
        success "Database downgraded successfully!"
        poetry run alembic current
        ;;

    current)
        info "Current migration version:"
        poetry run alembic current
        ;;

    history)
        info "Migration history:"
        poetry run alembic history --verbose
        ;;

    create)
        [ -z "${2:-}" ] && error "Migration message required. Usage: $0 create \"message\""
        info "Creating new migration: $2"
        poetry run alembic revision --autogenerate -m "$2"
        success "Migration created successfully!"
        ;;

    reset)
        info "Resetting database (downgrade all + upgrade all)..."
        poetry run alembic downgrade base
        success "Database downgraded to base!"
        poetry run alembic upgrade head
        success "Database upgraded to head!"
        poetry run alembic current
        ;;

    *)
        cat <<EOF
Aurora Database Migration Management

Usage:
  $0 upgrade              Upgrade to latest migration
  $0 downgrade [revision] Downgrade to specific revision or previous (-1)
  $0 current              Show current migration version
  $0 history              Show migration history
  $0 create "message"     Create new migration with autogenerate
  $0 reset                Reset database (downgrade all + upgrade all)

Examples:
  $0 upgrade                      # Apply all pending migrations
  $0 downgrade -1                 # Rollback one migration
  $0 downgrade cec3a80e61a4       # Rollback to specific revision
  $0 create "Add user table"      # Create new migration
  $0 reset                        # Complete database reset

Environment:
  Requires .env file with DATABASE_URL configured
  Database: \${DATABASE_URL}

EOF
        exit 1
        ;;
esac
