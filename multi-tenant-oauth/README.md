# Social Automation - Multi-Tenant OAuth Platform

A production-ready multi-tenant social media automation platform for restaurants, featuring OAuth2 authentication for Facebook and Instagram, AI-powered content generation, and intelligent brand asset management.

## Overview

This platform enables restaurant owners to:
- Connect multiple Facebook Pages and Instagram Business accounts via OAuth2
- Upload and organize brand assets (photos, videos) in a hierarchical folder system
- Generate AI-powered social media captions using OpenAI GPT-4
- Post content with images to Facebook and Instagram
- Schedule posts for future publication
- Track post history and engagement analytics
- Manage everything through a user-friendly web interface

## Key Features

### Multi-Tenant Architecture
- **Tenant Isolation**: Each restaurant operates in complete isolation with dedicated data
- **Scalable Design**: Supports 1,000+ concurrent tenants
- **Flexible Plans**: Basic, Pro, and Enterprise tiers with configurable rate limits

### Secure OAuth2 Authentication
- **Facebook Login**: Authenticate with Facebook to access Pages
- **Instagram Business**: Connect Instagram Business accounts linked to Facebook Pages
- **Encrypted Storage**: All OAuth tokens encrypted with AES-256-GCM
- **Automatic Refresh**: Background jobs refresh tokens before expiration
- **CSRF Protection**: State tokens prevent OAuth security attacks

### AI-Powered Content Generation
- **OpenAI GPT-4**: Generate engaging, contextual social media captions
- **Smart Anti-Repetition**: Analyzes recent posts to avoid repetitive content
- **Platform Optimization**: Different strategies for Facebook vs Instagram
- **Customizable Tone**: Professional, casual, humorous, promotional, educational
- **Context-Aware**: Uses restaurant description, item details, and brand voice
- **Configurable AI Usage**: Toggle between full AI mode or mixed template/AI mode for cost control

### Content Calendar Management
- **Monthly Calendars**: Generate complete monthly content calendars with AI-powered posts
- **Flexible Post Count**: Create 5-31 posts per month (default: 8, recommended: 8-15)
- **Strategic Planning**: AI analyzes restaurant data to create diverse post strategies
- **Post Variety**: Promotional posts, product showcases, weekend drivers, engagement polls, customer appreciation
- **AI Cost Control**: Toggle "Use AI for All Posts" to control OpenAI usage and costs
- **Progress Tracking**: Real-time generation progress with detailed logs
- **Complete Transparency**: View full OpenAI request/response data for debugging

### Brand Asset Management
- **Hierarchical Folders**: Organize images by category (Food, Drinks, Restaurant, Seasonal)
- **Metadata & Tagging**: Rich metadata and tags for easy discovery
- **Quick Upload**: Upload new assets on-the-fly during post creation
- **Asset Browser**: Visual grid interface for selecting images
- **Multiple Formats**: Support for JPEG, PNG, GIF, WebP

### Social Media Posting
- **Facebook Pages**: Post text and images to connected Facebook Pages
- **Instagram Business**: Post to Instagram Business accounts
- **Image Support**: Direct file upload for reliable image posting
- **Post Scheduling**: Schedule posts for future publication with Celery
- **Post History**: Complete history of all posts with engagement tracking

### Developer-Friendly
- **FastAPI**: Modern, fast Python web framework with auto-generated docs
- **RESTful API**: Clean API design with comprehensive endpoints
- **SQLAlchemy 2.0**: Modern ORM with async support
- **Background Jobs**: Celery + Redis for async task processing
- **Comprehensive Logging**: Structured logging for debugging and monitoring

## Tech Stack

### Backend
- **Framework**: FastAPI 0.104+ (Python 3.11+)
- **Database**: PostgreSQL 14+ with SQLAlchemy 2.0 ORM
- **Cache/Queue**: Redis 7+ for caching and Celery task queue
- **Task Queue**: Celery 5+ with Beat scheduler for background jobs
- **Authentication**: OAuth2 (Facebook/Instagram Graph API v18.0)
- **AI**: OpenAI GPT-4 for content generation
- **Encryption**: AES-256-GCM via cryptography library

