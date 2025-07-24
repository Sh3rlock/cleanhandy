from django.db import models
from customers.models import Customer  # Import the correct Customer model
from giftcards.models import GiftCard
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
    extra_minutes = models.PositiveIntegerField(default=0, help_text="Add time in minutes (e.g. 30, 60)")

    def __str__(self):
        return f"{self.name} (${self.price})"
    
class HomeType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    extra_minutes = models.PositiveIntegerField(default=180, help_text="Additional time in minutes for this home type")

    def __str__(self):
        return f"{self.name} (${self.price})"

class SquareFeetOption(models.Model):
    label = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"{self.name}"

class Quote(models.Model):
    customer = models.ForeignKey("accounts.CustomerProfile", on_delete=models.CASCADE, null=True, blank=True)
    service = models.ForeignKey("quotes.Service", on_delete=models.CASCADE)
    extras = models.ManyToManyField("CleaningExtra", blank=True)
    home_types = models.ForeignKey("HomeType", on_delete=models.CASCADE, null=True, blank=True)
    square_feet_options = models.ForeignKey("SquareFeetOption", on_delete=models.CASCADE, null=True, blank=True)

     # Cleaning-specific fields
    cleaning_type = models.CharField(max_length=100, null=True, blank=True)
    num_cleaners = models.PositiveIntegerField(null=True, blank=True)

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
        return f"Quote {self.id} - {self.customer.full_name if self.customer else 'No Name'} ({self.status})"
     
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
    
    def is_large_home(self):
        return not self.square_feet_options.name.lower().startswith("under 1000")
    
    def calculate_subtotal(self):
        subtotal = Decimal("0.00")

        if self.square_feet_options:
            subtotal += Decimal(self.square_feet_options.price)

        # ✅ Only include home type price if it's a small home
        if not self.is_large_home() and self.home_types:
            subtotal += Decimal(self.home_types.price)

        # ✅ Extras always apply (for small homes only)
        for extra in self.extras.all():
            subtotal += Decimal(extra.price)

        # ✅ Labor cost only for large homes
        if self.is_large_home() and self.hours_requested and self.num_cleaners:
            rate = Decimal("60") if self.cleaning_type and ("post" in self.cleaning_type.lower() or "renovation" in self.cleaning_type.lower()) else Decimal("55")
            subtotal += Decimal(self.num_cleaners) * Decimal(self.hours_requested) * rate

        return subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


    def calculate_tax(self):
        tax_rate = Decimal("0.08875")
        # ✅ Subtotal already includes labor, no need to add again
        return (self.calculate_subtotal() * tax_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


    def calculate_total_price(self):
        subtotal = self.calculate_subtotal()
        tax = self.calculate_tax()
        return (subtotal + tax).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    

class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
    


class Booking(models.Model):
    service_cat = models.ForeignKey("quotes.ServiceCategory", on_delete=models.CASCADE)
    extras = models.ManyToManyField("CleaningExtra", blank=True)
    home_types = models.ForeignKey("HomeType", on_delete=models.CASCADE, null=True, blank=True)
    square_feet_options = models.ForeignKey("SquareFeetOption", on_delete=models.CASCADE, null=True, blank=True)

     # Cleaning-specific fields
    cleaning_type = models.CharField(max_length=100, null=True, blank=True)
    num_cleaners = models.PositiveIntegerField(null=True, blank=True)

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
            ("confirmed", "Confirmed"),
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

    # Contract Info
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    phone = models.CharField(max_length=15, null=True, blank=True)

     # Address Info
    address = models.CharField(max_length=255, null=True, blank=True)
    apartment = models.CharField(max_length=50, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True, default="New York")
    state = models.CharField(max_length=50, null=True, blank=True, default="NY")
    zip_code = models.CharField(max_length=10, null=True, blank=True)

    # --- New Gift Card fields ---
    gift_card = models.ForeignKey(
        "giftcards.GiftCard", 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="bookings"
    )
    gift_card_discount = models.DecimalField(
        max_digits=8, decimal_places=2, 
        null=True, blank=True, 
        help_text="Amount discounted using gift card."
    )
    
    def __str__(self):
        return f"Booking {self.id} - {self.name if self.name else 'No Name'} ({self.status})"
     
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
    
    def is_large_home(self):
        return not self.square_feet_options.name.lower().startswith("under 1000")
    
    def calculate_subtotal(self):
        subtotal = Decimal("0.00")

        if self.square_feet_options:
            subtotal += Decimal(self.square_feet_options.price)

        # ✅ Only include home type price if it's a small home
        if not self.is_large_home() and self.home_types:
            subtotal += Decimal(self.home_types.price)

        # ✅ Extras always apply (for small homes only)
        for extra in self.extras.all():
            subtotal += Decimal(extra.price)

        # ✅ Labor cost only for large homes
        if self.is_large_home() and self.hours_requested and self.num_cleaners:
            rate = Decimal("60") if self.cleaning_type and ("post" in self.cleaning_type.lower() or "renovation" in self.cleaning_type.lower()) else Decimal("55")
            subtotal += Decimal(self.num_cleaners) * Decimal(self.hours_requested) * rate

        return subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


    def calculate_tax(self):
        tax_rate = Decimal("0.08875")
        # ✅ Subtotal already includes labor, no need to add again
        return (self.calculate_subtotal() * tax_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


    def calculate_total_price(self):
        subtotal = self.calculate_subtotal()
        tax = self.calculate_tax()
        total = subtotal + tax

        if self.gift_card_discount:
            total -= self.gift_card_discount
            if total < 0:
                total = Decimal("0.00")

        return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)





class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Contact from {self.name} <{self.email}>: {self.subject}"





class Review(models.Model):
    booking = models.ForeignKey('Booking', on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    review = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for Booking {self.booking.id} - {self.rating} stars"




