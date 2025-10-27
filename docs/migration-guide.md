# Database Migration Guide - Aurora

This guide explains how to manage database schema migrations using Alembic for the Aurora project.

## Overview

Aurora uses Alembic for database schema migrations with async SQLAlchemy support. The migration system is configured to:
- Auto-generate migrations from ORM model changes
- Support both upgrade and downgrade operations
- Properly handle PostgreSQL ENUM types
- Format migrations with Black automatically
- Load configuration from environment variables

## Quick Start

### Prerequisites
- PostgreSQL database running (via Docker Compose)
- Environment variables configured (`.env` file or shell exports)
- Poetry installed and dependencies up to date

### Common Operations

```bash
# Apply all pending migrations
./scripts/migrate.sh upgrade

# Show current migration version
./scripts/migrate.sh current

# View migration history
./scripts/migrate.sh history

# Create a new migration after model changes
./scripts/migrate.sh create "Add user email verification"

# Rollback one migration
./scripts/migrate.sh downgrade -1

# Rollback to specific revision
./scripts/migrate.sh downgrade cec3a80e61a4

# Complete database reset (all down, then all up)
./scripts/migrate.sh reset
```

## Migration Workflow

### 1. Making Model Changes

When you modify ORM models in `src/core/models/`:

```python
# Example: Adding a new column to an existing model
class Chain(BaseModel):
    # ... existing columns ...

    # New column
    rpc_endpoint: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="Primary RPC endpoint URL"
    )
```

### 2. Generate Migration

```bash
./scripts/migrate.sh create "Add RPC endpoint to chains table"
```

This will:
- Auto-detect model changes
- Generate a new migration file in `alembic/versions/`
- Format the file with Black automatically
- Show the detected changes in the output

### 3. Review Migration

**IMPORTANT**: Always review generated migrations before applying them!

```bash
# Find the newest migration file
ls -lt alembic/versions/
# Review the upgrade() and downgrade() functions
cat alembic/versions/<new_revision>.py
```

Check for:
- Correct column definitions and types
- Proper handling of nullable/default values
- Index and constraint creation
- Data migration logic (if needed)
- Enum type handling for PostgreSQL

### 4. Apply Migration

```bash
# Test in development first
./scripts/migrate.sh upgrade

# Verify database state
./scripts/migrate.sh current
docker exec aurora-postgres psql -U aurora -d aurora -c "\d chains"
```

### 5. Test Downgrade

Always ensure your downgrade works:

```bash
# Rollback the migration
./scripts/migrate.sh downgrade -1

# Verify it rolled back cleanly
./scripts/migrate.sh current

# Re-apply for normal operation
./scripts/migrate.sh upgrade
```

## Advanced Topics

### Manual Migrations

For complex changes (data migrations, manual SQL), you may need to edit the generated migration:

```python
def upgrade() -> None:
    # Auto-generated schema change
    op.add_column('chains', sa.Column('status', sa.String(20)))

    # Manual data migration
    op.execute("""
        UPDATE chains
        SET status = CASE
            WHEN is_active THEN 'active'
            ELSE 'inactive'
        END
    """)

    # Remove old column after migration
    op.drop_column('chains', 'is_active')

def downgrade() -> None:
    # Reverse operations in reverse order
    op.add_column('chains', sa.Column('is_active', sa.Boolean()))
    op.execute("UPDATE chains SET is_active = (status = 'active')")
    op.drop_column('chains', 'status')
```

### PostgreSQL ENUM Types

**Important**: PostgreSQL ENUM types require special handling in downgrade functions.

Alembic doesn't automatically drop ENUM types, so we manually add cleanup:

```python
def downgrade() -> None:
    # ... auto-generated drop table commands ...

    # Manual enum cleanup (add at end)
    op.execute("DROP TYPE IF EXISTS myenumtype CASCADE")
```

Our initial migration (`cec3a80e61a4`) includes this pattern.

### Multi-Environment Migrations

For production deployments:

```bash
# 1. Test migration in dev first
DATABASE_URL=postgresql+asyncpg://aurora:aurora_dev@localhost:5432/aurora \
    ./scripts/migrate.sh upgrade

# 2. Create backup before production migration
pg_dump -h prod-host -U aurora aurora > backup_$(date +%Y%m%d).sql

# 3. Apply to production
DATABASE_URL=postgresql+asyncpg://aurora:password@prod-host:5432/aurora \
    ./scripts/migrate.sh upgrade

# 4. If issues occur, rollback
DATABASE_URL=postgresql+asyncpg://aurora:password@prod-host:5432/aurora \
    ./scripts/migrate.sh downgrade -1
```

### Branching and Merging

When working with multiple developers:

```bash
# If you get "multiple heads" error after git merge:
poetry run alembic heads  # Shows conflicting revisions
poetry run alembic merge <rev1> <rev2> -m "Merge migrations"

# This creates a merge revision that combines both branches
```

## Troubleshooting

### "Type already exists" Error

If you get duplicate type errors:

```bash
# Drop enum types manually
docker exec aurora-postgres psql -U aurora -d aurora \
    -c "DROP TYPE IF EXISTS myenumtype CASCADE"

# Then re-run migration
./scripts/migrate.sh upgrade
```

### "Multiple heads detected" Error

```bash
# List all head revisions
poetry run alembic heads

# Merge conflicting migrations
poetry run alembic merge <head1> <head2> -m "Merge branches"
```

### Migration Out of Sync

If alembic_version table doesn't match actual schema:

```bash
# Option 1: Stamp database to match actual state
poetry run alembic stamp head

# Option 2: Complete reset (DESTRUCTIVE - dev only!)
./scripts/migrate.sh reset
```

### Can't Connect to Database

```bash
# Check if database is running
docker ps | grep aurora-postgres

# Start database if not running
docker-compose up -d postgres

# Verify DATABASE_URL in .env
cat .env | grep DATABASE_URL
```

## Best Practices

1. **Always Review Generated Migrations** - Alembic can't detect everything correctly
2. **Test Downgrade Immediately** - Don't wait until you need it in production
3. **One Migration Per Logical Change** - Makes rollback easier and clearer history
4. **Add Comments** - Explain complex migrations or data transformations
5. **Backup Before Production** - Always have a rollback plan
6. **Version Control** - Commit migration files with related code changes
7. **Sequential Naming** - Let Alembic auto-generate revision IDs
8. **Test in Isolation** - Use fresh database for migration testing

## References

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [PostgreSQL ENUM Types](https://www.postgresql.org/docs/current/datatype-enum.html)
- Aurora Database Schema: `/docs/database-schema.md`
- ORM Models: `/src/core/models/`
