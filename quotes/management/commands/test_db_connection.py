from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Test database connection and show connection details'

    def add_arguments(self, parser):
        parser.add_argument(
            '--show-credentials',
            action='store_true',
            help='Show database credentials (use with caution)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔍 Testing database connection...'))
        
        # Show database configuration
        db_config = settings.DATABASES['default']
        self.stdout.write(f"📊 Database Engine: {db_config['ENGINE']}")
        self.stdout.write(f"📊 Database Name: {db_config['NAME']}")
        
        if options['show_credentials']:
            self.stdout.write(f"👤 User: {db_config.get('USER', 'N/A')}")
            self.stdout.write(f"🏠 Host: {db_config.get('HOST', 'N/A')}")
            self.stdout.write(f"🔌 Port: {db_config.get('PORT', 'N/A')}")
        
        # Test connection
        try:
            with connection.cursor() as cursor:
                # Test basic connection
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                self.stdout.write(self.style.SUCCESS('✅ Database connection successful!'))
                
                # Get database version
                if 'postgresql' in db_config['ENGINE']:
                    cursor.execute("SELECT version();")
                    version = cursor.fetchone()[0]
                    self.stdout.write(f"🐘 PostgreSQL Version: {version}")
                
                # Check if migrations have been run
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name LIKE 'django_%'
                    ORDER BY table_name;
                """)
                django_tables = cursor.fetchall()
                
                if django_tables:
                    self.stdout.write(self.style.SUCCESS(f'✅ Found {len(django_tables)} Django tables'))
                    self.stdout.write("📋 Django tables:")
                    for table in django_tables[:5]:  # Show first 5
                        self.stdout.write(f"  - {table[0]}")
                    if len(django_tables) > 5:
                        self.stdout.write(f"  ... and {len(django_tables) - 5} more")
                else:
                    self.stdout.write(self.style.WARNING('⚠️  No Django tables found. Run migrations first.'))
                
                # Check for app-specific tables
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name LIKE 'quotes_%'
                    ORDER BY table_name;
                """)
                quotes_tables = cursor.fetchall()
                
                if quotes_tables:
                    self.stdout.write(self.style.SUCCESS(f'✅ Found {len(quotes_tables)} quotes tables'))
                else:
                    self.stdout.write(self.style.WARNING('⚠️  No quotes tables found. Run migrations first.'))
                
                # Check database size
                if 'postgresql' in db_config['ENGINE']:
                    cursor.execute("""
                        SELECT pg_size_pretty(pg_database_size(current_database()));
                    """)
                    size = cursor.fetchone()[0]
                    self.stdout.write(f"💾 Database size: {size}")
                
                # Check active connections
                if 'postgresql' in db_config['ENGINE']:
                    cursor.execute("""
                        SELECT count(*) FROM pg_stat_activity 
                        WHERE state = 'active';
                    """)
                    active_connections = cursor.fetchone()[0]
                    self.stdout.write(f"🔗 Active connections: {active_connections}")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Database connection failed: {e}'))
            return
        
        # Show environment variables
        self.stdout.write("\n🔧 Environment Variables:")
        if os.getenv('DATABASE_URL'):
            self.stdout.write("✅ DATABASE_URL is set")
            if options['show_credentials']:
                self.stdout.write(f"🔗 DATABASE_URL: {os.getenv('DATABASE_URL')}")
        else:
            self.stdout.write("⚠️  DATABASE_URL not set")
        
        # Show other database-related env vars
        db_vars = ['DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT']
        for var in db_vars:
            if os.getenv(var):
                if options['show_credentials'] or var in ['DB_NAME', 'DB_HOST', 'DB_PORT']:
                    self.stdout.write(f"✅ {var}: {os.getenv(var)}")
                else:
                    self.stdout.write(f"✅ {var}: [HIDDEN]")
            else:
                self.stdout.write(f"❌ {var}: Not set")
        
        self.stdout.write(self.style.SUCCESS('\n🎉 Database connection test completed!'))
