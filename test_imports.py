#!/usr/bin/env python
"""
Test all imports to find any issues
"""

import os
import sys
from pathlib import Path

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cleanhandy.settings')

print("🚀 Testing imports...")

try:
    print("1. Testing basic imports...")
    import django
    print("✅ Django imported")
    
    print("2. Testing Django setup...")
    django.setup()
    print("✅ Django setup complete")
    
    print("3. Testing database...")
    from django.db import connection
    print("✅ Database connection imported")
    
    print("4. Testing models...")
    from quotes.models import Service
    print("✅ Models imported")
    
    print("5. Testing views...")
    from quotes.views import home
    print("✅ Views imported")
    
    print("6. Testing URLs...")
    from quotes.urls import urlpatterns
    print("✅ URLs imported")
    
    print("7. Testing WSGI...")
    from cleanhandy.wsgi import application
    print("✅ WSGI application imported")
    
    print("🎉 All imports successful!")
    
except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
