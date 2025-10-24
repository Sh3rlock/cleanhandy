#!/bin/bash

# Railway startup script for Django app
echo "🚀 Starting CleanHandy Django application..."

# Function to wait for database
wait_for_db() {
    echo "⏳ Waiting for database connection..."
    max_attempts=30
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if python -c "
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
    print(f'⏳ Database connection attempt {attempt + 1}/{max_attempts} failed: {e}')
    exit(1)
" 2>/dev/null; then
            return 0
        fi
        
        attempt=$((attempt + 1))
        if [ $attempt -lt $max_attempts ]; then
            echo "⏳ Waiting 2 seconds before retry..."
            sleep 2
        fi
    done
    
    echo "❌ Failed to connect to database after $max_attempts attempts"
    return 1
}

# Wait for database
if ! wait_for_db; then
    echo "❌ Database connection failed. Exiting."
    exit 1
fi

# Run database migrations
echo "📊 Running database migrations..."
python manage.py migrate --noinput

# Check if migrations were successful
if [ $? -eq 0 ]; then
    echo "✅ Migrations completed successfully"
else
    echo "❌ Migrations failed"
    exit 1
fi

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Start the application
echo "🌐 Starting Gunicorn server..."
exec gunicorn cleanhandy.wsgi:application --bind 0.0.0.0:$PORT
