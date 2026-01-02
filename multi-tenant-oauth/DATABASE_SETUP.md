# Database Setup Guide

Complete guide to set up PostgreSQL database for multi-tenant OAuth2 system.

---

## Prerequisites

- macOS, Linux, or Windows
- Terminal/Command Line access
- Administrator privileges

---

## Option 1: macOS Setup (Recommended for Mac Users)

### Step 1: Install PostgreSQL via Homebrew

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install PostgreSQL
brew install postgresql@14

# Start PostgreSQL service
brew services start postgresql@14

# Verify installation
psql --version
# Should output: psql (PostgreSQL) 14.x
```

### Step 2: Create Database

```bash
# Create the database
createdb social_automation_multi_tenant

# Verify database was created
psql -l | grep social_automation
```

### Step 3: Load Database Schema

```bash
# Navigate to the multi-tenant-oauth directory
cd /Users/asifrao/Library/CloudStorage/Dropbox/ABCD/Innowi/DataScience-AI-MIT/social-automation/multi-tenant-oauth

# Load the schema
psql social_automation_multi_tenant < database_schema.sql

# Verify tables were created
psql social_automation_multi_tenant -c "\dt"
```

---

## Option 2: Linux (Ubuntu/Debian) Setup

### Step 1: Install PostgreSQL

```bash
# Update package list
sudo apt update

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Verify installation
psql --version
```

### Step 2: Create Database and User

```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL prompt, run:
CREATE DATABASE social_automation_multi_tenant;
CREATE USER your_username WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE social_automation_multi_tenant TO your_username;
\q
```

### Step 3: Load Database Schema

```bash
# Load the schema
psql social_automation_multi_tenant < database_schema.sql
```

---

## Option 3: Windows Setup

### Step 1: Install PostgreSQL

1. Download installer from: [postgresql.org/download/windows](https://www.postgresql.org/download/windows/)
2. Run the installer
3. During installation:
   - Remember the password you set for `postgres` user
   - Default port: 5432 (keep default)
   - Install pgAdmin 4 (recommended)

### Step 2: Create Database

Using Command Line:
```cmd
# Open Command Prompt or PowerShell

# Create database
createdb -U postgres social_automation_multi_tenant

# Enter password when prompted
```

Or using pgAdmin 4:
1. Open pgAdmin 4
2. Right-click "Databases" → Create → Database
3. Name: `social_automation_multi_tenant`
4. Click "Save"

### Step 3: Load Database Schema

```cmd
# Navigate to multi-tenant-oauth directory
cd path\to\social-automation\multi-tenant-oauth

# Load schema
psql -U postgres social_automation_multi_tenant < database_schema.sql

# Enter password when prompted
```

---

## Option 4: Docker Setup (Cross-Platform)

### Step 1: Install Docker

Download and install Docker Desktop:
- macOS/Windows: [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
- Linux: [docs.docker.com/engine/install](https://docs.docker.com/engine/install/)

### Step 2: Run PostgreSQL Container

```bash
# Start PostgreSQL container
docker run --name social-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=social_automation_multi_tenant \
  -p 5432:5432 \
  -d postgres:14

# Verify container is running
docker ps
```

### Step 3: Load Database Schema

```bash
# Copy schema file into container
docker cp database_schema.sql social-postgres:/database_schema.sql

# Execute schema
docker exec social-postgres psql -U postgres -d social_automation_multi_tenant -f /database_schema.sql

# Verify tables
docker exec social-postgres psql -U postgres -d social_automation_multi_tenant -c "\dt"
```

---

## Verification

After setup, verify your database is working:

```bash
# Connect to database
psql social_automation_multi_tenant

# List all tables (should see 8 tables)
\dt

# Expected tables:
# - tenants
# - tenant_users
# - social_accounts
# - oauth_tokens
# - post_history
# - webhook_events
# - oauth_state
# - token_refresh_history

# Check tenant table structure
\d tenants

# Exit
\q
```

---

## Redis Setup (Required for Background Jobs)

### macOS (Homebrew):
```bash
brew install redis
brew services start redis

# Verify
redis-cli ping
# Should output: PONG
```

### Linux (Ubuntu/Debian):
```bash
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis

# Verify
redis-cli ping
```

### Windows:
```bash
# Download Redis from: https://github.com/microsoftarchive/redis/releases
# Or use Docker:
docker run --name social-redis -p 6379:6379 -d redis:7

# Verify
redis-cli ping
```

### Docker (Cross-Platform):
```bash
docker run --name social-redis -p 6379:6379 -d redis:7
docker exec social-redis redis-cli ping
```

---

## Database Configuration

After setup, note your database connection details:

```env
# Format: postgresql://username:password@host:port/database

# Local setup (macOS/Linux default):
DATABASE_URL=postgresql://localhost/social_automation_multi_tenant

# With custom user/password:
DATABASE_URL=postgresql://your_username:your_password@localhost:5432/social_automation_multi_tenant

# Docker setup:
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/social_automation_multi_tenant

# Redis URL:
REDIS_URL=redis://localhost:6379/0
```

---

## Troubleshooting

### "psql: command not found"
- **macOS**: Run `brew link postgresql@14 --force`
- **Linux**: Ensure PostgreSQL bin directory is in PATH
- **Windows**: Add PostgreSQL bin directory to System PATH

### "createdb: could not connect to database"
- Verify PostgreSQL is running: `brew services list` (macOS) or `sudo systemctl status postgresql` (Linux)
- Check if port 5432 is in use: `lsof -i :5432` (macOS/Linux)

### "FATAL: database does not exist"
- Create database first: `createdb social_automation_multi_tenant`

### "permission denied for schema public"
- Grant permissions: `psql -c "GRANT ALL ON SCHEMA public TO your_username"`

### Redis Connection Issues
- Verify Redis is running: `redis-cli ping`
- Check if port 6379 is in use: `lsof -i :6379`

---

## Database Management Commands

```bash
# Connect to database
psql social_automation_multi_tenant

# List databases
\l

# List tables
\dt

# Describe table
\d table_name

# View data
SELECT * FROM tenants;

# Drop database (CAREFUL - deletes all data!)
dropdb social_automation_multi_tenant

# Backup database
pg_dump social_automation_multi_tenant > backup.sql

# Restore database
psql social_automation_multi_tenant < backup.sql
```

---

## Next Steps

After completing database setup:
1. ✅ Copy DATABASE_URL to `.env` file
2. ✅ Copy REDIS_URL to `.env` file
3. ✅ Proceed to Environment Configuration
4. ✅ Test database connection

---

**Estimated Setup Time**: 10-15 minutes

For more information:
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
