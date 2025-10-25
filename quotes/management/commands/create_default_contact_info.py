from django.core.management.base import BaseCommand
from quotes.models import ContactInfo

class Command(BaseCommand):
    help = 'Create default ContactInfo if none exists'

    def handle(self, *args, **options):
        # Check if any ContactInfo exists
        if not ContactInfo.objects.exists():
            ContactInfo.objects.create(
                email='support@thecleanhandy.com',
                phone='(555) 123-4567',
                address='New York, NY',
                is_active=True
            )
            self.stdout.write(
                self.style.SUCCESS('Successfully created default ContactInfo')
            )
        else:
            self.stdout.write(
                self.style.WARNING('ContactInfo already exists')
            )
