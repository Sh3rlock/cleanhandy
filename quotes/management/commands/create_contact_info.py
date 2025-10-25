from django.core.management.base import BaseCommand
from quotes.models import ContactInfo

class Command(BaseCommand):
    help = 'Create initial contact information'

    def handle(self, *args, **options):
        # Check if contact info already exists
        if ContactInfo.objects.filter(is_active=True).exists():
            self.stdout.write(
                self.style.WARNING('Contact information already exists. Skipping creation.')
            )
            return

        # Create initial contact information
        contact_info = ContactInfo.objects.create(
            email='support@thecleanhandy.com',
            phone='+1 516 619 3065',
            address='31-85 Crescent St, Astoria, NY 11106',
            is_active=True
        )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created contact information: {contact_info}')
        ) 