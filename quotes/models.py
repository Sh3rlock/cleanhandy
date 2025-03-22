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
