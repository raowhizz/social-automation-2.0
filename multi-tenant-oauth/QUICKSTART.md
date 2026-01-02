# Quick Start Guide - Multi-Tenant OAuth Social Media Automation

Get your multi-tenant OAuth system up and running in under 30 minutes!

---

## Prerequisites

- macOS, Linux, or Windows
- Python 3.10+
- Terminal/Command Line access

---

## Step 1: Install Dependencies (5 minutes)

### Install PostgreSQL

**macOS:**
```bash
brew install postgresql@14
brew services start postgresql@14
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Docker (All platforms):**
```bash
docker run --name social-postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=social_automation_multi_tenant -p 5432:5432 -d postgres:14
```

### Install Redis

**macOS:**
```bash
brew install redis
brew services start redis
```

**Linux:**
```bash
sudo apt install redis-server
sudo systemctl start redis
```

**Docker:**
```bash
docker run --name social-redis -p 6379:6379 -d redis:7
```

---

## Step 2: Set Up Database (3 minutes)

```bash
# Navigate to project directory
cd multi-tenant-oauth

# Create database
createdb social_automation_multi_tenant

# Load schema
psql social_automation_multi_tenant < database_schema.sql

# Verify tables created
psql social_automation_multi_tenant -c "\dt"
# You should see 8 tables
```

---

## Step 3: Configure Environment (5 minutes)

### Generate Security Keys

```bash
# Generate encryption keys
python generate_keys.py

# Output will show:
# SECRET_KEY=...
# ENCRYPTION_KEY=...
```

### Create .env File

```bash
# Copy example
cp .env.example .env

# Edit .env with your favorite editor
nano .env  # or vim, or code .env
```

### Minimum Required Configuration

Edit `.env` and set these values:

```env
# Database
DATABASE_URL=postgresql://localhost/social_automation_multi_tenant

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Security (paste from generate_keys.py output)
SECRET_KEY=your-generated-secret-key-here
ENCRYPTION_KEY=your-generated-encryption-key-here

# Facebook App (temporary - we'll set up in next step)
FACEBOOK_APP_ID=123456789  # Replace after creating app
FACEBOOK_APP_SECRET=abc123  # Replace after creating app
FACEBOOK_REDIRECT_URI=http://localhost:8000/oauth/facebook/callback
FACEBOOK_GRAPH_API_VERSION=v18.0
FACEBOOK_OAUTH_SCOPES=pages_show_list,pages_read_engagement,pages_manage_posts,instagram_basic,instagram_content_publish

# Application
DEBUG=True
LOG_LEVEL=INFO
```

---

## Step 4: Install Python Dependencies (2 minutes)

```bash
# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Step 5: Create Facebook App (10 minutes)

Follow the detailed guide in `FACEBOOK_APP_SETUP.md`, or quick steps:

1. Go to [developers.facebook.com](https://developers.facebook.com/)
2. Click "Create App" → "Business" type
3. Name: "Social Automation Multi-Tenant"
4. Add "Facebook Login" product
5. Configure redirect URI: `http://localhost:8000/oauth/facebook/callback`
6. Add "Instagram Graph API" product
7. Get App ID and App Secret from Settings → Basic
8. Update `.env` with your App ID and Secret

**Important**: App will be in Development Mode - only you can test OAuth flow initially.

---

## Step 6: Start the Application (2 minutes)

### Terminal 1: Start FastAPI Server

```bash
cd multi-tenant-oauth
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

**Test it**: Open http://localhost:8000 in browser
- You should see: `{"message": "Social Media Automation - Multi-Tenant OAuth API"}`

**View API Docs**: http://localhost:8000/docs

### Terminal 2: Start Celery Worker (Optional for now)

```bash
cd multi-tenant-oauth
celery -A app.tasks.celery_app worker -l info
```

### Terminal 3: Start Celery Beat (Optional for now)

```bash
cd multi-tenant-oauth
celery -A app.tasks.celery_app beat -l info
```

---

## Step 7: Test OAuth Flow (5 minutes)

### 1. Register a Test Tenant

Using cURL:
```bash
curl -X POST http://localhost:8000/api/v1/tenants/register \
  -H "Content-Type: application/json" \
  -d '{
    "slug": "test_restaurant",
    "name": "Test Restaurant",
    "email": "test@restaurant.com",
    "plan_type": "basic"
  }'
```

Or using Python:
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/tenants/register",
    json={
        "slug": "test_restaurant",
        "name": "Test Restaurant",
        "email": "test@restaurant.com",
        "plan_type": "basic"
    }
)

print(response.json())
# Save the tenant_id from response
tenant_id = response.json()["id"]
```

### 2. Start OAuth Flow

