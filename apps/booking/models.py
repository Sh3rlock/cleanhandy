from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.content.models import ServicePage


class Property(models.Model):
    class Kind(models.TextChoices):
        APARTMENT = "apartment", "Apartment"
        HOME = "home", "Home"
        OFFICE = "office", "Office"
        RETAIL = "retail", "Retail"
        OTHER = "other", "Other"

    class Borough(models.TextChoices):
        MANHATTAN = "manhattan", "Manhattan"
        BROOKLYN = "brooklyn", "Brooklyn"
        QUEENS = "queens", "Queens"
        BRONX = "bronx", "Bronx"
        STATEN_ISLAND = "staten_island", "Staten Island"
        LONG_ISLAND = "long_island", "Long Island"
        NEW_JERSEY = "new_jersey", "New Jersey"

    class SqftBand(models.TextChoices):
        UNDER_1000 = "under-1000", "Under 1,000 sq ft"
        BAND_1000 = "1000-1500", "1,000–1,500 sq ft"
        BAND_1500 = "1500-2000", "1,500–2,000 sq ft"
        BAND_2000 = "2000-2500", "2,000–2,500 sq ft"
        BAND_2500 = "2500-3000", "2,500–3,000 sq ft"
        OVER_3000 = "3000-plus", "Over 3,000 sq ft"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="properties",
    )
    label = models.CharField(max_length=120, blank=True)
    street = models.CharField(max_length=200, blank=True)
    unit = models.CharField(max_length=40, blank=True)
    borough = models.CharField(max_length=32, choices=Borough.choices)
    kind = models.CharField(max_length=32, choices=Kind.choices)
    sqft_band = models.CharField(max_length=32, choices=SqftBand.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Properties"
        ordering = ["-created_at"]

    def __str__(self):
        name = self.label or self.get_kind_display()
        return f"{name} ({self.get_borough_display()})"


class DiscountKind(models.TextChoices):
    AMOUNT = "amount", "Amount ($)"
    PERCENT = "percent", "Percent (%)"


class QuoteRequest(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        QUOTED = "quoted", "Quoted"
        SCHEDULED = "scheduled", "Scheduled"
        DECLINED = "declined", "Declined"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="quotes",
    )
    service = models.ForeignKey(ServicePage, on_delete=models.PROTECT, related_name="quotes")
    property = models.ForeignKey(Property, on_delete=models.PROTECT, related_name="quotes")
    destination = models.ForeignKey(
        Property,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="destination_quotes",
    )
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_kind = models.CharField(max_length=16, choices=DiscountKind.choices, default=DiscountKind.AMOUNT)
    discount_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=6, decimal_places=3, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    preferred_date = models.DateField(null=True, blank=True)
    parking_notes = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    email_note = models.TextField(blank=True)
    quote_email_sent_at = models.DateTimeField(null=True, blank=True)
    contact_name = models.CharField(max_length=160)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=32)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.REQUESTED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Quote {self.pk} · {self.service.name}"

    def paid_payment(self):
        return next((payment for payment in self.payments.all() if payment.status == QuotePayment.Status.PAID), None)

    def open_payments(self):
        if self.paid_payment():
            return []
        return [
            payment
            for payment in self.payments.all()
            if payment.status != QuotePayment.Status.PAID and payment.stripe_payment_link_url
        ]


class QuoteEstimate(models.Model):
    quote = models.OneToOneField(QuoteRequest, on_delete=models.CASCADE, related_name="estimate")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    scope = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="estimates_written",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.quote.status == QuoteRequest.Status.REQUESTED:
            self.quote.status = QuoteRequest.Status.QUOTED
            self.quote.save(update_fields=["status"])

    def __str__(self):
        return f"Estimate for quote {self.quote_id}"


class Job(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        QUOTED = "quoted", "Quoted"
        SCHEDULED = "scheduled", "Scheduled"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    quote = models.OneToOneField(QuoteRequest, on_delete=models.PROTECT, related_name="job")
    scheduled_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.SCHEDULED)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Job {self.pk} · {self.quote.service.name}"


