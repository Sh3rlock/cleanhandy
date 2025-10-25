from django.core.management.base import BaseCommand
from django.db import connection
from django.core.exceptions import ImproperlyConfigured

class Command(BaseCommand):
    help = 'Check database connection and table status'

    def handle(self, *args, **options):
        try:
            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                self.stdout.write(self.style.SUCCESS('✅ Database connection successful'))
            
            # Check if migrations have been run
            cursor = connection.cursor()
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'quotes_%'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            
            if tables:
                self.stdout.write(self.style.SUCCESS(f'✅ Found {len(tables)} quotes tables:'))
                for table in tables:
                    self.stdout.write(f'  - {table[0]}')
            else:
                self.stdout.write(self.style.WARNING('⚠️  No quotes tables found. Run migrations first.'))
                
            # Check for ContactInfo table specifically
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'quotes_contactinfo'
                );
            """)
            contactinfo_exists = cursor.fetchone()[0]
            
            if contactinfo_exists:
                self.stdout.write(self.style.SUCCESS('✅ quotes_contactinfo table exists'))
            else:
                self.stdout.write(self.style.ERROR('❌ quotes_contactinfo table does not exist'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Database error: {e}'))
