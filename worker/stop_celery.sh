#!/bin/bash
# Stop Celery Distributed Worker System

echo "=========================================="
echo "Stopping Celery System"
echo "=========================================="

# Graceful shutdown
echo "Sending shutdown signal to workers..."
celery -A celery_app control shutdown 2>/dev/null || true
sleep 3

# Force kill if still running
echo "Stopping remaining processes..."
pkill -f "celery.*worker" || true
pkill -f "celery.*beat" || true
pkill -f "celery.*flower" || true

sleep 2

# Check if stopped
if pgrep -f "celery" > /dev/null; then
    echo "⚠️  Some Celery processes still running"
    echo "Force killing..."
    pkill -9 -f "celery" || true
else
    echo "✅ All Celery processes stopped"
fi

echo ""
echo "Celery system stopped successfully"
