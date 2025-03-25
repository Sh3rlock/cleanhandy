from django.db import models
from customers.models import Customer  # Import the correct Customer model
from datetime import datetime, timedelta

class ServiceCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Service(models.Model):
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name="services")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.category.name} - {self.name}"

class CleaningExtra(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"{self.name} (${self.price})"

class Quote(models.Model):
    customer = models.ForeignKey("customers.Customer", on_delete=models.CASCADE, null=True, blank=True)
    service = models.ForeignKey("quotes.Service", on_delete=models.CASCADE)
    zip_code = models.CharField(max_length=10, null=True, blank=True)
    job_description = models.TextField(null=True, blank=True)
    date = models.DateField()
    hour = models.TimeField()
    hours_requested = models.IntegerField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    quote_email_sent_at = models.DateTimeField(null=True, blank=True)
    last_admin_note = models.TextField(null=True, blank=True)
    approval_token = models.CharField(max_length=64, blank=True, null=True)
    
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("declined", "Declined"),
            ("accepted", "Accepted"),
            ("booked", "Booked"),
            ("expired", "Expired"),
        ],
        default="pending",
    )

    home_type = models.CharField(
        max_length=50,
        choices=[
            ("apartment", "Apartment"),
            ("house", "House"),
            ("studio", "Studio"),
            ("other", "Other"),
        ],
        null=True,
        blank=True,
    )
    square_feet = models.PositiveIntegerField(null=True, blank=True)
    num_bedrooms = models.PositiveIntegerField(null=True, blank=True)
    num_bathrooms = models.PositiveIntegerField(null=True, blank=True)
    is_recurring = models.BooleanField(default=False)  # Recurring toggle

    # Price calculation extras (optional, see model below)
    extras = models.ManyToManyField("CleaningExtra", blank=True)

    def __str__(self):
        return f"Quote {self.id} - {self.customer.name if self.customer else 'No Name'} ({self.status})"

    def get_time_slots(self):
        """
        Returns a list of hourly time slot strings based on the starting hour and requested duration.
        Ensures at least 2 hours are used even if `hours_requested` is null or less.
        """
        if not self.hour:
            return []

        duration = max(self.hours_requested or 2, 2)
        slots = []

        base_datetime = datetime.combine(self.date, self.hour)
        for i in range(duration):
            start = base_datetime + timedelta(hours=i)
            end = base_datetime + timedelta(hours=i + 1)
            slots.append(f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}")
        
        return slots
    
    def calculate_total_price(self):
        base_price = 50  # or per sqft or room logic
        sqft_price = 0.15 * (self.square_feet or 0)
        bedroom_price = 10 * (self.num_bedrooms or 0)
        bathroom_price = 12 * (self.num_bathrooms or 0)
        extras_price = sum(extra.price for extra in self.extras.all())

        total = base_price + sqft_price + bedroom_price + bathroom_price + extras_price
        return round(total, 2)
