#!/usr/bin/env python
"""
Export data from SQLite database
"""

import os
import sys
import django
import json
from pathlib import Path

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sqlite_settings')

def export_data():
    """Export data from SQLite database"""
    print("🚀 Starting data export from SQLite...")
    
    try:
        # Setup Django
        django.setup()
        print("✅ Django setup complete")
        
        # Check database connection
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"📊 Found {len(tables)} tables in database")
            
            # Show all tables
            for table in tables:
                print(f"  - {table[0]}")
        
        # Export data using Django's dumpdata
        from django.core.management import call_command
        from io import StringIO
        
        print("📤 Exporting data...")
        output = StringIO()
        call_command('dumpdata', 
                    '--natural-foreign', 
                    '--natural-primary',
                    '--exclude=contenttypes',
                    '--exclude=auth.Permission',
                    '--exclude=sessions.Session',
                    stdout=output)
        
        # Save to file
        data = output.getvalue()
        with open('data_export.json', 'w') as f:
            f.write(data)
        
        print(f"✅ Data exported to data_export.json ({len(data)} characters)")
        
        # Show some stats
        try:
            data_json = json.loads(data)
            print(f"📊 Exported {len(data_json)} records")
            
            # Count by model
            model_counts = {}
            for item in data_json:
                model = item['model']
                model_counts[model] = model_counts.get(model, 0) + 1
            
            print("📋 Records by model:")
            for model, count in sorted(model_counts.items()):
                print(f"  - {model}: {count}")
                
        except json.JSONDecodeError as e:
            print(f"⚠️  Could not parse JSON: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = export_data()
    sys.exit(0 if success else 1)
