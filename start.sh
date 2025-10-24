#!/bin/bash

# Railway startup script for Django app
echo "🚀 Starting CleanHandy Django application..."

# Wait for database to be ready
echo "⏳ Waiting for database connection..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cleanhandy.settings')
django.setup()
from django.db import connection
from django.core.exceptions import ImproperlyConfigured
import time

max_attempts = 30
attempt = 0
while attempt < max_attempts:
    try:
        connection.ensure_connection()
        print('✅ Database connection successful!')
        break
    except Exception as e:
        attempt += 1
        print(f'⏳ Database connection attempt {attempt}/{max_attempts} failed: {e}')
        if attempt < max_attempts:
            time.sleep(2)
        else:
            print('❌ Failed to connect to database after 30 attempts')
            exit(1)
"

# Run database migrations
echo "📊 Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Start the application
echo "🌐 Starting Gunicorn server..."
exec gunicorn cleanhandy.wsgi:application --bind 0.0.0.0:$PORT
