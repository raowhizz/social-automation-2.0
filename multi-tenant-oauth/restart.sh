#!/bin/bash

# Restart all services for Social Automation Platform
# Usage: ./restart.sh

echo "🔄 Restarting Social Automation Platform..."
echo ""

# Stop all services
./stop.sh

# Wait a moment
sleep 2

# Start all services
./start.sh
