from django.core.management.base import BaseCommand
from quotes.models import HourlyRate
from decimal import Decimal


class Command(BaseCommand):
    help = 'Set up initial hourly rates for different service types'

    def handle(self, *args, **options):
        # Define initial hourly rates
        initial_rates = [
            {
                'service_type': 'office_cleaning',
                'hourly_rate': Decimal('75.00'),
                'description': 'Standard office cleaning service rate per cleaner per hour'
            },
            {
                'service_type': 'home_cleaning',
                'hourly_rate': Decimal('55.00'),
                'description': 'Standard home cleaning service rate per cleaner per hour'
            },
            {
                'service_type': 'post_renovation',
                'hourly_rate': Decimal('60.00'),
                'description': 'Post-renovation cleaning service rate per cleaner per hour'
            },
            {
                'service_type': 'construction',
                'hourly_rate': Decimal('60.00'),
                'description': 'Construction site cleaning service rate per cleaner per hour'
            },
            {
                'service_type': 'move_in_out',
                'hourly_rate': Decimal('65.00'),
                'description': 'Move in/out cleaning service rate per cleaner per hour'
            },
            {
                'service_type': 'deep_cleaning',
                'hourly_rate': Decimal('70.00'),
                'description': 'Deep cleaning service rate per cleaner per hour'
            },
            {
                'service_type': 'regular_cleaning',
                'hourly_rate': Decimal('55.00'),
                'description': 'Regular maintenance cleaning service rate per cleaner per hour'
            },
        ]

        created_count = 0
        updated_count = 0

        for rate_data in initial_rates:
            rate, created = HourlyRate.objects.get_or_create(
                service_type=rate_data['service_type'],
                defaults={
                    'hourly_rate': rate_data['hourly_rate'],
                    'description': rate_data['description'],
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created hourly rate for {rate.get_service_type_display()}: ${rate.hourly_rate}/hour'
                    )
                )
            else:
                # Update existing rate if it exists
                if rate.hourly_rate != rate_data['hourly_rate'] or rate.description != rate_data['description']:
                    rate.hourly_rate = rate_data['hourly_rate']
                    rate.description = rate_data['description']
                    rate.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'Updated hourly rate for {rate.get_service_type_display()}: ${rate.hourly_rate}/hour'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully set up hourly rates. Created: {created_count}, Updated: {updated_count}'
            )
        )
        
        # Display all current rates
        self.stdout.write('\nCurrent hourly rates:')
        for rate in HourlyRate.objects.filter(is_active=True).order_by('service_type'):
            self.stdout.write(
                f'  {rate.get_service_type_display()}: ${rate.hourly_rate}/hour'
            )
