# Service Management Guide

## Quick Start

```bash
# Start all services (FastAPI, Celery Worker, Celery Beat, Redis)
./start.sh

# Stop all services
./stop.sh

# Restart all services
./restart.sh
```

## What's Running

### 1. FastAPI Server
- **Port**: 8000
- **URL**: http://localhost:8000
- **Purpose**: Web API and dashboard
- **Log**: `logs/uvicorn.log`

### 2. Celery Worker
- **Purpose**: Executes background tasks
- **Log**: `logs/celery_worker.log`
- **Tasks**:
  - `publish_due_calendar_posts` - Auto-publishes approved calendar posts
  - `refresh_expiring_tokens` - Refreshes OAuth tokens
  - `cleanup_expired_states` - Cleans up OAuth states

### 3. Celery Beat Scheduler
- **Purpose**: Triggers periodic tasks
- **Log**: `logs/celery_beat.log`
- **Schedule**:
  - Calendar posts: Every 1 minute
  - Token refresh: Every 24 hours
  - State cleanup: Every 1 hour

### 4. Redis
- **Purpose**: Message broker for Celery
- **Port**: 6379

## Auto-Publishing Calendar Posts

### How It Works

1. **Create Calendar** → Generate monthly post calendar
2. **Approve Posts** → Approve posts you want to publish
3. **Automatic Publishing** → Celery checks every minute for approved posts that are due
4. **Post to Platforms** → Posts are published to Facebook/Instagram automatically
5. **Status Updates** → Post status changes to "published" or "failed"

### Post Lifecycle

```
draft → approved → published
   ↓               ↓
   └───────────→ failed
```

### Monitoring

```bash
# Watch Celery worker in real-time
tail -f logs/celery_worker.log

# Watch Celery beat scheduler
tail -f logs/celery_beat.log

# Watch FastAPI server
tail -f logs/uvicorn.log

# Check all logs
tail -f logs/*.log
```

## Troubleshooting

### Services Not Starting

```bash
# Check if Redis is running
redis-cli ping

# Start Redis if needed
redis-server --daemonize yes

# Check port 8000
lsof -i:8000

# Restart everything
./restart.sh
```

### Calendar Posts Not Auto-Publishing

1. Check Celery worker is running:
   ```bash
   ps aux | grep celery
   ```

2. Check logs for errors:
   ```bash
   tail -100 logs/celery_worker.log
   ```

3. Verify posts are approved and due:
   ```sql
   SELECT id, title, status, scheduled_date, scheduled_time
   FROM calendar_posts
   WHERE status = 'approved';
   ```

4. Check OAuth tokens are valid:
   ```bash
   # Check in dashboard or database
   ```

### Manual Publishing

If needed, you can manually test publishing a post:

```python
from app.services.content_calendar_service import ContentCalendarService
from app.models.base import SessionLocal

db = SessionLocal()
service = ContentCalendarService()
result = service.publish_calendar_post(db, "post-uuid-here")
print(result)
```

## Process Management

The scripts use PID files stored in `logs/` directory:
- `logs/uvicorn.pid` - FastAPI server process ID
- `logs/celery_worker.pid` - Celery worker process ID
- `logs/celery_beat.pid` - Celery beat process ID

## Production Deployment

For production, consider using:
- **Supervisor** or **systemd** for process management
- **Nginx** as reverse proxy
- **PostgreSQL** connection pooling
- **Flower** for Celery monitoring
- **Sentry** for error tracking

## Additional Commands

```bash
# Start only FastAPI
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Start only Celery worker
celery -A app.tasks.celery_app worker --loglevel=info

# Start only Celery beat
celery -A app.tasks.celery_app beat --loglevel=info

# Monitor Celery with Flower (optional)
celery -A app.tasks.celery_app flower
```
