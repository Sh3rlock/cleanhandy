from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import connection
import os

class Command(BaseCommand):
    help = 'Create a Django superuser for Railway PostgreSQL database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Username for the superuser (default: admin)',
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@thecleanhandy.com',
            help='Email for the superuser (default: admin@thecleanhandy.com)',
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123',
            help='Password for the superuser (default: admin123)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force creation even if superuser already exists',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Creating Django superuser for Railway...'))
        
        # Check database connection
        self.check_database_connection()
        
        # Create superuser
        self.create_superuser(options)
        
        self.stdout.write(self.style.SUCCESS('✅ Superuser creation completed!'))

    def check_database_connection(self):
        """Check if database connection is working"""
        self.stdout.write('🔍 Checking database connection...')
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                self.stdout.write(self.style.SUCCESS('✅ Database connection successful!'))
                
                # Show database info
                db_config = connection.settings_dict
                self.stdout.write(f"📊 Database: {db_config['NAME']}")
                self.stdout.write(f"🏠 Host: {db_config.get('HOST', 'localhost')}")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Database connection failed: {e}'))
            self.stdout.write('💡 Make sure your DATABASE_URL is correctly set in Railway environment variables')
            raise

    def create_superuser(self, options):
        """Create the superuser"""
        User = get_user_model()
        username = options['username']
        email = options['email']
        password = options['password']
        force = options['force']
        
        # Check if superuser already exists
        if User.objects.filter(is_superuser=True).exists():
            if not force:
                self.stdout.write(self.style.WARNING('⚠️  Superuser already exists!'))
                self.stdout.write('💡 Use --force to create another superuser')
                return
            else:
                self.stdout.write('🔄 Force mode: Creating additional superuser...')
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(f'❌ Username "{username}" already exists!'))
            self.stdout.write('💡 Choose a different username or use --force')
            return
        
        try:
            # Create superuser
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            
            self.stdout.write(self.style.SUCCESS(f'✅ Superuser created successfully!'))
            self.stdout.write(f'👤 Username: {username}')
            self.stdout.write(f'📧 Email: {email}')
            self.stdout.write(f'🔑 Password: {password}')
            self.stdout.write('')
            self.stdout.write('🌐 You can now access Django admin at:')
            self.stdout.write('   https://your-railway-app.up.railway.app/admin/')
            self.stdout.write('')
            self.stdout.write('⚠️  Remember to change the password after first login!')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Failed to create superuser: {e}'))
            raise

    def show_environment_info(self):
        """Show relevant environment information"""
        self.stdout.write('\n🔧 Environment Information:')
        
        # Check if we're on Railway
        if os.getenv('RAILWAY_ENVIRONMENT'):
            self.stdout.write(f'🚂 Railway Environment: {os.getenv("RAILWAY_ENVIRONMENT")}')
        
        # Check DATABASE_URL
        if os.getenv('DATABASE_URL'):
            self.stdout.write('✅ DATABASE_URL is set')
        else:
            self.stdout.write('❌ DATABASE_URL not set')
        
        # Show other relevant env vars
        env_vars = ['SECRET_KEY', 'DEBUG', 'ALLOWED_HOSTS']
        for var in env_vars:
            value = os.getenv(var)
            if value:
                if var == 'SECRET_KEY':
                    self.stdout.write(f'✅ {var}: [HIDDEN]')
                else:
                    self.stdout.write(f'✅ {var}: {value}')
            else:
                self.stdout.write(f'❌ {var}: Not set')