### Frontend
- **UI Framework**: Vanilla JavaScript with modern CSS
- **Asset Management**: Interactive file browser with drag-and-drop
- **Posting Interface**: Rich text editor with image picker
- **Analytics Dashboard**: Real-time engagement metrics

### Infrastructure
- **Development**: ngrok for local image hosting (tunneling localhost)
- **Production**: AWS S3 for scalable image storage (recommended)
- **Monitoring**: Health checks for API, database, and Redis
- **Logging**: Python logging module with file rotation

## Project Structure

```
multi-tenant-oauth/
├── app/
│   ├── api/                    # API endpoints
│   │   ├── accounts.py         # Connected accounts management
│   │   ├── assets.py           # Brand asset library endpoints
│   │   ├── oauth.py            # OAuth flow endpoints
│   │   ├── posts.py            # Social media posting endpoints
│   │   └── tenants.py          # Tenant management endpoints
│   ├── models/                 # Database models
│   │   ├── asset.py            # Brand assets & folders
│   │   ├── oauth_state.py      # OAuth state tokens (CSRF)
│   │   ├── oauth_token.py      # OAuth access/refresh tokens
│   │   ├── post.py             # Post history & analytics
│   │   ├── social_account.py   # Connected social accounts
│   │   ├── tenant.py           # Tenants & users
│   │   └── webhook.py          # Webhook events
│   ├── services/               # Business logic
│   │   ├── asset_service.py    # Asset management
│   │   ├── content_generator.py # AI content generation
│   │   ├── oauth_service.py    # OAuth flow handling
│   │   ├── posting_service.py  # Social media posting
│   │   └── token_service.py    # Token lifecycle management
│   ├── tasks/                  # Background jobs
│   │   ├── celery_app.py       # Celery configuration
│   │   └── token_tasks.py      # Token refresh & cleanup
│   ├── utils/                  # Utilities
│   │   ├── encryption.py       # AES-256-GCM encryption
│   │   └── logger.py           # Structured logging
│   ├── static/                 # Static files
│   │   ├── posting-ui.html     # Posting interface
│   │   └── assets-ui.html      # Asset management UI
│   └── main.py                 # FastAPI application entry
├── uploads/                    # Local file storage
│   └── images/                 # Uploaded brand assets
├── logs/                       # Application logs
├── .env                        # Environment configuration
├── requirements.txt            # Python dependencies
├── database_schema.sql         # Database schema
└── README.md                   # This file
```

## Installation

### Prerequisites

- **Python**: 3.11 or higher
- **PostgreSQL**: 14 or higher
- **Redis**: 7 or higher
- **Facebook Developer Account**: For OAuth app credentials
- **OpenAI API Key**: For AI content generation (optional)
- **ngrok**: For local development image hosting (optional)

### Step 1: Clone Repository

```bash
cd /path/to/your/projects
git clone <repository-url>
cd multi-tenant-oauth
```

### Step 2: Set Up Python Environment

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Set Up PostgreSQL Database

```bash
# macOS (Homebrew)
brew install postgresql@14
brew services start postgresql@14
createdb social_automation_multi_tenant

# Ubuntu/Debian
sudo apt-get install postgresql-14
sudo systemctl start postgresql
sudo -u postgres createdb social_automation_multi_tenant

# Verify connection
psql social_automation_multi_tenant
\q
```

### Step 4: Set Up Redis

```bash
# macOS (Homebrew)
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# Verify connection
redis-cli ping
# Should return: PONG
```

### Step 5: Initialize Database Schema

```bash
# Run database schema
psql social_automation_multi_tenant < database_schema.sql

# Verify tables created
psql social_automation_multi_tenant -c "\dt"
# Should show 8 tables
```

### Step 6: Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env
```

**Required configuration:**

```bash
# Database
DATABASE_URL=postgresql://localhost/social_automation_multi_tenant

