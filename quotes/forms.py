from django import forms
from .models import Quote, Service, HomeType, SquareFeetOption, NewsletterSubscriber, Booking, Contact, Review
from datetime import time, datetime, timedelta
from django.core.exceptions import ValidationError
from giftcards.models import GiftCard, DiscountCode
from django.utils import timezone

class CleaningQuoteForm(forms.ModelForm):
    zip_code = forms.CharField(
        label="ZIP Code",
        max_length=10,
        required=True,
        widget=forms.TextInput(attrs={"class": "cmn-input", "placeholder": "ZIP Code"})
    )

    job_description = forms.CharField(
        label="Tell us about the job",
        required=True,
        widget=forms.Textarea(attrs={
            "class": "cmn-input",
            "placeholder": "Please describe the job in detail.",
            "rows": 3
        })
    )

    hours_requested = forms.IntegerField(
        label="Hours Requested",
        required=True,
        initial=2,
        min_value=2,
        widget=forms.NumberInput(attrs={
            "class": "cmn-input",
            "placeholder": "Enter number of hours",
            "min": 2
        })
    )

    date = forms.DateField(
        label="Select Date",
        widget=forms.DateInput(attrs={"class": "cmn-input", "autocomplete": "off"})
    )

    hour = forms.ChoiceField(
        label="Select Hour",
        widget=forms.Select(attrs={"class": "cmn-input"})
    )

    cleaning_type = forms.CharField(
        required=False
    )

    num_cleaners = forms.IntegerField(
        label="Number of Cleaners",
        required=False,
        initial=2,
        widget=forms.NumberInput(attrs={"class": "cmn-input"})
    )

    class Meta:
        model = Quote
        fields = [
            "service",
            "square_feet_options",
            "home_types",
            "cleaning_type",
            "num_cleaners",
            "job_description",
            "address",
            "apartment",
            "zip_code",
            "date",
            "hour",
            "hours_requested",
            "recurrence_pattern"
        ]

        widgets = {
            "service": forms.Select(attrs={"class": "cmn-input"}),
            "square_feet_options": forms.Select(attrs={"class": "cmn-input"}),
            "home_types": forms.Select(attrs={"class": "cmn-input"}),
            "address": forms.TextInput(attrs={"class": "cmn-input", "placeholder": "Street Address"}),
            "apartment": forms.TextInput(attrs={"class": "cmn-input", "placeholder": "Apt/Suite #"}),
            "recurrence_pattern": forms.Select(attrs={"class": "cmn-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Only show Cleaning services
        self.fields["service"].queryset = Service.objects.filter(category__name="Cleaning")

        # 30-minute time slots from 09:00 to 17:00
        time_slots = []
        t = datetime.strptime("09:00", "%H:%M")
        while t.time() <= time(20, 0):
            time_slots.append((t.strftime("%H:%M"), t.strftime("%H:%M")))
            t += timedelta(minutes=30)

        self.fields["hour"].choices = time_slots

    def clean_hour(self):
        hour = self.cleaned_data.get("hour")
        if not hour or hour in ["", "No available time"]:
            raise forms.ValidationError("Please select a valid available start time.")
        return hour


class HandymanQuoteForm(forms.ModelForm):
    zip_code = forms.CharField(
        label="ZIP Code",
        max_length=10,
        required=True,
        widget=forms.TextInput(attrs={"class": "cmn-input", "placeholder": "ZIP Code"})
    )

    job_description = forms.CharField(
        label="Tell us about the job",
        required=True,
        widget=forms.Textarea(attrs={
            "class": "cmn-input",
            "placeholder": "Please describe the job in detail. (required)",
            "rows": 3
        })
    )

    hours_requested = forms.IntegerField(
        label="Hours Requested",
        required=True,
        initial=2,  # Default value
        min_value=2,  # Minimum allowed value
        widget=forms.NumberInput(attrs={
            "class": "cmn-input",
            "placeholder": "Enter number of hours",
            "min": 2  # Enforces min value on the frontend
        })
    )

    date = forms.DateField(
        label="Select Date",
        widget=forms.DateInput(attrs={"type": "date", "class": "cmn-input"})
    )

    hour = forms.ChoiceField(
        label="Select Hour",
        widget=forms.Select(attrs={"class": "cmn-input"})
    )

    class Meta:
        model = Quote
        fields = ["service", "zip_code", "job_description", "hours_requested", "date", "hour"]

        widgets = {
                "service": forms.Select(attrs={"class": "cmn-input"})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["service"].queryset = Service.objects.filter(category__name="Handyman")

        # Default hour choices (9:00 to 17:00, every 30 min)
        time_slots = []
        t = datetime.strptime("09:00", "%H:%M")
        while t.time() <= time(20, 0):
            time_slots.append((t.strftime("%H:%M"), t.strftime("%H:%M")))
            t += timedelta(minutes=30)

        self.fields["hour"].choices = time_slots

class NewsletterForm(forms.ModelForm):
    class Meta:
        model = NewsletterSubscriber
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'placeholder': 'Enter Your Email',
                'class': 'cmn-input mb-0 newsletter-input',
                'id': 'email',
            })
        }

    def clean_email(self):
        email = self.cleaned_data['email']
        if NewsletterSubscriber.objects.filter(email=email).exists():
            raise ValidationError("You're already subscribed with this email.")
        return email
    

# Booking Form
class CleaningBookingForm(forms.ModelForm):
    zip_code = forms.CharField(
        label="ZIP Code",
        max_length=10,
        required=True,
        widget=forms.TextInput(attrs={"class": "cmn-input", "placeholder": "ZIP Code"})
    )

    job_description = forms.CharField(
        label="Tell us about the job",
        required=True,
        widget=forms.Textarea(attrs={
            "class": "cmn-input",
            "placeholder": "Please describe the job in detail.",
            "rows": 3
        })
    )

    hours_requested = forms.IntegerField(
        label="Hours Requested",
        required=True,
        initial=2,
        min_value=2,
        widget=forms.NumberInput(attrs={
            "class": "cmn-input",
            "placeholder": "Enter number of hours",
            "min": 2
        })
    )

    date = forms.DateField(
        label="Select Date",
        widget=forms.DateInput(attrs={"class": "cmn-input", "autocomplete": "off"})
    )

    hour = forms.ChoiceField(
        label="Select Hour",
        widget=forms.Select(attrs={"class": "cmn-input", "id": "id_hour" })
    )

    cleaning_type = forms.CharField(
        required=False
    )

    num_cleaners = forms.IntegerField(
        label="Number of Cleaners",
        required=False,
        initial=2,
        widget=forms.NumberInput(attrs={"class": "cmn-input"})
    )

    gift_card_code = forms.CharField(
        required=False,
        label="Gift Card / Discount Code",
        widget=forms.TextInput(attrs={
            "class": "cmn-input",
            "placeholder": "Enter Gift Card or Discount Code"
        })
    )

    class Meta:
        model = Booking
        fields = [
            "service_cat",
            "square_feet_options",
            "home_types",
            "cleaning_type",
            "num_cleaners",
            "job_description",
            "name",
            "email",
            "phone",
            "address",
            "apartment",
            "zip_code",
            "date",
            "hour",
            "hours_requested",
            "recurrence_pattern"
        ]

        widgets = {
            "service_cat": forms.Select(attrs={"class": "cmn-input"}),
            "square_feet_options": forms.Select(attrs={"class": "cmn-input"}),
            "home_types": forms.Select(attrs={"class": "cmn-input"}),
            "name": forms.TextInput(attrs={"class": "cmn-input", "placeholder": "Full Name"}),
            "email": forms.EmailInput(attrs={"class": "cmn-input", "placeholder": "Email"}),
            "phone": forms.TextInput(attrs={"class": "cmn-input", "placeholder": "Phone Number (Optional)"}),
            "address": forms.TextInput(attrs={"class": "cmn-input", "placeholder": "Street Address"}),
            "apartment": forms.TextInput(attrs={"class": "cmn-input", "placeholder": "Apt/Suite #"}),
            "recurrence_pattern": forms.Select(attrs={"class": "cmn-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Only show Cleaning services
        # self.fields["service"].queryset = Service.objects.filter(category__name="Cleaning")

        # 30-minute time slots from 09:00 to 17:00
        time_slots = []
        t = datetime.strptime("09:00", "%H:%M")
        while t.time() <= time(20, 0):
            time_slots.append((t.strftime("%H:%M"), t.strftime("%H:%M")))
            t += timedelta(minutes=30)

        self.fields["hour"].choices = time_slots

    def clean_gift_card_code(self):
        code = self.cleaned_data.get("gift_card_code", "").strip()
        if not code:
            return None

        # 1. Try GiftCard
        try:
            giftcard = GiftCard.objects.get(code__iexact=code, is_active=True, balance__gt=0)
            return ("giftcard", giftcard)
        except GiftCard.DoesNotExist:
            pass

        # 2. Try DiscountCode
        try:
            discount = DiscountCode.objects.get(code__iexact=code, is_active=True)
            if discount.usage_limit > discount.times_used and (not discount.expires_at or timezone.now() < discount.expires_at):
                return ("discount", discount)
        except DiscountCode.DoesNotExist:
            pass

        raise forms.ValidationError("Invalid or expired code.")


class HandymanBookingForm(forms.ModelForm):
    zip_code = forms.CharField(
        label="ZIP Code",
        max_length=10,
        required=True,
        widget=forms.TextInput(attrs={"class": "cmn-input", "placeholder": "ZIP Code"})
    )

    job_description = forms.CharField(
        label="Tell us about the job",
        required=True,
        widget=forms.Textarea(attrs={
            "class": "cmn-input",
            "placeholder": "Please describe the job in detail. (required)",
            "rows": 3
        })
    )

    hours_requested = forms.IntegerField(
        label="Hours Requested",
        required=True,
        initial=2,  # Default value
        min_value=2,  # Minimum allowed value
        widget=forms.NumberInput(attrs={
            "class": "cmn-input",
            "placeholder": "Enter number of hours",
            "min": 2  # Enforces min value on the frontend
        })
    )

    date = forms.DateField(
        label="Select Date",
        widget=forms.DateInput(attrs={"type": "date", "class": "cmn-input"})
    )

    hour = forms.ChoiceField(
        label="Select Hour",
        widget=forms.Select(attrs={"class": "cmn-input"})
    )

    class Meta:
        model = Booking
        fields = ["service_cat", "name", "email", "phone", "address", "apartment", "zip_code", "job_description", "hours_requested", "date", "hour"]

        widgets = {
                "service_cat": forms.Select(attrs={"class": "cmn-input"}),
                "name": forms.TextInput(attrs={"class": "cmn-input", "placeholder": "Full Name"}),
                "email": forms.EmailInput(attrs={"class": "cmn-input", "placeholder": "Email"}),
                "phone": forms.TextInput(attrs={"class": "cmn-input", "placeholder": "Phone Number (Optional)"}),
                "address": forms.TextInput(attrs={"class": "cmn-input", "placeholder": "Street Address"}),
                "apartment": forms.TextInput(attrs={"class": "cmn-input", "placeholder": "Apt/Suite #"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #self.fields["service"].queryset = Service.objects.filter(category__name="Handyman")

        # Default hour choices (9:00 to 17:00, every 30 min)
        time_slots = []
        t = datetime.strptime("09:00", "%H:%M")
        while t.time() <= time(20, 0):
            time_slots.append((t.strftime("%H:%M"), t.strftime("%H:%M")))
            t += timedelta(minutes=30)

        self.fields["hour"].choices = time_slots


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ["name", "email", "subject", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "cmn-input", "placeholder": "Enter Name"}),
            "email": forms.EmailInput(attrs={"class": "cmn-input", "placeholder": "Your Email"}),
            "subject": forms.TextInput(attrs={"class": "cmn-input", "placeholder": "Subject"}),
            "message": forms.Textarea(attrs={"class": "cmn-input", "placeholder": "Write your message", "rows": 4}),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "review"]
        widgets = {
            "rating": forms.Select(attrs={"class": "cmn-input", "required": True}),
            "review": forms.Textarea(attrs={"class": "cmn-input", "rows": 4, "required": True}),
        }




