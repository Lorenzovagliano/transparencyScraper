#!/bin/bash

# Set environment variables
export REDIS_URL="redis://localhost:6379/0"
export DJANGO_SETTINGS_MODULE="gov_scraper.settings"

# Function to handle shutdown
cleanup() {
    echo "Shutting down services..."
    kill $REDIS_PID $DJANGO_PID $CELERY_PID 2>/dev/null
    wait
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Start Redis in background
echo "Starting Redis..."
redis-server --bind 0.0.0.0 --port 6379 --daemonize yes

# Wait for Redis to be ready
sleep 2

# Start Django in background
echo "Starting Django..."
cd /app
poetry run python manage.py runserver 0.0.0.0:8000 &
DJANGO_PID=$!

# Start Celery worker in background
echo "Starting Celery worker..."
poetry run celery -A gov_scraper worker -l info -P solo &
CELERY_PID=$!

# Wait for all background processes
wait $DJANGO_PID $CELERY_PID