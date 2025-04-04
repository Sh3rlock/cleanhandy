from django.db import models
from customers.models import Customer  # Import the correct Customer model
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

class ServiceCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Service(models.Model):
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name="services")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    base_price = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    service_image = models.ImageField(upload_to='service_images/', blank=True, null=True)
    service_detail_image = models.ImageField(upload_to='service_detail_images/', blank=True, null=True)
    view_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.name}"


class CleaningExtra(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"{self.name} (${self.price})"
    
class HomeType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"{self.name} (${self.price})"

class SquareFeetOption(models.Model):
    label = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"{self.name}"

class Quote(models.Model):
    customer = models.ForeignKey("customers.Customer", on_delete=models.CASCADE, null=True, blank=True)
    service = models.ForeignKey("quotes.Service", on_delete=models.CASCADE)
    extras = models.ManyToManyField("CleaningExtra", blank=True)
    home_types = models.ForeignKey("HomeType", on_delete=models.CASCADE, null=True, blank=True)
    square_feet_options = models.ForeignKey("SquareFeetOption", on_delete=models.CASCADE, null=True, blank=True)

    # System Fields
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    quote_email_sent_at = models.DateTimeField(null=True, blank=True)
    last_admin_note = models.TextField(null=True, blank=True)
    approval_token = models.CharField(max_length=64, blank=True, null=True)
    pdf_file = models.FileField(upload_to="quotes/pdfs/", null=True, blank=True)

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


    # Scheduling
    date = models.DateField()
    hour = models.TimeField()
    hours_requested = models.IntegerField(null=True, blank=True)
    recurrence_pattern = models.CharField(
        max_length=20,
        choices=[
            ("one_time", "One Time"),
            ("weekly", "Weekly"),
            ("biweekly", "Biweekly"),
            ("monthly", "Monthly"),
        ],
        default="one_time",
    )
    job_description = models.TextField(null=True, blank=True)

     # Address Info
    address = models.CharField(max_length=255, null=True, blank=True)
    apartment = models.CharField(max_length=50, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True, default="New York")
    state = models.CharField(max_length=50, null=True, blank=True, default="NY")
    zip_code = models.CharField(max_length=10, null=True, blank=True)
    
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
    
    def calculate_subtotal(self):
        subtotal = Decimal("0.00")

        if self.square_feet_options:
            subtotal += Decimal(self.square_feet_options.price)

        if self.home_types:
            subtotal += Decimal(self.home_types.price)

        for extra in self.extras.all():
            subtotal += Decimal(extra.price)

        return subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calculate_tax(self):
        tax_rate = Decimal("0.08875")
        return (self.calculate_subtotal() * tax_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calculate_total_price(self):
        subtotal = self.calculate_subtotal()
        tax = self.calculate_tax()
        return (subtotal + tax).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
