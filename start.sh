#!/bin/bash

# Railway startup script for Django app
echo "🚀 Starting CleanHandy Django application..."

# Set environment variables
export PYTHONUNBUFFERED=1
export DJANGO_SETTINGS_MODULE=cleanhandy.settings

# Function to check if database is ready
check_db() {
    python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cleanhandy.settings')
django.setup()
from django.db import connection
try:
    connection.ensure_connection()
    print('✅ Database connection successful!')
    exit(0)
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
" 2>/dev/null
}

# Wait for database with timeout
echo "⏳ Waiting for database connection..."
max_attempts=60
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if check_db; then
        echo "✅ Database is ready!"
        break
    fi
    
    attempt=$((attempt + 1))
    echo "⏳ Database attempt $attempt/$max_attempts - waiting 5 seconds..."
    sleep 5
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Database connection timeout after $max_attempts attempts"
    echo "🚀 Starting app anyway (migrations will run on first request)..."
fi

# Run migrations in background (non-blocking)
echo "📊 Running database migrations in background..."
python manage.py migrate --noinput &
MIGRATE_PID=$!

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Start the application
echo "🌐 Starting Gunicorn server on port $PORT..."
exec gunicorn cleanhandy.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --keep-alive 2 \
    --max-requests 1000 \
    --max-requests-jitter 100