class Invoice(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SENT = "sent", "Sent"
        PAID = "paid", "Paid"

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="invoices")
    number = models.CharField(max_length=40, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    issued_on = models.DateField()

    def __str__(self):
        return self.number


class PricingGuideRow(models.Model):
    service = models.ForeignKey(ServicePage, null=True, blank=True, on_delete=models.SET_NULL, related_name="pricing_rows")
    label = models.CharField(max_length=120)
    sqft_band = models.CharField(max_length=40)
    cleaners = models.PositiveSmallIntegerField()
    hours = models.DecimalField(max_digits=4, decimal_places=1)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "label", "sqft_band"]

    def __str__(self):
        return f"{self.label} · {self.sqft_band}"


class PriceVariableCategory(models.Model):
    class InputType(models.TextChoices):
        SINGLE = "single", "Single choice"
        ADDON = "addon", "Optional add-on"

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    input_type = models.CharField(max_length=16, choices=InputType.choices, default=InputType.SINGLE)
    services = models.ManyToManyField(ServicePage, blank=True, related_name="price_categories")
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Price variable category"
        verbose_name_plural = "Price variable categories"

    def __str__(self):
        return self.name


class PriceVariable(models.Model):
    category = models.ForeignKey(PriceVariableCategory, on_delete=models.CASCADE, related_name="variables")
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_kind = models.CharField(max_length=16, choices=DiscountKind.choices, default=DiscountKind.PERCENT)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Price variable"
        verbose_name_plural = "Price variables"
        constraints = [
            models.UniqueConstraint(fields=["category", "name"], name="uniq_price_variable_name"),
        ]

    def __str__(self):
        return f"{self.category.name}: {self.name}"


class TaxSettings(models.Model):
    tax_rate = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        default=Decimal("8.875"),
        help_text="Percent applied to the discounted subtotal. 8.875 means 8.875%.",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Tax settings"
        verbose_name_plural = "Tax settings"

    def __str__(self):
        return f"Tax {self.tax_rate}%"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _created = cls.objects.get_or_create(pk=1, defaults={"tax_rate": Decimal("8.875"), "is_active": True})
        return obj

    @classmethod
    def get_tax_rate(cls):
        obj = cls.load()
        if not obj.is_active:
            return Decimal("0")
        return obj.tax_rate


class QuoteLineItem(models.Model):
    quote = models.ForeignKey(QuoteRequest, on_delete=models.CASCADE, related_name="line_items")
    price_variable = models.ForeignKey(
        PriceVariable,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="quote_lines",
    )
    label = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_kind = models.CharField(max_length=16, choices=DiscountKind.choices, default=DiscountKind.PERCENT)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.label


class QuotePayment(models.Model):
    class Kind(models.TextChoices):
        DEPOSIT = "deposit", "Deposit (50%)"
        FULL = "full", "Full amount"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"

    quote = models.ForeignKey(QuoteRequest, on_delete=models.CASCADE, related_name="payments")
    kind = models.CharField(max_length=16, choices=Kind.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_payment_link_id = models.CharField(max_length=255, blank=True)
    stripe_payment_link_url = models.URLField(blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["kind"]
        constraints = [
            models.UniqueConstraint(fields=["quote", "kind"], name="uniq_quote_payment_kind"),
        ]

    def __str__(self):
        return f"{self.get_kind_display()} for quote {self.quote_id}"


class ConversionEvent(models.Model):
    class Kind(models.TextChoices):
        PHONE = "phone_click", "Phone click"
        EMAIL = "email_click", "Email click"
        QUOTE = "quote_submission", "Quote submission"

    kind = models.CharField(max_length=32, choices=Kind.choices)
    path = models.CharField(max_length=300, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="conversion_events",
    )
    quote = models.ForeignKey(QuoteRequest, null=True, blank=True, on_delete=models.SET_NULL, related_name="events")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.kind} @ {self.path}"
