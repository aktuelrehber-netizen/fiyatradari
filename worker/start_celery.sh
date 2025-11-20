#!/bin/bash
# Start Celery Distributed Worker System
# Usage: ./start_celery.sh [workers_count]

set -e

WORKERS=${1:-3}  # Default 3 workers
CONCURRENCY=${2:-4}  # Default 4 concurrent tasks per worker

echo "=========================================="
echo "Starting Celery Distributed Worker System"
echo "=========================================="
echo "Workers: $WORKERS"
echo "Concurrency per worker: $CONCURRENCY"
echo "Total concurrent tasks: $((WORKERS * CONCURRENCY))"
echo "=========================================="

# Check if Redis is running
echo "Checking Redis..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis is not running. Starting Redis..."
    redis-server --daemonize yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    sleep 2
fi
echo "✅ Redis is running"

# Check database connection
echo "Checking database connection..."
python3 -c "from database import get_db; next(get_db())" 2>/dev/null && echo "✅ Database connection OK" || echo "❌ Database connection failed"

# Apply migrations if needed
echo "Checking migrations..."
if [ -f "../backend/migrations/add_celery_fields.sql" ]; then
    echo "⚠️  Remember to run: psql -U fiyatradari -d fiyatradari -f backend/migrations/add_celery_fields.sql"
fi

# Kill existing Celery processes
echo "Stopping existing Celery processes..."
pkill -f "celery.*worker" || true
pkill -f "celery.*beat" || true
pkill -f "celery.*flower" || true
sleep 2

# Start Celery Beat (Scheduler)
echo "Starting Celery Beat (Scheduler)..."
celery -A celery_app beat --loglevel=info --logfile=logs/celery_beat.log --detach
sleep 2
echo "✅ Celery Beat started"

# Start Celery Workers
echo "Starting $WORKERS Celery Workers..."
for i in $(seq 1 $WORKERS); do
    echo "  Starting worker $i..."
    celery -A celery_app worker \
        --loglevel=info \
        --concurrency=$CONCURRENCY \
        --max-tasks-per-child=50 \
        --logfile=logs/celery_worker_$i.log \
        --hostname=worker$i@%h \
        --detach
    sleep 1
done
echo "✅ $WORKERS workers started"

# Start Flower (Monitoring)
echo "Starting Flower (Monitoring)..."
celery -A celery_app flower --port=5555 --logfile=logs/flower.log &
sleep 2
echo "✅ Flower started at http://localhost:5555"

echo ""
echo "=========================================="
echo "✅ Celery System Started Successfully!"
echo "=========================================="
echo ""
echo "Monitoring:"
echo "  - Flower Dashboard: http://localhost:5555"
echo "  - Worker logs: tail -f logs/celery_worker_*.log"
echo "  - Beat logs: tail -f logs/celery_beat.log"
echo ""
echo "Useful commands:"
echo "  - Check status: celery -A celery_app inspect active"
echo "  - Stop all: ./stop_celery.sh"
echo "  - Scale workers: ./start_celery.sh 10"
echo ""
echo "Statistics:"
python3 -c "
from services.smart_batch_processor import SmartBatchProcessor
import json
stats = SmartBatchProcessor().get_statistics()
print(json.dumps(stats, indent=2))
" 2>/dev/null || echo "Run statistics manually: python -c 'from services.smart_batch_processor import SmartBatchProcessor; print(SmartBatchProcessor().get_statistics())'"
echo ""
