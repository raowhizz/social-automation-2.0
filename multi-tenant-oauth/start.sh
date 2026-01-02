#!/bin/bash

# Start all services for Social Automation Platform
# Usage: ./start.sh

set -e

echo "🚀 Starting Social Automation Platform..."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Environment variables loaded"
else
    echo "⚠️  Warning: .env file not found"
fi

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "📦 Starting Redis..."
    redis-server --daemonize yes
    sleep 2
    echo "✅ Redis started"
else
    echo "✅ Redis already running"
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Kill any existing processes on port 8000
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "🔄 Stopping existing server on port 8000..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Start FastAPI server
echo "🌐 Starting FastAPI server..."
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > logs/uvicorn.log 2>&1 &
UVICORN_PID=$!
echo $UVICORN_PID > logs/uvicorn.pid
echo "✅ FastAPI server started (PID: $UVICORN_PID)"

# Start Celery worker (using solo pool for macOS compatibility)
echo "⚙️  Starting Celery worker..."
nohup celery -A app.tasks.celery_app worker --pool=solo --loglevel=info > logs/celery_worker.log 2>&1 &
WORKER_PID=$!
echo $WORKER_PID > logs/celery_worker.pid
echo "✅ Celery worker started (PID: $WORKER_PID)"

# Start Celery beat scheduler
echo "⏰ Starting Celery beat scheduler..."
nohup celery -A app.tasks.celery_app beat --loglevel=info > logs/celery_beat.log 2>&1 &
BEAT_PID=$!
echo $BEAT_PID > logs/celery_beat.pid
echo "✅ Celery beat started (PID: $BEAT_PID)"

# Wait a moment for services to start
sleep 3

echo ""
echo "✨ All services started successfully!"
echo ""
echo "📊 Service Status:"
echo "  - FastAPI Server: http://localhost:8000 (PID: $UVICORN_PID)"
echo "  - Celery Worker:  Running (PID: $WORKER_PID)"
echo "  - Celery Beat:    Running (PID: $BEAT_PID)"
echo "  - Redis:          Running"
echo ""
echo "📝 Logs:"
echo "  - FastAPI:  tail -f logs/uvicorn.log"
echo "  - Worker:   tail -f logs/celery_worker.log"
echo "  - Beat:     tail -f logs/celery_beat.log"
echo ""
echo "🛑 To stop all services: ./stop.sh"
echo ""
