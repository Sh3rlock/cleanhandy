#!/usr/bin/env python
"""
Test Railway PostgreSQL connection
Run this to test if your local setup can connect to Railway's PostgreSQL
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

def test_railway_connection():
    """Test connection to Railway PostgreSQL"""
    print("🔍 Testing Railway PostgreSQL connection...")
    
    # Set the Railway DATABASE_URL
    railway_db_url = "postgresql://postgres:uNBHWTzTbtZAcmjSSnGoVBbKjBwDbFCo@postgres.railway.internal:5432/railway"
    os.environ['DATABASE_URL'] = railway_db_url
    
    try:
        print("1. Setting up Django...")
        django.setup()
        print("✅ Django setup complete")
        
        print("2. Testing database connection...")
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print("✅ Database connection successful!")
            
        print("3. Testing database info...")
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database(), current_user, version();")
            db_name, user, version = cursor.fetchone()
            print(f"📊 Database: {db_name}")
            print(f"👤 User: {user}")
            print(f"🐘 Version: {version}")
            
        print("4. Testing migrations...")
        from django.core.management import call_command
        call_command('migrate', '--dry-run')
        print("✅ Migrations would run successfully")
        
        print("🎉 All tests passed! Railway PostgreSQL connection works!")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure your Railway PostgreSQL service is running")
        print("2. Check if DATABASE_URL is correct in Railway dashboard")
        print("3. Verify the PostgreSQL service is accessible")
        return False

if __name__ == '__main__':
    success = test_railway_connection()
    sys.exit(0 if success else 1)