# Redis
REDIS_URL=redis://localhost:6379/0

# Security Keys (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here

# Facebook OAuth (get from developers.facebook.com/apps)
FACEBOOK_APP_ID=your-app-id
FACEBOOK_APP_SECRET=your-app-secret

# OpenAI (optional - get from platform.openai.com)
OPENAI_API_KEY=sk-your-key-here

# Application URLs
API_URL=http://localhost:8000
PUBLIC_URL=http://localhost:8000
```

### Step 7: Set Up Facebook App

1. Go to [developers.facebook.com](https://developers.facebook.com/apps)
2. Create a new app (type: Business)
3. Add products: Facebook Login + Instagram Graph API
4. Configure Facebook Login:
   - Valid OAuth Redirect URIs: `http://localhost:8000/api/v1/oauth/facebook/callback`
   - Client OAuth Login: YES
   - Web OAuth Login: YES
5. Configure Basic Settings:
   - App Domains: `localhost`
   - Add Platform: Website → `http://localhost:8000`
6. Copy App ID and App Secret to .env

See `FACEBOOK_APP_SETUP.md` for detailed instructions.

### Step 8: Set Up ngrok (Development Only)

For local development, use ngrok to expose localhost for Facebook image access:

```bash
# Install ngrok
brew install ngrok/ngrok/ngrok  # macOS
# or download from ngrok.com

# Configure auth token (get from ngrok.com/dashboard)
ngrok config add-authtoken YOUR_NGROK_TOKEN

# Start tunnel
ngrok http 8000

# Copy the HTTPS URL (e.g., https://abc123.ngrok-free.dev)
# Update .env:
# API_URL=https://your-ngrok-url.ngrok-free.dev
# PUBLIC_URL=https://your-ngrok-url.ngrok-free.dev
```

For production, use AWS S3 instead. See `NGROK_SETUP.md` for details.

## Running the Application

### Development Mode

```bash
# Terminal 1: Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Start Celery worker
celery -A app.tasks.celery_app worker --loglevel=info

# Terminal 3: Start Celery beat scheduler
celery -A app.tasks.celery_app beat --loglevel=info

# Terminal 4 (optional): Start ngrok
ngrok http 8000
```

### Production Mode

```bash
# Use Gunicorn with Uvicorn workers
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000

# Start Celery worker as daemon
celery -A app.tasks.celery_app worker --detach --loglevel=info

# Start Celery beat as daemon
celery -A app.tasks.celery_app beat --detach --loglevel=info
```

## API Documentation

Once the server is running, access interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Key API Endpoints

### Tenant Management
- `POST /api/v1/tenants` - Register new tenant
- `GET /api/v1/tenants/{tenant_id}` - Get tenant details
- `POST /api/v1/tenants/{tenant_id}/init-folders` - Initialize folder structure

### OAuth Flow
- `GET /api/v1/oauth/facebook/authorize` - Start Facebook OAuth
- `GET /api/v1/oauth/facebook/callback` - OAuth callback handler
- `GET /api/v1/oauth/instagram/authorize` - Start Instagram OAuth

### Connected Accounts
- `GET /api/v1/tenants/{tenant_id}/accounts` - List connected accounts
- `DELETE /api/v1/accounts/{account_id}` - Disconnect account
- `GET /api/v1/accounts/{account_id}/token-health` - Check token status

### Brand Assets
- `GET /api/v1/tenants/{tenant_id}/folders` - List folders
- `POST /api/v1/folders` - Create folder
- `GET /api/v1/folders/{folder_id}/assets` - List assets in folder
- `POST /api/v1/folders/{folder_id}/assets` - Upload asset
- `DELETE /api/v1/assets/{asset_id}` - Delete asset

### Social Media Posting
- `POST /api/v1/posts/generate` - Generate AI caption
- `POST /api/v1/posts/create` - Create post
- `POST /api/v1/posts/schedule` - Schedule post
- `GET /api/v1/tenants/{tenant_id}/posts` - Get post history

