from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
import os
import json

class Command(BaseCommand):
    help = 'Migrate data from SQLite to PostgreSQL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--export-only',
            action='store_true',
            help='Only export data from SQLite, do not import to PostgreSQL',
        )
        parser.add_argument(
            '--import-only',
            action='store_true',
            help='Only import data to PostgreSQL from existing export file',
        )

    def handle(self, *args, **options):
        if options['import_only']:
            self.import_data()
        elif options['export_only']:
            self.export_data()
        else:
            self.export_data()
            self.import_data()

    def export_data(self):
        """Export data from current database (SQLite)"""
        self.stdout.write(self.style.SUCCESS('📤 Exporting data from current database...'))
        
        try:
            # Export data to JSON file
            with open('data_export.json', 'w') as f:
                call_command('dumpdata', 
                           '--natural-foreign', 
                           '--natural-primary',
                           '--exclude=contenttypes',
                           '--exclude=auth.Permission',
                           '--exclude=sessions.Session',
                           stdout=f)
            
            self.stdout.write(self.style.SUCCESS('✅ Data exported to data_export.json'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error exporting data: {e}'))

    def import_data(self):
        """Import data to PostgreSQL"""
        self.stdout.write(self.style.SUCCESS('📥 Importing data to PostgreSQL...'))
        
        # Check if DATABASE_URL is set (indicates PostgreSQL)
        if not os.getenv('DATABASE_URL'):
            self.stdout.write(self.style.WARNING('⚠️  DATABASE_URL not found. Make sure PostgreSQL is configured.'))
            return
        
        # Check if export file exists
        if not os.path.exists('data_export.json'):
            self.stdout.write(self.style.ERROR('❌ data_export.json not found. Run export first.'))
            return
        
        try:
            # Import data from JSON file
            call_command('loaddata', 'data_export.json')
            self.stdout.write(self.style.SUCCESS('✅ Data imported successfully to PostgreSQL'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error importing data: {e}'))
