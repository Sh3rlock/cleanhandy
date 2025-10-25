#!/usr/bin/env python
"""
Migration script to transfer data from SQLite to PostgreSQL
Run this script after setting up PostgreSQL on Railway
"""

import os
import sys
import django
from django.conf import settings
from django.core.management import execute_from_command_line

def setup_django():
    """Setup Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cleanhandy.settings')
    django.setup()

def export_sqlite_data():
    """Export data from SQLite database"""
    print("📤 Exporting data from SQLite database...")
    
    # Create a temporary settings file for SQLite export
    sqlite_settings = """
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-b@l@av@rh*6)xlvgfrhu0a+*h9#l9pb&zdebab*+$(mkg)d73w')
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'quotes',
    'bookings',
    'customers',
    'adminpanel',
    'blog',
    'accounts',
    'giftcards',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'cleanhandy.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'quotes' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'cleanhandy.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = ['static/']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
"""
    
    # Write temporary settings file
    with open('temp_sqlite_settings.py', 'w') as f:
        f.write(sqlite_settings)
    
    # Export data using SQLite settings
    os.environ['DJANGO_SETTINGS_MODULE'] = 'temp_sqlite_settings'
    django.setup()
    
    # Run dumpdata command
    from django.core.management import call_command
    from io import StringIO
    
    output = StringIO()
    call_command('dumpdata', 
                 '--natural-foreign', 
                 '--natural-primary',
                 '--exclude=contenttypes',
                 '--exclude=auth.Permission',
                 '--exclude=sessions.Session',
                 stdout=output)
    
    # Save to file
    with open('data_export.json', 'w') as f:
        f.write(output.getvalue())
    
    print("✅ Data exported to data_export.json")
    
    # Clean up
    os.remove('temp_sqlite_settings.py')
    if os.path.exists('temp_sqlite_settings.pyc'):
        os.remove('temp_sqlite_settings.pyc')

def import_postgres_data():
    """Import data to PostgreSQL database"""
    print("📥 Importing data to PostgreSQL database...")
    
    # Check if DATABASE_URL is set
    if not os.getenv('DATABASE_URL'):
        print("❌ DATABASE_URL not found. Make sure PostgreSQL is configured on Railway.")
        return False
    
    # Reset Django settings
    os.environ['DJANGO_SETTINGS_MODULE'] = 'cleanhandy.settings'
    django.setup()
    
    # Run loaddata command
    from django.core.management import call_command
    
    try:
        call_command('loaddata', 'data_export.json')
        print("✅ Data imported successfully to PostgreSQL")
        return True
    except Exception as e:
        print(f"❌ Error importing data: {e}")
        return False

def main():
    """Main migration function"""
    print("🚀 Starting SQLite to PostgreSQL migration...")
    
    # Check if data export file exists
    if not os.path.exists('data_export.json'):
        print("📤 Data export file not found. Exporting from SQLite...")
        export_sqlite_data()
    
    # Import to PostgreSQL
    if import_postgres_data():
        print("🎉 Migration completed successfully!")
        print("\nNext steps:")
        print("1. Test your application on Railway")
        print("2. Verify all data is correctly migrated")
        print("3. Remove data_export.json file for security")
    else:
        print("❌ Migration failed. Check the errors above.")

if __name__ == '__main__':
    main()