### Health Checks
- `GET /health` - API health
- `GET /health/db` - Database health
- `GET /health/redis` - Redis health

## Web Interface

Access the web UI at:

- **Main Dashboard**: http://localhost:8000/
- **Posting Interface**: http://localhost:8000/ui
- **Asset Management**: http://localhost:8000/assets

## Usage Example

### 1. Register a Tenant

```bash
curl -X POST http://localhost:8000/api/v1/tenants \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Krusty Pizza",
    "email": "owner@krustypizza.com",
    "plan": "pro"
  }'
```

Response:
```json
{
  "id": "1485f8b4-04e9-47b7-ad8a-27adbe78d20a",
  "name": "Krusty Pizza",
  "plan": "pro",
  "created_at": "2025-12-28T10:00:00"
}
```

### 2. Initialize Folder Structure

```bash
curl -X POST http://localhost:8000/api/v1/tenants/1485f8b4-04e9-47b7-ad8a-27adbe78d20a/init-folders
```

### 3. Connect Facebook Account

Visit:
```
http://localhost:8000/api/v1/oauth/facebook/authorize?tenant_id=1485f8b4-04e9-47b7-ad8a-27adbe78d20a
```

This redirects to Facebook, then back to your app with connected accounts.

### 4. Upload Brand Asset

```bash
curl -X POST http://localhost:8000/api/v1/folders/{folder_id}/assets \
  -F "file=@pizza.jpg" \
  -F "tags=pizza,margherita,lunch"
```

### 5. Generate AI Caption

```bash
curl -X POST http://localhost:8000/api/v1/posts/generate \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "1485f8b4-04e9-47b7-ad8a-27adbe78d20a",
    "platform": "facebook",
    "restaurant_name": "Krusty Pizza",
    "restaurant_description": "Fresh authentic Italian pizza made with love",
    "item_name": "Margherita Pizza",
    "item_description": "Classic Neapolitan pizza with buffalo mozzarella",
    "tone": "casual"
  }'
```

Response:
```json
{
  "caption": "🍕 Nothing beats the classics! Our Margherita Pizza features authentic buffalo mozzarella, San Marzano tomatoes, and fresh basil on a perfectly charred Neapolitan crust. Taste the tradition today! 🇮🇹✨ #MargheritaPizza #ItalianCuisine #PizzaLovers #FreshIngredients #AuthenticItalian"
}
```

### 6. Create Post with Image

```bash
curl -X POST http://localhost:8000/api/v1/posts/create \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "account-uuid",
    "caption": "Your generated caption here",
    "image_url": "http://localhost:8000/uploads/images/pizza.jpg",
    "platform": "facebook"
  }'
```

## Configuration

### Rate Limits

Adjust in .env:
```bash
RATE_LIMIT_BASIC=100      # requests/hour
RATE_LIMIT_PRO=500
RATE_LIMIT_ENTERPRISE=2000

POST_LIMIT_BASIC=10       # posts/day
POST_LIMIT_PRO=50
POST_LIMIT_ENTERPRISE=200
```

### Token Management

```bash
TOKEN_REFRESH_THRESHOLD_DAYS=7   # Refresh tokens 7 days before expiry
TOKEN_REFRESH_INTERVAL=24        # Check for expiring tokens every 24 hours
OAUTH_STATE_EXPIRATION_MINUTES=10  # OAuth state tokens expire in 10 minutes
```

### OpenAI Models

```bash
GPT_TEXT_MODEL=gpt-4              # Text generation model
OPENAI_API_KEY=sk-your-key-here   # Your OpenAI API key
```

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest

# Run with coverage
pytest --cov=app tests/
```

### Code Style

```bash
# Install dev dependencies
pip install black isort flake8

# Format code
black app/
isort app/

# Lint code
flake8 app/
```

### Database Migrations

Using Alembic for database migrations:

```bash
# Generate migration
alembic revision --autogenerate -m "Description"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Troubleshooting

### Server won't start

