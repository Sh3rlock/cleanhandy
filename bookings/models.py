from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class ServiceType(models.Model):
    """Service type (Home Cleaning, Office Cleaning)"""
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name


class ExtraService(models.Model):
    """Extra services that can be added to bookings"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    base_price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    is_time_based = models.BooleanField(default=False)
    time_minutes = models.IntegerField(default=0, help_text="Time in minutes if time-based")
    icon = models.CharField(max_length=50, blank=True, help_text="CSS class or icon identifier")
    
    def __str__(self):
        return self.name


class Booking(models.Model):
    """Main booking model"""
    
    # Service Details (Step 1)
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE)
    
    # Home Cleaning specific fields
    bedrooms = models.CharField(max_length=50, choices=[
        ('studio_500', 'Studio (<500 Sq Ft)'),
        ('studio_1000', 'Studio (500-1000 Sq Ft)'),
        ('1_bedroom', '1 Bedroom'),
        ('2_bedrooms', '2 Bedrooms'),
        ('3_bedrooms', '3 Bedrooms'),
        ('4_bedrooms', '4 Bedrooms'),
        ('5_plus_bedrooms', '5+ Bedrooms'),
    ], blank=True, null=True)
    bathrooms = models.CharField(max_length=50, choices=[
        ('1_bathroom', '1 Bathroom'),
        ('2_bathrooms', '2 Bathrooms'),
        ('3_bathrooms', '3 Bathrooms'),
        ('4_plus_bathrooms', '4+ Bathrooms'),
    ], blank=True, null=True)
    cleaning_type = models.CharField(max_length=50, choices=[
        ('standard', 'Standard Cleaning'),
        ('deep', 'Deep Cleaning'),
    ], blank=True, null=True)
    has_pets = models.CharField(max_length=50, choices=[
        ('no_pets', 'No Pets'),
        ('has_pets', 'Yes, I have pets'),
    ], blank=True, null=True)
    
    # Office Cleaning specific fields
    business_type = models.CharField(max_length=50, choices=[
        ('office', 'Office'),
        ('retail', 'Retail'),
        ('medical', 'Medical'),
        ('school', 'School'),
        ('other', 'Other'),
    ], blank=True, null=True)
    crew_size_hours = models.CharField(max_length=100, choices=[
        ('1_cleaner_2_hours_500', '1 Cleaner Total 2 Hours (<500 Sq Ft)'),
        ('1_cleaner_3_hours_1000', '1 Cleaner Total 3 Hours (500-1000 Sq Ft)'),
        ('1_cleaner_4_hours_1500', '1 Cleaner Total 4 Hours (1000-1500 Sq Ft)'),
        ('2_cleaners_3_hours_2000', '2 Cleaners Total 3 Hours (1500-2000 Sq Ft)'),
        ('2_cleaners_4_hours_2500', '2 Cleaners Total 4 Hours (2000-2500 Sq Ft)'),
        ('2_cleaners_5_hours_3000', '2 Cleaners Total 5 Hours (2500-3000 Sq Ft)'),
        ('3_cleaners_4_hours_4000', '3 Cleaners Total 4 Hours (3000-4000 Sq Ft)'),
        ('3_cleaners_5_hours_5000', '3 Cleaners Total 5 Hours (4000-5000 Sq Ft)'),
        ('custom', 'Custom - Contact for Quote'),
    ], blank=True, null=True)
    
    # Office space quantities
    num_restrooms = models.PositiveIntegerField(default=0, blank=True, null=True)
    num_kitchen_areas = models.PositiveIntegerField(default=0, blank=True, null=True)
    num_conference_rooms = models.PositiveIntegerField(default=0, blank=True, null=True)
    num_private_offices = models.PositiveIntegerField(default=0, blank=True, null=True)
    
    # Extra Services (Step 2)
    extra_services = models.ManyToManyField(ExtraService, blank=True)
    
    # Additional Details
    additional_details = models.TextField(blank=True)
    
    # Frequency (Step 3)
    FREQUENCY_CHOICES = [
        ('one_time', 'One time'),
        ('weekly', 'Weekly - 15% Off'),
        ('bi_weekly', 'Bi Weekly - 10% Off'),
        ('monthly', 'Monthly - 5% Off'),
    ]
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='one_time')
    
    # Date and Time (Step 4)
    date_of_service = models.DateField()
    time_slot = models.TimeField()
    timezone_choice = models.CharField(max_length=20, choices=[
        ('company', 'Our Company\'s'),
        ('user', 'Yours'),
    ], default='user')
    
    # Contact Information (Step 5)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_country_code = models.CharField(max_length=10, default='+1')
    phone_number = models.CharField(max_length=20)
    access_method = models.CharField(max_length=50, choices=[
        ('at_home', 'I\'ll be at home'),
        ('key_under_mat', 'Key under mat'),
        ('doorman', 'Doorman'),
        ('lockbox', 'Lockbox'),
        ('other', 'Other'),
    ], default='at_home')
    referral_source = models.CharField(max_length=100, blank=True)
    
    # Location (Step 6)
    street_address = models.CharField(max_length=255)
    unit_apt_suite = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=20)
    
    # Booking Status and Metadata
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Pricing
    base_price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    extra_services_total = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Terms acceptance
    terms_accepted = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Booking {self.id} - {self.first_name} {self.last_name} - {self.date_of_service}"
    
    def calculate_total_price(self):
        """Calculate total price including extras and discounts"""
        total = self.base_price + self.extra_services_total
        
        # Apply frequency discount
        if self.frequency == 'weekly':
            self.discount_amount = total * Decimal('0.15')
        elif self.frequency == 'bi_weekly':
            self.discount_amount = total * Decimal('0.10')
        elif self.frequency == 'monthly':
            self.discount_amount = total * Decimal('0.05')
        else:
            self.discount_amount = Decimal('0.00')
        
        self.total_price = total - self.discount_amount
        return self.total_price


class TimeSlot(models.Model):
    """Available time slots for bookings"""
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE)
    day_of_week = models.IntegerField(choices=[
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ])
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['service_type', 'day_of_week', 'start_time']
    
    def __str__(self):
        return f"{self.get_day_of_week_display()} {self.start_time}-{self.end_time}"

