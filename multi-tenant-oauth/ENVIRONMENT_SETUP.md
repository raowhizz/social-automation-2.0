# Environment Configuration Guide

Complete guide to configure environment variables for multi-tenant OAuth2 system.

---

## Quick Start

```bash
# 1. Navigate to multi-tenant-oauth directory
cd multi-tenant-oauth

# 2. Copy the example environment file
cp .env.example .env

# 3. Generate encryption keys
python generate_keys.py

# 4. Edit .env file with your credentials
nano .env  # or use your preferred editor
```

---

## Step 1: Generate Security Keys

Run the key generation script:

```bash
# Generate all required keys
python generate_keys.py
```

This will generate:
- `SECRET_KEY`: For JWT tokens and session management
- `ENCRYPTION_KEY`: For encrypting OAuth tokens (AES-256)

**The script will output values like:**
```
SECRET_KEY=kX9v2pL3mZ8qR7wE6tY5uI4oP1aS0dF2...
ENCRYPTION_KEY=dGVzdGluZ19rZXlfMzJfYnl0ZXNfbG9uZ19mb3JfYWVzXzI1Ng==
```

Copy these values into your `.env` file.

---

## Step 2: Configure Database

### Option A: Local PostgreSQL

```env
DATABASE_URL=postgresql://localhost/social_automation_multi_tenant
```

### Option B: PostgreSQL with User/Password

```env
DATABASE_URL=postgresql://your_username:your_password@localhost:5432/social_automation_multi_tenant
```

### Option C: Docker PostgreSQL

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/social_automation_multi_tenant
```

---

## Step 3: Configure Redis

### Local Redis

```env
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Docker Redis

```env
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

---

## Step 4: Configure Facebook App

Get these values from Facebook Developer Portal (see FACEBOOK_APP_SETUP.md):

```env
# From Facebook App Dashboard → Settings → Basic
FACEBOOK_APP_ID=123456789012345
FACEBOOK_APP_SECRET=abcdef1234567890abcdef1234567890

# Must match EXACTLY what you configured in Facebook Login settings
FACEBOOK_REDIRECT_URI=http://localhost:8000/oauth/facebook/callback

# Facebook API version (check latest at developers.facebook.com)
FACEBOOK_GRAPH_API_VERSION=v18.0

# Permissions to request (comma-separated, no spaces)
FACEBOOK_OAUTH_SCOPES=pages_show_list,pages_read_engagement,pages_manage_posts,instagram_basic,instagram_content_publish
```

**Important**: The `FACEBOOK_REDIRECT_URI` must **exactly** match one of the "Valid OAuth Redirect URIs" in your Facebook App settings.

---

## Step 5: Configure OpenAI (For Content Generation)

```env
OPENAI_API_KEY=sk-proj-...your-openai-api-key...
GPT_MODEL=gpt-4
GPT_VISION_MODEL=gpt-4-vision-preview
```

Get your API key from: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

---

## Step 6: Configure Application URLs

### Development (localhost)

```env
API_URL=http://localhost:8000
APP_URL=http://localhost:3000
PUBLIC_URL=http://localhost:8000
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

### Production

```env
API_URL=https://api.yourdomain.com
APP_URL=https://app.yourdomain.com
PUBLIC_URL=https://api.yourdomain.com
CORS_ORIGINS=https://app.yourdomain.com,https://yourdomain.com
```

---

## Step 7: Configure Token Management

```env
# Refresh tokens 7 days before expiration
TOKEN_REFRESH_THRESHOLD_DAYS=7

# OAuth state expires in 10 minutes
OAUTH_STATE_EXPIRATION_MINUTES=10

# Cache tokens for 5 minutes
TOKEN_CACHE_TTL=300

# Background job schedule
TOKEN_REFRESH_INTERVAL=24  # Check every 24 hours
STATE_CLEANUP_INTERVAL=1   # Cleanup every hour
```

---

## Step 8: Configure Rate Limits

```env
# API requests per hour
RATE_LIMIT_BASIC=100
RATE_LIMIT_PRO=500
RATE_LIMIT_ENTERPRISE=2000

# Posts per day
POST_LIMIT_BASIC=10
POST_LIMIT_PRO=50
POST_LIMIT_ENTERPRISE=200
```

---

## Step 9: Configure Logging

```env
# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# Development mode
DEBUG=True
RELOAD=True  # Auto-reload on code changes
```

