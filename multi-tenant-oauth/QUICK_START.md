# Quick Start Guide

Get the Social Automation Multi-Tenant OAuth Platform running in **under 15 minutes**.

This guide focuses on the fastest path to a working development environment. For detailed setup and production deployment, see [README.md](README.md).

---

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] **Python 3.11+** installed (`python3 --version`)
- [ ] **PostgreSQL 14+** installed and running
- [ ] **Redis 7+** installed and running
- [ ] **Facebook Developer Account** (create at [developers.facebook.com](https://developers.facebook.com))
- [ ] **OpenAI API Key** (optional, for AI features - get at [platform.openai.com](https://platform.openai.com))

---

## Step 1: Clone and Setup (2 minutes)

```bash
# Clone repository
git clone <repository-url>
cd multi-tenant-oauth

# Create and activate virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Verify**:
```bash
python --version  # Should show Python 3.11+
pip list | grep fastapi  # Should show fastapi package
```

---

## Step 2: Database Setup (2 minutes)

```bash
# Create database
createdb social_automation_multi_tenant

# Initialize schema
psql social_automation_multi_tenant < database_schema.sql

# Verify tables
psql social_automation_multi_tenant -c "\dt"
# Should list 8 tables: tenants, tenant_users, social_accounts, oauth_tokens, 
# token_refresh_history, post_history, webhook_events, oauth_state
```

**Troubleshooting**:
- If `createdb` not found: PostgreSQL not in PATH or not installed
- If connection error: PostgreSQL service not running (`brew services start postgresql@14` on macOS)

---

## Step 3: Redis Setup (1 minute)

```bash
# Start Redis (if not running)
brew services start redis  # macOS
# or
sudo systemctl start redis  # Linux

# Verify connection
redis-cli ping
# Should return: PONG
```

---

## Step 4: Environment Configuration (3 minutes)

```bash
# Copy example environment file
cp .env.example .env

# Generate security keys
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))" >> .env.temp
python -c "import secrets; print('ENCRYPTION_KEY=' + secrets.token_urlsafe(32))" >> .env.temp
cat .env.temp  # Copy these values into .env
rm .env.temp

# Edit .env with your configuration
nano .env
```

**Minimum Required Configuration**:

```bash
# Database
DATABASE_URL=postgresql://localhost/social_automation_multi_tenant

# Redis
REDIS_URL=redis://localhost:6379/0

# Security (paste generated keys from above)
SECRET_KEY=<generated-key>
ENCRYPTION_KEY=<generated-key>

# Facebook OAuth (we'll add these in Step 5)
FACEBOOK_APP_ID=
FACEBOOK_APP_SECRET=

# Application URLs
API_URL=http://localhost:8000
PUBLIC_URL=http://localhost:8000
```

**Save and close** (Ctrl+X, then Y, then Enter).

---

## Step 5: Facebook App Setup (5 minutes)

### 5.1 Create Facebook App

1. Go to [developers.facebook.com/apps](https://developers.facebook.com/apps)
2. Click **"Create App"**
3. Select **"Business"** as app type
4. Fill in:
   - **Display Name**: `Social Automation Dev`
   - **App Contact Email**: your email
5. Click **"Create App"**

### 5.2 Add Facebook Login

1. In App Dashboard, find **"Add Products to Your App"**
2. Locate **"Facebook Login"** → Click **"Set Up"**
3. Select **"Web"** platform
4. Enter **Site URL**: `http://localhost:8000`
5. Click **"Save"** → **"Continue"**

### 5.3 Configure OAuth Settings

1. Go to **Products** → **Facebook Login** → **Settings**
2. Add **Valid OAuth Redirect URIs**:
   ```
   http://localhost:8000/api/v1/oauth/facebook/callback
   ```
3. Configure toggles:
   - ✅ **Client OAuth Login**: ON
   - ✅ **Web OAuth Login**: ON
   - ✅ **Use Strict Mode for Redirect URIs**: ON
4. Click **"Save Changes"**

### 5.4 Add Instagram Graph API

1. Return to App Dashboard
2. Find **"Instagram Graph API"** → Click **"Set Up"**

### 5.5 Get Your Credentials

1. Go to **Settings** → **Basic**
2. Copy **App ID** and **App Secret**
3. Update `.env`:
   ```bash
   FACEBOOK_APP_ID=<your-app-id>
   FACEBOOK_APP_SECRET=<your-app-secret>
   ```

---

## Step 6: Start the Application (2 minutes)

### Terminal 1: FastAPI Server

```bash
# Activate venv if not already active
source venv/bin/activate

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected output**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Terminal 2: Celery Worker (Optional for now)

```bash
# Activate venv
source venv/bin/activate

# Start Celery worker
celery -A app.tasks.celery_app worker --loglevel=info
```

**Note**: Celery is only needed for background jobs (token refresh, scheduled posts). You can skip this for initial testing.

---

## Step 7: Verify Installation (1 minute)

### Test API Health

```bash
# API health
curl http://localhost:8000/health
# Expected: {"status":"healthy","service":"social-automation-oauth"}

# Database health
curl http://localhost:8000/health/db
# Expected: {"status":"healthy","database":"connected"}

# Redis health (if Celery running)
curl http://localhost:8000/health/redis
# Expected: {"status":"healthy","redis":"connected"}
```

### Access Interactive Docs

Open browser to:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

You should see all API endpoints documented.

---

## Step 8: Test Basic Workflow (5 minutes)

### 8.1 Register a Tenant

```bash
curl -X POST http://localhost:8000/api/v1/tenants \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Restaurant",
    "email": "test@restaurant.com",
    "plan": "pro"
  }'
```

**Response**:
```json
{
  "id": "uuid-here",
  "name": "Test Restaurant",
  "email": "test@restaurant.com",
  "plan": "pro",
  "created_at": "2025-12-28T..."
}
```

**Copy the `id`** - you'll need it in the next steps.

### 8.2 Initialize Folder Structure

```bash
# Replace {TENANT_ID} with the ID from previous step
curl -X POST http://localhost:8000/api/v1/tenants/{TENANT_ID}/init-folders
```

**Response**:
```json
{
  "message": "Folder structure initialized",
  "folders_created": 13
}
```

### 8.3 Connect Facebook Account

Open browser and visit:
```
http://localhost:8000/api/v1/oauth/facebook/authorize?tenant_id={TENANT_ID}
```

This will:
1. Redirect you to Facebook
2. Ask for permissions
3. Redirect back with connected accounts

**Note**: Use a Facebook account that manages a Page for testing.

### 8.4 Upload a Brand Asset

```bash
# Upload an image (replace {FOLDER_ID} with root folder ID)
curl -X POST http://localhost:8000/api/v1/folders/{FOLDER_ID}/assets \
  -F "file=@/path/to/your/image.jpg" \
  -F "tags=test,food"
```

### 8.5 Test AI Caption Generation (if OpenAI key configured)

```bash
curl -X POST http://localhost:8000/api/v1/posts/generate \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "{TENANT_ID}",
    "platform": "facebook",
    "restaurant_name": "Test Restaurant",
    "restaurant_description": "Delicious homemade food",
    "item_name": "Pizza",
    "tone": "casual"
  }'
