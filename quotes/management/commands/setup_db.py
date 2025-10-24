from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
import time

class Command(BaseCommand):
    help = 'Setup database with migrations and initial data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force setup even if tables exist',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Starting database setup...'))
        
        # Wait for database connection
        self.wait_for_db()
        
        # Run migrations
        self.run_migrations()
        
        # Create superuser if needed
        self.create_superuser()
        
        self.stdout.write(self.style.SUCCESS('✅ Database setup completed!'))

    def wait_for_db(self):
        """Wait for database to be ready"""
        self.stdout.write('⏳ Waiting for database connection...')
        max_attempts = 30
        attempt = 0
        
        while attempt < max_attempts:
            try:
                connection.ensure_connection()
                self.stdout.write(self.style.SUCCESS('✅ Database connection successful!'))
                return
            except Exception as e:
                attempt += 1
                self.stdout.write(f'⏳ Database connection attempt {attempt}/{max_attempts} failed: {e}')
                if attempt < max_attempts:
                    time.sleep(2)
                else:
                    self.stdout.write(self.style.ERROR('❌ Failed to connect to database after 30 attempts'))
                    raise

    def run_migrations(self):
        """Run database migrations"""
        self.stdout.write('📊 Running database migrations...')
        try:
            call_command('migrate', verbosity=2)
            self.stdout.write(self.style.SUCCESS('✅ Migrations completed successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Migration failed: {e}'))
            raise

    def create_superuser(self):
        """Create superuser if none exists"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if not User.objects.filter(is_superuser=True).exists():
            self.stdout.write('👤 Creating superuser...')
            try:
                User.objects.create_superuser(
                    username='admin',
                    email='admin@thecleanhandy.com',
                    password='admin123'
                )
                self.stdout.write(self.style.SUCCESS('✅ Superuser created: admin/admin123'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'⚠️  Could not create superuser: {e}'))
        else:
            self.stdout.write('👤 Superuser already exists')
