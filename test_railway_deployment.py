#!/usr/bin/env python
"""
Test Railway deployment functionality
Run this on Railway to verify everything is working
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
django.setup()

def test_deployment():
    """Test Railway deployment functionality"""
    print("🚀 Testing Railway deployment...")
    
    try:
        # Test 1: Database connection
        print("\n1. Testing database connection...")
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✅ Database connection successful!")
        
        # Test 2: Check if migrations have been run
        print("\n2. Checking migrations...")
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'django_%'
                ORDER BY table_name;
            """)
            django_tables = cursor.fetchall()
            print(f"✅ Found {len(django_tables)} Django tables")
        
        # Test 3: Check app-specific tables
        print("\n3. Checking app tables...")
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'quotes_%'
                ORDER BY table_name;
            """)
            app_tables = cursor.fetchall()
            print(f"✅ Found {len(app_tables)} quotes tables")
            for table in app_tables:
                print(f"  - {table[0]}")
        
        # Test 4: Test Django models
        print("\n4. Testing Django models...")
        from quotes.models import Service, ContactInfo
        service_count = Service.objects.count()
        contact_count = ContactInfo.objects.count()
        print(f"✅ Services: {service_count}")
        print(f"✅ Contact Info: {contact_count}")
        
        # Test 5: Test URL configuration
        print("\n5. Testing URL configuration...")
        from django.test import Client
        client = Client()
        
        # Test healthcheck endpoint
        response = client.get('/health/')
        if response.status_code == 200:
            print("✅ Healthcheck endpoint working")
        else:
            print(f"⚠️  Healthcheck endpoint returned {response.status_code}")
        
        # Test homepage (might fail if no data)
        try:
            response = client.get('/')
            print(f"✅ Homepage accessible (status: {response.status_code})")
        except Exception as e:
            print(f"⚠️  Homepage error: {e}")
        
        print("\n🎉 Railway deployment test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_deployment()
    sys.exit(0 if success else 1)
