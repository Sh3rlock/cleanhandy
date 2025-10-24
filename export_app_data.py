#!/usr/bin/env python
"""
Export app-specific data from SQLite database
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

def export_app_data():
    """Export app-specific data from SQLite database"""
    print("🚀 Starting app data export from SQLite...")
    
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
        
        # Export only app-specific data
        from django.core.management import call_command
        from io import StringIO
        
        print("📤 Exporting app data...")
        output = StringIO()
        
        # List of apps to export
        apps_to_export = [
            'quotes',
            'bookings', 
            'customers',
            'adminpanel',
            'blog',
            'accounts',
            'giftcards'
        ]
        
        all_data = []
        
        for app in apps_to_export:
            try:
                print(f"  Exporting {app}...")
                app_output = StringIO()
                call_command('dumpdata', 
                            app,
                            '--natural-foreign', 
                            '--natural-primary',
                            stdout=app_output)
                
                app_data = app_output.getvalue()
                if app_data.strip():
                    # Parse JSON and add to all_data
                    app_json = json.loads(app_data)
                    all_data.extend(app_json)
                    print(f"    ✅ {app}: {len(app_json)} records")
                else:
                    print(f"    ⚠️  {app}: No data")
                    
            except Exception as e:
                print(f"    ❌ {app}: {e}")
        
        # Save all data to file
        with open('data_export.json', 'w') as f:
            json.dump(all_data, f, indent=2)
        
        print(f"✅ Data exported to data_export.json ({len(all_data)} total records)")
        
        # Show summary
        model_counts = {}
        for item in all_data:
            model = item['model']
            model_counts[model] = model_counts.get(model, 0) + 1
        
        print("📋 Records by model:")
        for model, count in sorted(model_counts.items()):
            print(f"  - {model}: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = export_app_data()
    sys.exit(0 if success else 1)
