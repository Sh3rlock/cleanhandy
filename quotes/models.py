from django.db import models
from customers.models import Customer  # Import the correct Customer model

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
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("declined", "Declined"),
        ("accepted", "Accepted"),
        ("expired", "Expired"),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)
    service = models.ForeignKey("quotes.Service", on_delete=models.CASCADE)
    date = models.DateTimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    # Cleaning-specific fields
    num_bedrooms = models.PositiveIntegerField(null=True, blank=True)
    square_feet = models.PositiveIntegerField(null=True, blank=True)

    # Handyman-specific field
    hours_requested = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"Quote {self.id} - {self.customer.name if self.customer else 'No Customer'} ({self.status})"
