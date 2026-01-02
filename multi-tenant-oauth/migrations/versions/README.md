# Database Migration Versions

This directory contains Alembic migration files that track database schema changes over time.

## How to Use

### Create a New Migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "description of changes"

# Create empty migration (for data migrations or manual schema changes)
alembic revision -m "description of changes"
```

### Apply Migrations

```bash
# Upgrade to latest version
alembic upgrade head

# Upgrade one version
alembic upgrade +1

# Downgrade one version
alembic downgrade -1

# Show current version
alembic current

# Show migration history
alembic history
```

## Migration Files

Migration files will be created here with the naming pattern:
`YYYYMMDD_HHMM_<revision>_<description>.py`

Each migration file contains:
- `upgrade()` - SQL commands to apply the migration
- `downgrade()` - SQL commands to rollback the migration
