#!/usr/bin/env python
"""
Database management script for CleanHandy
Run this to manage your PostgreSQL database on Railway
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

from django.core.management import call_command
from django.db import connection

def show_menu():
    """Display the main menu"""
    print("\n" + "="*50)
    print("🗄️  CleanHandy Database Management")
    print("="*50)
    print("1. Test database connection")
    print("2. Run migrations")
    print("3. Create superuser")
    print("4. Show database status")
    print("5. Access Django shell")
    print("6. Export data")
    print("7. Import data")
    print("8. Reset database (DANGER)")
    print("9. Exit")
    print("="*50)

def test_connection():
    """Test database connection"""
    print("\n🔍 Testing database connection...")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✅ Database connection successful!")
            
            # Show database info
            cursor.execute("SELECT current_database(), current_user, version();")
            db_name, user, version = cursor.fetchone()
            print(f"📊 Database: {db_name}")
            print(f"👤 User: {user}")
            print(f"🐘 Version: {version}")
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

def run_migrations():
    """Run database migrations"""
    print("\n📊 Running database migrations...")
    try:
        call_command('migrate', verbosity=2)
        print("✅ Migrations completed successfully!")
    except Exception as e:
        print(f"❌ Migration failed: {e}")

def create_superuser():
    """Create a superuser"""
    print("\n👤 Creating superuser...")
    try:
        call_command('createsuperuser')
        print("✅ Superuser created successfully!")
    except Exception as e:
        print(f"❌ Failed to create superuser: {e}")

def show_status():
    """Show database status"""
    print("\n📊 Database Status:")
    try:
        with connection.cursor() as cursor:
            # Show tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            print(f"📋 Total tables: {len(tables)}")
            
            # Show Django tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'django_%'
                ORDER BY table_name;
            """)
            django_tables = cursor.fetchall()
            print(f"🎯 Django tables: {len(django_tables)}")
            
            # Show app tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'quotes_%'
                ORDER BY table_name;
            """)
            app_tables = cursor.fetchall()
            print(f"📱 App tables: {len(app_tables)}")
            
            # Show database size
            cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()));")
            size = cursor.fetchone()[0]
            print(f"💾 Database size: {size}")
            
    except Exception as e:
        print(f"❌ Failed to get status: {e}")

def export_data():
    """Export data to JSON"""
    print("\n📤 Exporting data...")
    try:
        filename = f"data_export_{os.getpid()}.json"
        call_command('dumpdata', 
                    '--natural-foreign', 
                    '--natural-primary',
                    '--exclude=contenttypes',
                    '--exclude=auth.Permission',
                    '--exclude=sessions.Session',
                    '--output', filename)
        print(f"✅ Data exported to {filename}")
    except Exception as e:
        print(f"❌ Export failed: {e}")

def import_data():
    """Import data from JSON"""
    print("\n📥 Importing data...")
    filename = input("Enter filename (or press Enter for data_export.json): ").strip()
    if not filename:
        filename = "data_export.json"
    
    if not os.path.exists(filename):
        print(f"❌ File {filename} not found")
        return
    
    try:
        call_command('loaddata', filename)
        print("✅ Data imported successfully!")
    except Exception as e:
        print(f"❌ Import failed: {e}")

def reset_database():
    """Reset database (DANGER)"""
    print("\n⚠️  WARNING: This will delete ALL data!")
    confirm = input("Type 'DELETE' to confirm: ")
    if confirm != 'DELETE':
        print("❌ Operation cancelled")
        return
    
    try:
        # Drop all tables
        with connection.cursor() as cursor:
            cursor.execute("DROP SCHEMA public CASCADE;")
            cursor.execute("CREATE SCHEMA public;")
            cursor.execute("GRANT ALL ON SCHEMA public TO postgres;")
            cursor.execute("GRANT ALL ON SCHEMA public TO public;")
        
        print("✅ Database reset completed!")
        print("📊 Run migrations to recreate tables")
        
    except Exception as e:
        print(f"❌ Reset failed: {e}")

def access_shell():
    """Access Django shell"""
    print("\n🐍 Opening Django shell...")
    try:
        call_command('shell')
    except Exception as e:
        print(f"❌ Failed to open shell: {e}")

def main():
    """Main function"""
    while True:
        show_menu()
        choice = input("\nEnter your choice (1-9): ").strip()
        
        if choice == '1':
            test_connection()
        elif choice == '2':
            run_migrations()
        elif choice == '3':
            create_superuser()
        elif choice == '4':
            show_status()
        elif choice == '5':
            access_shell()
        elif choice == '6':
            export_data()
        elif choice == '7':
            import_data()
        elif choice == '8':
            reset_database()
        elif choice == '9':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == '__main__':
    main()
