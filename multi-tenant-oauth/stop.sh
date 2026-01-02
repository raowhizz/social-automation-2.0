#!/bin/bash

# Stop all services for Social Automation Platform
# Usage: ./stop.sh

echo "🛑 Stopping Social Automation Platform..."

# Function to stop a service by PID file
stop_service() {
    local name=$1
    local pid_file=$2

    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        if ps -p $PID > /dev/null 2>&1; then
            echo "  Stopping $name (PID: $PID)..."
            kill $PID 2>/dev/null || true
            sleep 1
            # Force kill if still running
            if ps -p $PID > /dev/null 2>&1; then
                kill -9 $PID 2>/dev/null || true
            fi
            rm "$pid_file"
            echo "  ✅ $name stopped"
        else
            echo "  ⚠️  $name not running (stale PID file)"
            rm "$pid_file"
        fi
    else
        echo "  ℹ️  $name PID file not found"
    fi
}

# Stop FastAPI server
stop_service "FastAPI server" "logs/uvicorn.pid"

# Stop Celery worker
stop_service "Celery worker" "logs/celery_worker.pid"

# Stop Celery beat
stop_service "Celery beat" "logs/celery_beat.pid"

# Also kill any remaining celery processes
CELERY_PIDS=$(pgrep -f "celery.*app.tasks" || true)
if [ ! -z "$CELERY_PIDS" ]; then
    echo "  Cleaning up remaining Celery processes..."
    echo $CELERY_PIDS | xargs kill -9 2>/dev/null || true
fi

# Kill any process still on port 8000
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "  Cleaning up port 8000..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
fi

echo ""
echo "✅ All services stopped"
echo ""
