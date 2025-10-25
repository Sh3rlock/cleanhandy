from django.core.management.base import BaseCommand
from django.utils import timezone
from bookings.models import ServiceType, ExtraService, TimeSlot
from datetime import time


class Command(BaseCommand):
    help = 'Populate initial data for the booking system'

    def handle(self, *args, **options):
        self.stdout.write('Creating initial booking data...')
        
        # Create Service Types
        home_cleaning, created = ServiceType.objects.get_or_create(
            name='Home Cleaning',
            defaults={'description': 'Professional residential cleaning services'}
        )
        if created:
            self.stdout.write(f'Created service type: {home_cleaning.name}')
        
        office_cleaning, created = ServiceType.objects.get_or_create(
            name='Office Cleaning',
            defaults={'description': 'Commercial cleaning services for offices and businesses'}
        )
        if created:
            self.stdout.write(f'Created service type: {office_cleaning.name}')
        
        # Create Extra Services
        extra_services_data = [
            {
                'name': 'Go Green - Free Upgrade',
                'description': 'Eco-friendly cleaning products at no additional cost',
                'base_price': 0.00,
                'is_time_based': False,
                'icon': 'fas fa-leaf'
            },
            {
                'name': 'Inside of fridge',
                'description': 'Deep cleaning of refrigerator interior',
                'base_price': 25.00,
                'is_time_based': False,
                'icon': 'fas fa-snowflake'
            },
            {
                'name': 'Inside of oven',
                'description': 'Deep cleaning of oven interior',
                'base_price': 35.00,
                'is_time_based': False,
                'icon': 'fas fa-fire'
            },
            {
                'name': 'Interior Kitchen Cabinets (Empty)',
                'description': 'Cleaning inside kitchen cabinets (must be empty)',
                'base_price': 30.00,
                'is_time_based': False,
                'icon': 'fas fa-door-open'
            },
            {
                'name': 'Laundry (wash & fold)',
                'description': 'Washing and folding laundry service',
                'base_price': 40.00,
                'is_time_based': False,
                'icon': 'fas fa-tshirt'
            },
            {
                'name': 'Organizing/Packing (30 Min)',
                'description': 'Organizing and packing services, 30 minutes',
                'base_price': 45.00,
                'is_time_based': True,
                'time_minutes': 30,
                'icon': 'fas fa-boxes'
            },
            {
                'name': 'Inside Windows (30 Min)',
                'description': 'Interior window cleaning, 30 minutes',
                'base_price': 35.00,
                'is_time_based': True,
                'time_minutes': 30,
                'icon': 'fas fa-window-maximize'
            },
            {
                'name': 'Pet Hair Removal',
                'description': 'Specialized pet hair removal service',
                'base_price': 30.00,
                'is_time_based': False,
                'icon': 'fas fa-paw'
            },
            {
                'name': 'Post Construction Equipment (HEPA)',
                'description': 'HEPA filtration cleaning for post-construction',
                'base_price': 75.00,
                'is_time_based': False,
                'icon': 'fas fa-vacuum-robot'
            },
            {
                'name': 'Wall washing (60 min)',
                'description': 'Wall washing service, 60 minutes',
                'base_price': 60.00,
                'is_time_based': True,
                'time_minutes': 60,
                'icon': 'fas fa-border-style'
            },
            {
                'name': 'Extra/Deep Bathroom',
                'description': 'Extra deep bathroom cleaning',
                'base_price': 45.00,
                'is_time_based': False,
                'icon': 'fas fa-bath'
            },
            {
                'name': 'Hand Wash Dishes',
                'description': 'Hand washing dishes service',
                'base_price': 25.00,
                'is_time_based': False,
                'icon': 'fas fa-hand-sparkles'
            },
            {
                'name': 'Furniture & Carpet Cleaning (Request Quote)',
                'description': 'Furniture and carpet cleaning - custom pricing',
                'base_price': 0.00,
                'is_time_based': False,
                'icon': 'fas fa-couch'
            },
            {
                'name': 'Patio or Balcony',
                'description': 'Outdoor patio or balcony cleaning',
                'base_price': 40.00,
                'is_time_based': False,
                'icon': 'fas fa-umbrella-beach'
            },
            {
                'name': 'Baseboards & Radiators',
                'description': 'Cleaning baseboards and radiators',
                'base_price': 35.00,
                'is_time_based': False,
                'icon': 'fas fa-thermometer-half'
            },
            {
                'name': 'Airbnb Package',
                'description': 'Specialized cleaning for Airbnb properties',
                'base_price': 85.00,
                'is_time_based': False,
                'icon': 'fas fa-home'
            }
        ]
        
        for service_data in extra_services_data:
            service, created = ExtraService.objects.get_or_create(
                name=service_data['name'],
                defaults=service_data
            )
            if created:
                self.stdout.write(f'Created extra service: {service.name}')
        
        # Create Time Slots for Home Cleaning
        home_time_slots = [
            # Monday - Friday: 8 AM - 6 PM
            {'day': 0, 'start': time(8, 0), 'end': time(9, 0)},
            {'day': 0, 'start': time(9, 0), 'end': time(10, 0)},
            {'day': 0, 'start': time(10, 0), 'end': time(11, 0)},
            {'day': 0, 'start': time(11, 0), 'end': time(12, 0)},
            {'day': 0, 'start': time(12, 0), 'end': time(13, 0)},
            {'day': 0, 'start': time(13, 0), 'end': time(14, 0)},
            {'day': 0, 'start': time(14, 0), 'end': time(15, 0)},
            {'day': 0, 'start': time(15, 0), 'end': time(16, 0)},
            {'day': 0, 'start': time(16, 0), 'end': time(17, 0)},
            {'day': 0, 'start': time(17, 0), 'end': time(18, 0)},
            
            # Tuesday
            {'day': 1, 'start': time(8, 0), 'end': time(9, 0)},
            {'day': 1, 'start': time(9, 0), 'end': time(10, 0)},
            {'day': 1, 'start': time(10, 0), 'end': time(11, 0)},
            {'day': 1, 'start': time(11, 0), 'end': time(12, 0)},
            {'day': 1, 'start': time(12, 0), 'end': time(13, 0)},
            {'day': 1, 'start': time(13, 0), 'end': time(14, 0)},
            {'day': 1, 'start': time(14, 0), 'end': time(15, 0)},
            {'day': 1, 'start': time(15, 0), 'end': time(16, 0)},
            {'day': 1, 'start': time(16, 0), 'end': time(17, 0)},
            {'day': 1, 'start': time(17, 0), 'end': time(18, 0)},
            
            # Wednesday
            {'day': 2, 'start': time(8, 0), 'end': time(9, 0)},
            {'day': 2, 'start': time(9, 0), 'end': time(10, 0)},
            {'day': 2, 'start': time(10, 0), 'end': time(11, 0)},
            {'day': 2, 'start': time(11, 0), 'end': time(12, 0)},
            {'day': 2, 'start': time(12, 0), 'end': time(13, 0)},
            {'day': 2, 'start': time(13, 0), 'end': time(14, 0)},
            {'day': 2, 'start': time(14, 0), 'end': time(15, 0)},
            {'day': 2, 'start': time(15, 0), 'end': time(16, 0)},
            {'day': 2, 'start': time(16, 0), 'end': time(17, 0)},
            {'day': 2, 'start': time(17, 0), 'end': time(18, 0)},
            
            # Thursday
            {'day': 3, 'start': time(8, 0), 'end': time(9, 0)},
            {'day': 3, 'start': time(9, 0), 'end': time(10, 0)},
            {'day': 3, 'start': time(10, 0), 'end': time(11, 0)},
            {'day': 3, 'start': time(11, 0), 'end': time(12, 0)},
            {'day': 3, 'start': time(12, 0), 'end': time(13, 0)},
            {'day': 3, 'start': time(13, 0), 'end': time(14, 0)},
            {'day': 3, 'start': time(14, 0), 'end': time(15, 0)},
            {'day': 3, 'start': time(15, 0), 'end': time(16, 0)},
            {'day': 3, 'start': time(16, 0), 'end': time(17, 0)},
            {'day': 3, 'start': time(17, 0), 'end': time(18, 0)},
            
            # Friday
            {'day': 4, 'start': time(8, 0), 'end': time(9, 0)},
            {'day': 4, 'start': time(9, 0), 'end': time(10, 0)},
            {'day': 4, 'start': time(10, 0), 'end': time(11, 0)},
            {'day': 4, 'start': time(11, 0), 'end': time(12, 0)},
            {'day': 4, 'start': time(12, 0), 'end': time(13, 0)},
            {'day': 4, 'start': time(13, 0), 'end': time(14, 0)},
            {'day': 4, 'start': time(14, 0), 'end': time(15, 0)},
            {'day': 4, 'start': time(15, 0), 'end': time(16, 0)},
            {'day': 4, 'start': time(16, 0), 'end': time(17, 0)},
            {'day': 4, 'start': time(17, 0), 'end': time(18, 0)},
            
            # Saturday: Extended hours
            {'day': 5, 'start': time(8, 0), 'end': time(9, 0)},
            {'day': 5, 'start': time(9, 0), 'end': time(10, 0)},
            {'day': 5, 'start': time(10, 0), 'end': time(11, 0)},
            {'day': 5, 'start': time(11, 0), 'end': time(12, 0)},
            {'day': 5, 'start': time(12, 0), 'end': time(13, 0)},
            {'day': 5, 'start': time(13, 0), 'end': time(14, 0)},
            {'day': 5, 'start': time(14, 0), 'end': time(15, 0)},
            {'day': 5, 'start': time(15, 0), 'end': time(16, 0)},
            {'day': 5, 'start': time(16, 0), 'end': time(17, 0)},
            {'day': 5, 'start': time(17, 0), 'end': time(18, 0)},
            
            # Sunday: Limited hours
            {'day': 6, 'start': time(10, 0), 'end': time(11, 0)},
            {'day': 6, 'start': time(11, 0), 'end': time(12, 0)},
            {'day': 6, 'start': time(12, 0), 'end': time(13, 0)},
            {'day': 6, 'start': time(13, 0), 'end': time(14, 0)},
            {'day': 6, 'start': time(14, 0), 'end': time(15, 0)},
            {'day': 6, 'start': time(15, 0), 'end': time(16, 0)},
        ]
        
        for slot_data in home_time_slots:
            slot, created = TimeSlot.objects.get_or_create(
                service_type=home_cleaning,
                day_of_week=slot_data['day'],
                start_time=slot_data['start'],
                defaults={'end_time': slot_data['end'], 'is_available': True}
            )
            if created:
                self.stdout.write(f'Created time slot: {slot}')
        
        # Create Time Slots for Office Cleaning (business hours only)
        office_time_slots = [
            # Monday - Friday: 6 PM - 8 PM (after business hours)
            {'day': 0, 'start': time(18, 0), 'end': time(19, 0)},
            {'day': 0, 'start': time(19, 0), 'end': time(20, 0)},
            {'day': 1, 'start': time(18, 0), 'end': time(19, 0)},
            {'day': 1, 'start': time(19, 0), 'end': time(20, 0)},
            {'day': 2, 'start': time(18, 0), 'end': time(19, 0)},
            {'day': 2, 'start': time(19, 0), 'end': time(20, 0)},
            {'day': 3, 'start': time(18, 0), 'end': time(19, 0)},
            {'day': 3, 'start': time(19, 0), 'end': time(20, 0)},
            {'day': 4, 'start': time(18, 0), 'end': time(19, 0)},
            {'day': 4, 'start': time(19, 0), 'end': time(20, 0)},
            
            # Saturday: Morning hours
            {'day': 5, 'start': time(8, 0), 'end': time(9, 0)},
            {'day': 5, 'start': time(9, 0), 'end': time(10, 0)},
            {'day': 5, 'start': time(10, 0), 'end': time(11, 0)},
            {'day': 5, 'start': time(11, 0), 'end': time(12, 0)},
        ]
        
        for slot_data in office_time_slots:
            slot, created = TimeSlot.objects.get_or_create(
                service_type=office_cleaning,
                day_of_week=slot_data['day'],
                start_time=slot_data['start'],
                defaults={'end_time': slot_data['end'], 'is_available': True}
            )
            if created:
                self.stdout.write(f'Created office time slot: {slot}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully populated initial booking data!')
        )
        self.stdout.write(f'Created {ServiceType.objects.count()} service types')
        self.stdout.write(f'Created {ExtraService.objects.count()} extra services')
        self.stdout.write(f'Created {TimeSlot.objects.count()} time slots')