For production:
```env
LOG_LEVEL=WARNING
DEBUG=False
RELOAD=False
```

---

## Complete .env Example

Here's a complete example for local development:

```env
# ===================================
# DATABASE & REDIS
# ===================================
DATABASE_URL=postgresql://localhost/social_automation_multi_tenant
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# ===================================
# SECURITY KEYS (Generate with: python generate_keys.py)
# ===================================
SECRET_KEY=your-generated-secret-key-here
ENCRYPTION_KEY=your-generated-encryption-key-here

# ===================================
# FACEBOOK APP
# ===================================
FACEBOOK_APP_ID=123456789012345
FACEBOOK_APP_SECRET=abcdef1234567890abcdef1234567890
FACEBOOK_REDIRECT_URI=http://localhost:8000/oauth/facebook/callback
FACEBOOK_GRAPH_API_VERSION=v18.0
FACEBOOK_OAUTH_SCOPES=pages_show_list,pages_read_engagement,pages_manage_posts,instagram_basic,instagram_content_publish

# ===================================
# OPENAI
# ===================================
OPENAI_API_KEY=sk-proj-your-api-key-here
GPT_MODEL=gpt-4
GPT_VISION_MODEL=gpt-4-vision-preview

# ===================================
# APPLICATION
# ===================================
API_URL=http://localhost:8000
PUBLIC_URL=http://localhost:8000
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
LOG_LEVEL=INFO
DEBUG=True
RELOAD=True

# ===================================
# TOKEN MANAGEMENT
# ===================================
TOKEN_REFRESH_THRESHOLD_DAYS=7
OAUTH_STATE_EXPIRATION_MINUTES=10
TOKEN_CACHE_TTL=300

# ===================================
# RATE LIMITS
# ===================================
RATE_LIMIT_BASIC=100
POST_LIMIT_BASIC=10
```

---

## Verification

Test your configuration:

```bash
# Test database connection
python -c "from sqlalchemy import create_engine; import os; from dotenv import load_dotenv; load_dotenv(); engine = create_engine(os.getenv('DATABASE_URL')); conn = engine.connect(); print('✅ Database connection successful'); conn.close()"

# Test Redis connection
python -c "import redis; import os; from dotenv import load_dotenv; load_dotenv(); r = redis.from_url(os.getenv('REDIS_URL')); r.ping(); print('✅ Redis connection successful')"

# Test encryption key
python -c "import base64, os; from dotenv import load_dotenv; load_dotenv(); key = base64.b64decode(os.getenv('ENCRYPTION_KEY')); assert len(key) == 32; print('✅ Encryption key valid')"
```

---

## Security Best Practices

### Development

- ✅ Use `.env` file (never commit to git)
- ✅ Add `.env` to `.gitignore`
- ✅ Use example values for testing
- ✅ Keep `.env.example` updated (without secrets)

### Production

- 🔒 Use environment variables (not .env file)
- 🔒 Use secret management (AWS Secrets Manager, etc.)
- 🔒 Rotate keys regularly
- 🔒 Use strong, unique keys (never reuse)
- 🔒 Enable HTTPS (never HTTP)
- 🔒 Restrict CORS to specific domains
- 🔒 Use managed database with encryption at rest

---

## Troubleshooting

### "No module named 'dotenv'"
```bash
pip install python-dotenv
```

### "Invalid ENCRYPTION_KEY"
- Must be 32 bytes, base64-encoded
- Generate new key: `python generate_keys.py`

### "Database connection failed"
- Verify PostgreSQL is running
- Check DATABASE_URL format
- Test connection: `psql $DATABASE_URL`

### "Redis connection failed"
- Verify Redis is running: `redis-cli ping`
- Check REDIS_URL format

### "Facebook OAuth redirect_uri_mismatch"
- Ensure FACEBOOK_REDIRECT_URI in .env **exactly** matches Facebook App settings
- No trailing slashes, correct protocol (http/https)

---

## Next Steps

After configuration:
1. ✅ Verify all connections work
2. ✅ Run database migrations: `alembic upgrade head`
3. ✅ Start development server: `uvicorn app.main:app --reload`
4. ✅ Test OAuth flow

---

**Estimated Time**: 5-10 minutes

For questions, see:
- `.env.example` - Full configuration template
- `FACEBOOK_APP_SETUP.md` - Facebook App configuration
- `DATABASE_SETUP.md` - Database setup guide
