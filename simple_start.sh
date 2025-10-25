#!/bin/bash

echo "🚀 Starting CleanHandy - Simple Mode"

# Test Python
echo "🐍 Testing Python..."
python --version

# Test Django
echo "🎯 Testing Django..."
python -c "import django; print('Django version:', django.get_version())"

# Test database connection
echo "🗄️ Testing database connection..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cleanhandy.settings')
django.setup()
from django.db import connection
try:
    connection.ensure_connection()
    print('✅ Database connection successful!')
except Exception as e:
    print('❌ Database connection failed:', e)
    exit(1)
"

# Run migrations
echo "📊 Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Start the app
echo "🌐 Starting Gunicorn..."
exec gunicorn cleanhandy.wsgi:application --bind 0.0.0.0:$PORT --timeout 300 --workers 1