```bash
curl -X POST http://localhost:8000/api/v1/oauth/facebook/authorize \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "YOUR_TENANT_ID_HERE",
    "return_url": "http://localhost:8000/"
  }'
```

Or using Python:
```python
response = requests.post(
    "http://localhost:8000/api/v1/oauth/facebook/authorize",
    json={
        "tenant_id": tenant_id,  # from step 1
        "return_url": "http://localhost:8000/"
    }
)

result = response.json()
print(f"Authorization URL: {result['authorization_url']}")

# Open this URL in your browser
import webbrowser
webbrowser.open(result['authorization_url'])
```

### 3. Complete Authorization

1. Browser will open Facebook login
2. Log in with your Facebook account (the one that created the Facebook App)
3. Grant permissions to the app
4. You'll be redirected back to localhost

### 4. Verify Connected Accounts

```bash
curl "http://localhost:8000/api/v1/accounts/connected?tenant_id=YOUR_TENANT_ID_HERE"
```

Or using Python:
```python
response = requests.get(
    "http://localhost:8000/api/v1/accounts/connected",
    params={"tenant_id": tenant_id}
)

accounts = response.json()
print(f"Connected {len(accounts)} accounts:")
for account in accounts:
    print(f"  - {account['platform']}: {account['account_name']}")
```

### 5. Check Token Health

```bash
curl "http://localhost:8000/api/v1/accounts/token-health?tenant_id=YOUR_TENANT_ID_HERE"
```

---

## Troubleshooting

### "Database connection failed"
```bash
# Check if PostgreSQL is running
psql -l

# If not running (macOS):
brew services start postgresql@14

# If not running (Linux):
sudo systemctl start postgresql
```

### "Redis connection failed"
```bash
# Check if Redis is running
redis-cli ping
# Should output: PONG

# If not running (macOS):
brew services start redis

# If not running (Linux):
sudo systemctl start redis
```

### "Facebook OAuth redirect_uri_mismatch"
- Ensure `FACEBOOK_REDIRECT_URI` in `.env` **exactly** matches the redirect URI in Facebook App settings
- No trailing slashes
- Correct protocol (http for localhost)

### "Invalid encryption key"
```bash
# Regenerate keys
python generate_keys.py

# Copy new keys to .env
```

---

## Next Steps

### 1. Add More Tenants
```python
# Register another restaurant
requests.post(
    "http://localhost:8000/api/v1/tenants/register",
    json={
        "slug": "pizza_place",
        "name": "Amazing Pizza Place",
        "email": "admin@pizzaplace.com"
    }
)
```

### 2. Integrate with Posting System

```python
from app.services import TokenService
from app.models.base import SessionLocal

# Get active token for posting
db = SessionLocal()
token_service = TokenService()

access_token = token_service.get_active_token(
    db=db,
    tenant_id="YOUR_TENANT_ID",
    platform="facebook"
)

# Use this token to post to Facebook/Instagram
# (same as your existing posting code, but now with encrypted token)
```

### 3. Deploy to Production
See `README.md` for production deployment checklist

---

## Useful Commands

```bash
# Check health
curl http://localhost:8000/health
curl http://localhost:8000/health/db

# View API documentation
open http://localhost:8000/docs

# View Celery tasks
celery -A app.tasks.celery_app inspect active

# Monitor logs
tail -f logs/app.log

# Database queries
psql social_automation_multi_tenant

# List all tenants
psql social_automation_multi_tenant -c "SELECT id, slug, name, status FROM tenants;"

# List all connected accounts
psql social_automation_multi_tenant -c "SELECT platform, account_name, is_active FROM social_accounts;"
```

---

## Success Criteria

You've successfully set up the system when:

- ✅ FastAPI server running on http://localhost:8000
- ✅ API docs accessible at http://localhost:8000/docs
- ✅ Health check returns `{"status": "healthy"}`
- ✅ Can register a tenant
- ✅ Can complete OAuth flow
- ✅ See connected accounts in database
- ✅ Token health shows healthy tokens

---

## What You Built

🎉 **Congratulations!** You now have:

- ✅ **Multi-tenant OAuth system** - Scales to 1,000+ restaurants
- ✅ **Secure token storage** - AES-256-GCM encryption
- ✅ **Auto token refresh** - Background jobs keep tokens fresh
- ✅ **Facebook & Instagram** - Support for both platforms
- ✅ **Production-ready** - Complete error handling, logging, monitoring

---

## Getting Help

- **Setup Issues**: See `DATABASE_SETUP.md`, `ENVIRONMENT_SETUP.md`, `FACEBOOK_APP_SETUP.md`
- **API Reference**: http://localhost:8000/docs
- **Architecture**: See `README.md`
- **Development Log**: See `SESSION_LOG.md`

---

**Estimated Total Time**: 25-30 minutes

Happy coding! 🚀