```

**Response**: AI-generated caption

---

## Next Steps

### Access the Web UI

- **Posting Interface**: [http://localhost:8000/ui](http://localhost:8000/ui)
- **Asset Management**: [http://localhost:8000/assets](http://localhost:8000/assets)

### Enable Image Posting (Development)

For Facebook to access your local images:

1. **Install ngrok**:
   ```bash
   brew install ngrok/ngrok/ngrok  # macOS
   ```

2. **Get auth token** from [ngrok.com/dashboard](https://dashboard.ngrok.com)

3. **Configure ngrok**:
   ```bash
   ngrok config add-authtoken YOUR_TOKEN
   ```

4. **Start tunnel**:
   ```bash
   ngrok http 8000
   ```

5. **Update .env** with ngrok URL:
   ```bash
   API_URL=https://your-ngrok-url.ngrok-free.dev
   PUBLIC_URL=https://your-ngrok-url.ngrok-free.dev
   ```

6. **Restart FastAPI server**

See [NGROK_SETUP.md](NGROK_SETUP.md) for details.

### Add OpenAI Integration

1. Get API key from [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Update `.env`:
   ```bash
   OPENAI_API_KEY=sk-your-key-here
   ```
3. Restart server
4. Test caption generation (Step 8.5 above)

---

## Common Issues

### Port 8000 already in use

```bash
# Find and kill process using port 8000
lsof -i :8000
kill -9 <PID>

# Or use different port
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### Database connection error

```bash
# Check PostgreSQL is running
brew services list | grep postgresql  # macOS
sudo systemctl status postgresql      # Linux

# Test connection
psql social_automation_multi_tenant
```

### Redis connection error

```bash
# Check Redis is running
brew services list | grep redis   # macOS
sudo systemctl status redis       # Linux

# Test connection
redis-cli ping  # Should return: PONG
```

### OAuth callback error

1. Verify FACEBOOK_REDIRECT_URI in .env matches exactly:
   ```
   http://localhost:8000/api/v1/oauth/facebook/callback
   ```
2. Verify same URI is in Facebook App settings
3. No trailing slashes!

### Module not found error

```bash
# Ensure venv is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

---

## Development Workflow

### Daily Development

```bash
# Terminal 1: Start server
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 (optional): Start Celery
source venv/bin/activate
celery -A app.tasks.celery_app worker --loglevel=info

# Terminal 3 (optional): Start ngrok
ngrok http 8000
```

### Making Changes

1. Edit code in your IDE
2. Server auto-reloads (thanks to `--reload` flag)
3. Test changes via Swagger UI or curl
4. Check logs in terminal

### Database Changes

```bash
# After modifying models, create migration
alembic revision --autogenerate -m "Description of change"

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

---

## What's Next?

**Explore the Documentation**:
- [README.md](README.md) - Complete setup and features
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design and data flow
- [CHANGELOG.md](CHANGELOG.md) - Version history
- [SESSION_LOG.md](../SESSION_LOG.md) - Development history

**Learn the Features**:
- Brand asset management with folders
- AI-powered content generation
- Multi-platform posting (Facebook + Instagram)
- Scheduled posts
- Analytics dashboard

**Production Deployment**:
See [README.md#production-deployment](README.md#production-deployment)

---

## Need Help?

- **API Documentation**: http://localhost:8000/docs
- **Health Checks**: http://localhost:8000/health
- **Logs**: Check your terminal output
- **Issues**: See [README.md#troubleshooting](README.md#troubleshooting)

---

**Congratulations!** 🎉

You now have a fully functional multi-tenant social media automation platform running locally!

Try posting to Facebook with AI-generated captions and images.

---

**Last Updated**: 2025-12-28  
**Version**: 1.0.2