```bash
# Check if port 8000 is already in use
lsof -i :8000

# Kill existing process
pkill uvicorn

# Restart server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Database connection error

```bash
# Verify PostgreSQL is running
brew services list | grep postgresql  # macOS
systemctl status postgresql           # Linux

# Test connection
psql social_automation_multi_tenant
```

### Redis connection error

```bash
# Verify Redis is running
brew services list | grep redis  # macOS
systemctl status redis           # Linux

# Test connection
redis-cli ping
```

### OAuth not working

1. Verify Facebook App settings:
   - Valid OAuth Redirect URIs includes your callback URL
   - App is in Development mode for testing
2. Check .env has correct FACEBOOK_APP_ID and FACEBOOK_APP_SECRET
3. Verify callback URL matches exactly: `http://localhost:8000/api/v1/oauth/facebook/callback`

### Images not showing in posts

1. **Development**: Make sure ngrok is running
   ```bash
   ngrok http 8000
   # Update API_URL in .env to ngrok URL
   # Restart server
   ```

2. **Production**: Use AWS S3 for image hosting
   - Configure S3 bucket with public read access
   - Update .env with S3 credentials
   - Images will be uploaded to S3 automatically

### OpenAI content generation not working

1. Verify OPENAI_API_KEY in .env is valid
2. Check you have credits in your OpenAI account
3. Restart server after updating .env
4. Check logs for specific error:
   ```bash
   tail -f logs/app.log
   ```

## Production Deployment

### Pre-Deployment Checklist

- [ ] Set `DEBUG=False` in .env
- [ ] Generate strong `SECRET_KEY` and `ENCRYPTION_KEY`
- [ ] Update `PUBLIC_URL` to your domain
- [ ] Configure AWS S3 for image storage (replace ngrok)
- [ ] Set up SSL/TLS certificates (Let's Encrypt)
- [ ] Configure production database with connection pooling
- [ ] Set up Redis with persistence
- [ ] Configure email SMTP for alerts
- [ ] Set up monitoring (Sentry, DataDog, etc.)
- [ ] Update Facebook App with production callback URLs
- [ ] Configure CORS_ORIGINS for your frontend domain
- [ ] Set appropriate rate limits for production
- [ ] Set up automated backups for PostgreSQL
- [ ] Configure log rotation and aggregation

### Recommended Production Stack

- **Hosting**: AWS EC2, DigitalOcean, or Heroku
- **Database**: AWS RDS PostgreSQL or managed PostgreSQL
- **Cache/Queue**: AWS ElastiCache Redis or managed Redis
- **Image Storage**: AWS S3 with CloudFront CDN
- **Load Balancer**: AWS ALB or Nginx
- **Process Manager**: Supervisor or systemd
- **Monitoring**: Sentry, DataDog, or New Relic
- **Logging**: CloudWatch, Papertrail, or ELK Stack

### AWS S3 Setup (Production)

```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure

# Create S3 bucket
aws s3 mb s3://your-bucket-name --region us-east-1

# Set bucket policy for public read
# (Use AWS Console or aws s3api put-bucket-policy)

# Update .env
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_BUCKET=your-bucket-name
AWS_S3_REGION=us-east-1
API_URL=https://your-bucket.s3.amazonaws.com
```

## Support

For questions, issues, or contributions:

- **Documentation**: See `QUICKSTART.md`, `ARCHITECTURE.md`, `SESSION_LOG.md`
- **Issues**: Open an issue on GitHub
- **Email**: support@social-automation.com

## Version History

See `CHANGELOG.md` for detailed version history.

- **v1.0.2** (2025-12-28): Image posting fix with direct file upload and ngrok setup
- **v1.0.1** (2025-12-27): Brand asset management and OpenAI integration
- **v1.0.0** (2025-12-26): Initial OAuth implementation and multi-tenant foundation

## License

Copyright 2025. All rights reserved.

## Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Celery](https://docs.celeryproject.org/)
- [OpenAI](https://openai.com/)
- [Facebook Graph API](https://developers.facebook.com/docs/graph-api)
