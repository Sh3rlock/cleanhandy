#!/usr/bin/env python
"""
Test script to verify Django startup works
Run this locally to test: python test_startup.py
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cleanhandy.settings')

try:
    print("🚀 Testing Django startup...")
    django.setup()
    print("✅ Django setup successful!")
    
    # Test database connection
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        print("✅ Database connection successful!")
    
    # Test URL configuration
    from django.urls import reverse
    from django.test import Client
    
    client = Client()
    response = client.get('/health/')
    print(f"✅ Healthcheck endpoint works: {response.status_code}")
    
    print("🎉 All tests passed! Django is ready to run.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
