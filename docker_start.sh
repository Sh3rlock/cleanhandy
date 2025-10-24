#!/bin/bash

# Docker startup script for Railway
echo "🚀 Starting CleanHandy in Docker container..."

# Set environment variables
export PYTHONUNBUFFERED=1
export DJANGO_SETTINGS_MODULE=cleanhandy.settings

# Function to test database connection
test_db_connection() {
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

# Wait for database to be ready
echo "⏳ Waiting for database connection..."
max_attempts=60
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if test_db_connection; then
        echo "✅ Database is ready!"
        break
    fi
    
    attempt=$((attempt + 1))
    echo "⏳ Database attempt $attempt/$max_attempts - waiting 3 seconds..."
    sleep 3
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Database connection timeout after $max_attempts attempts"
    echo "🚀 Starting app anyway (migrations will run on first request)..."
fi

# Run migrations (with error handling)
echo "📊 Running database migrations..."
if python manage.py migrate --noinput; then
    echo "✅ Migrations completed successfully!"
else
    echo "⚠️  Migrations failed, but continuing..."
fi

# Start the application
echo "🌐 Starting Gunicorn server on port ${PORT:-8000}..."
exec gunicorn cleanhandy.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 1 \
    --timeout 300 \
    --keep-alive 2 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --access-logfile - \
    --error-logfile -
