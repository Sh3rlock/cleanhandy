from django import forms
from .models import Quote, Service, HomeType, SquareFeetOption, NewsletterSubscriber, Booking, Contact, Review, OfficeQuote, HandymanQuote, PostEventCleaningQuote, HomeCleaningQuoteRequest
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

    hours_requested = forms.DecimalField(
        label="Hours Requested",
        required=True,
        initial=2,
        min_value=2,
        max_digits=4,
        decimal_places=1,
        widget=forms.NumberInput(attrs={
            "class": "cmn-input",
            "placeholder": "Enter number of hours",
            "min": 2,
            "step": 0.5
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

        # Only show Home cleaning services
        self.fields["service"].queryset = Service.objects.filter(category__name="Home")

        # 30-minute time slots from 08:00 to 20:00
        time_slots = []
        t = datetime.strptime("08:00", "%H:%M")
        while t.time() <= time(20, 0):
            time_slots.append((t.strftime("%H:%M"), t.strftime("%H:%M")))
            t += timedelta(minutes=30)

        self.fields["hour"].choices = time_slots

    def clean_hour(self):
        hour = self.cleaned_data.get("hour")
        print(f"🔍 Cleaning hour: '{hour}'")
        print(f"🔍 Available hour choices: {self.fields['hour'].choices}")
        if not hour or hour in ["", "No available time"]:
            print(f"❌ Invalid hour: '{hour}'")
            raise forms.ValidationError("Please select a valid available start time.")
        print(f"✅ Valid hour: '{hour}'")
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

class OfficeQuoteForm(forms.ModelForm):
    name = forms.CharField(
        label="Full Name",
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            "class": "cmn-input",
            "placeholder": "Enter your full name"
        })
    )
    
    email = forms.EmailField(
        label="Email Address",
        required=True,
        widget=forms.EmailInput(attrs={
            "class": "cmn-input",
            "placeholder": "Enter your email address"
        })
    )
    
    phone_number = forms.CharField(
        label="Phone Number",
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            "class": "cmn-input",
            "placeholder": "Enter your phone number"
        })
    )
    
    business_address = forms.CharField(
        label="Business Address",
        required=True,
        widget=forms.Textarea(attrs={
            "class": "cmn-input",
            "placeholder": "Enter your complete business address",
            "rows": 3
        })
    )
    
    square_footage = forms.CharField(
        label="Square Footage (Estimation)",
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            "class": "cmn-input",
            "placeholder": "e.g., 2,500 sq ft, 5,000 sq ft"
        })
    )
    
    job_description = forms.CharField(
        label="Description about the job",
        required=True,
        widget=forms.Textarea(attrs={
            "class": "cmn-input",
            "placeholder": "Please describe the cleaning job in detail...",
            "rows": 4
        })
    )
    
    class Meta:
        model = OfficeQuote
        fields = [
            "name",
            "email", 
            "phone_number",
            "business_address",
            "square_footage",
            "job_description"
        ]

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

    hours_requested = forms.DecimalField(
        label="Hours Requested",
        required=True,
        initial=2,
        min_value=2,
        max_digits=4,
        decimal_places=1,
        widget=forms.NumberInput(attrs={
            "class": "cmn-input",
            "placeholder": "Enter number of hours",
            "min": 2,
            "step": 0.5
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

    get_in = forms.ChoiceField(
        label="How will we get into your home?",
        choices=[
            ("at_home", "I'll be at home"),
            ("doorman", "The key is with doorman"),
            ("lockbox", "Lockbox on premises"),
            ("call_organize", "Call to organize"),
            ("other", "Other"),
        ],
        required=False,
        widget=forms.RadioSelect(attrs={"class": "form-check-input"})
    )

    parking = forms.CharField(
        label="Parking Instructions",
        required=False,
        widget=forms.Textarea(attrs={
            "class": "cmn-input",
            "placeholder": "Please provide parking instructions for our cleaning team...",
            "rows": 3
        })
    )

    pet = forms.ChoiceField(
        label="Do you have any pets?",
        choices=[
            ("cat", "Cat"),
            ("dog", "Dog"),
            ("both", "Both"),
            ("other", "Other"),
        ],
        required=False,
        widget=forms.RadioSelect(attrs={"class": "form-check-input"})
    )

    class Meta:
        model = Booking
        fields = [
            "service_cat",
            "square_feet_options",
            "home_types",
            "cleaning_type",
            "num_cleaners",
            "business_type",
            "crew_size_hours",
            "hear_about_us",
            "cleaning_frequency",
            "job_description",
            "name",
            "email",
            "phone",
            "address",
            "apartment",
            "zip_code",
            "city",
            "state",
            "bath_count",
            "date",
            "hour",
            "hours_requested",
            "recurrence_pattern",
            "get_in",
            "parking",
            "pet"
        ]

        widgets = {
            "service_cat": forms.Select(attrs={"class": "cmn-input"}),
            "square_feet_options": forms.Select(attrs={"class": "cmn-input"}),
            "home_types": forms.Select(attrs={"class": "cmn-input"}),
            "business_type": forms.Select(attrs={"class": "cmn-input"}),
            "crew_size_hours": forms.Select(attrs={"class": "cmn-input"}),
            "hear_about_us": forms.Select(attrs={"class": "cmn-input"}),
            "cleaning_frequency": forms.Select(attrs={"class": "cmn-input"}),
            "name": forms.TextInput(attrs={"class": "cmn-input", "placeholder": "Full Name"}),
            "email": forms.EmailInput(attrs={"class": "cmn-input", "placeholder": "Email"}),
            "phone": forms.TextInput(attrs={"class": "cmn-input", "placeholder": "Phone Number"}),
            "address": forms.TextInput(attrs={"class": "cmn-input", "placeholder": "Street Address"}),
            "apartment": forms.TextInput(attrs={"class": "cmn-input", "placeholder": "Apt/Suite #"}),
            "city": forms.TextInput(attrs={"class": "cmn-input", "placeholder": "City"}),
            "state": forms.TextInput(attrs={"class": "cmn-input", "placeholder": "State"}),
            "bath_count": forms.Select(attrs={"class": "cmn-input"}),
            "recurrence_pattern": forms.Select(attrs={"class": "cmn-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Only show Cleaning services
        # self.fields["service"].queryset = Service.objects.filter(category__name="Cleaning")

        # 30-minute time slots from 08:00 to 20:00
        time_slots = []
        t = datetime.strptime("08:00", "%H:%M")
        while t.time() <= time(20, 0):
            time_slots.append((t.strftime("%H:%M"), t.strftime("%H:%M")))
            t += timedelta(minutes=30)

        self.fields["hour"].choices = time_slots

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        hour = cleaned_data.get('hour')
        hours_requested = cleaned_data.get('hours_requested', 2)
        
        if date and hour and hours_requested:
            # Check for time slot conflicts
            from .utils import check_time_slot_conflict
            # Convert hour string to time object
            try:
                hour_time = datetime.strptime(hour, "%H:%M").time()
                if check_time_slot_conflict(date, hour_time, hours_requested):
                    raise forms.ValidationError(
                        "This time slot is already booked. Please select a different time."
                    )
            except ValueError:
                # If hour format is invalid, let the clean_hour method handle it
                pass
        
        return cleaned_data

    def clean_gift_card_code(self):
        code = self.cleaned_data.get("gift_card_code", "").strip()
        print(f"🔍 Cleaning gift_card_code: '{code}'")
        if not code:
            return None

        # 1. Try GiftCard
        try:
            giftcard = GiftCard.objects.get(code__iexact=code, is_active=True, balance__gt=0)
            print(f"✅ Found gift card: {giftcard.code}")
            return ("giftcard", giftcard)
        except GiftCard.DoesNotExist:
            print(f"❌ Gift card not found: {code}")
            pass

        # 2. Try DiscountCode
        try:
            discount = DiscountCode.objects.get(code__iexact=code, is_active=True)
            if discount.usage_limit > discount.times_used and (not discount.expires_at or timezone.now() < discount.expires_at):
                print(f"✅ Found discount code: {discount.code}")
                return ("discount", discount)
            else:
                print(f"❌ Discount code expired or usage limit reached: {code}")
        except DiscountCode.DoesNotExist:
            print(f"❌ Discount code not found: {code}")
            pass

        raise forms.ValidationError("Invalid or expired code.")


class PostEventCleaningQuoteForm(forms.ModelForm):
    """Form for Post Event Cleaning quote requests"""
    
    event_type = forms.ChoiceField(
        label="Event Type",
        choices=[
            ("wedding", "Wedding"),
            ("birthday", "Birthday Party"),
            ("corporate", "Corporate Event"),
            ("holiday", "Holiday Party"),
            ("graduation", "Graduation Party"),
            ("anniversary", "Anniversary"),
            ("other", "Other"),
        ],
        widget=forms.Select(attrs={"class": "cmn-input"})
    )
    
    venue_size = forms.ChoiceField(
        label="Venue Size",
        choices=[
            ("small", "Small (up to 50 people)"),
            ("medium", "Medium (50-150 people)"),
            ("large", "Large (150+ people)"),
        ],
        widget=forms.Select(attrs={"class": "cmn-input"})
    )
    
    event_date = forms.DateField(
        label="Event Date",
        widget=forms.DateInput(attrs={"type": "date", "class": "cmn-input"})
    )
    
    cleaning_date = forms.DateField(
        label="Preferred Cleaning Date",
        widget=forms.DateInput(attrs={"type": "date", "class": "cmn-input"})
    )
    
    special_requirements = forms.CharField(
        label="Special Requirements (Optional)",
        required=False,
        widget=forms.Textarea(attrs={
            "class": "cmn-input",
            "placeholder": "Any special cleaning requirements or notes",
            "rows": 3
        })
    )

    class Meta:
        model = PostEventCleaningQuote
        fields = [
            "name", "email", "phone_number", "address", "event_description", 
            "event_date", "cleaning_date", "event_type", "venue_size", "special_requirements"
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "cmn-input", "placeholder": "Full Name"}),
            "email": forms.EmailInput(attrs={"class": "cmn-input", "placeholder": "Email Address"}),
            "phone_number": forms.TextInput(attrs={"class": "cmn-input", "placeholder": "Phone Number"}),
            "address": forms.Textarea(attrs={
                "class": "cmn-input", 
                "placeholder": "Full Address",
                "rows": 3
            }),
            "event_description": forms.Textarea(attrs={
                "class": "cmn-input",
                "placeholder": "Please describe your event and cleaning requirements in detail",
                "rows": 4
            }),
        }

    def clean_cleaning_date(self):
        cleaning_date = self.cleaned_data.get('cleaning_date')
        event_date = self.cleaned_data.get('event_date')
        
        if cleaning_date and event_date:
            if cleaning_date < event_date:
                raise forms.ValidationError("Cleaning date cannot be before the event date.")
        
        return cleaning_date


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
                "phone": forms.TextInput(attrs={"class": "cmn-input", "placeholder": "Phone Number"}),
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


class OfficeCleaningBookingForm(CleaningBookingForm):
    business_type = forms.ChoiceField(
        label="Type Of Business",
        choices=[
            ("office", "Office"),
            ("retail", "Retail"),
            ("medical", "Medical"),
            ("school", "School"),
            ("other", "Other")
        ],
        initial="office",
        required=False,  # Make optional since it's handled by custom HTML
        widget=forms.Select(attrs={"class": "cmn-input"})
    )
    
    crew_size_hours = forms.ChoiceField(
        label="Crew/Size/Hours",
        choices=[
            ("1_cleaner_2_hours_500", "1 Cleaner Total 2 Hours (<500 Sq Ft)"),
            ("1_cleaner_3_hours_1000", "1 Cleaner Total 3 Hours (<1000 Sq Ft)"),
            ("1_cleaner_4_hours_1500", "1 Cleaner Total 4 Hours (<1500 Sq Ft)"),
            ("2_cleaners_2.5_hours_2000", "2 Cleaners Total 2.5 Hours (<2000 Sq Ft)"),
            ("2_cleaners_3_hours_2500", "2 Cleaners Total 3 Hours (<2500 Sq Ft)"),
            ("2_cleaners_4_hours_3000", "2 Cleaners Total 4 Hours (<3000 Sq Ft)"),
            ("2_cleaners_5_hours_3500", "2 Cleaners Total 5 Hours (<3500 Sq Ft)"),
            ("2_cleaners_6_hours_4000", "2 Cleaners Total 6 Hours (<4000 Sq Ft)"),
            ("2_cleaners_7_hours_5000", "2 Cleaners Total 7 Hours (<5000 Sq Ft)"),
            ("custom_cleaning", "Customized Cleaning (>5000 Sq Ft) Please Email")
        ],
        required=False,  # Make optional since it's handled by custom HTML
        widget=forms.Select(attrs={"class": "cmn-input"})
    )
    
    hear_about_us = forms.ChoiceField(
        label="How did you hear about us?",
        choices=[
            ("", "Select an option"),
            ("google", "Google Search"),
            ("social_media", "Social Media"),
            ("referral", "Referral"),
            ("advertisement", "Advertisement"),
            ("yelp", "Yelp"),
            ("other", "Other")
        ],
        required=False,
        widget=forms.Select(attrs={"class": "cmn-input"})
    )
    
    cleaning_frequency = forms.ChoiceField(
        label="Cleaning Frequency",
        choices=[
            ("one_time", "One time"),
            ("daily", "Daily - 20% Off"),
            ("weekly", "Weekly 15% Off"),
            ("bi_weekly", "Bi Weekly 10% Off"),
            ("monthly", "Monthly 5% Off")
        ],
        initial="one_time",
        required=False,  # Make optional since it's handled by custom HTML
        widget=forms.Select(attrs={"class": "cmn-input"})
    )

    class Meta(CleaningBookingForm.Meta):
        fields = CleaningBookingForm.Meta.fields + [
            "business_type",
            "crew_size_hours", 
            "hear_about_us",
            "cleaning_frequency"
        ]
        widgets = CleaningBookingForm.Meta.widgets.copy()
        widgets.update({
            "business_type": forms.Select(attrs={"class": "cmn-input"}),
            "crew_size_hours": forms.Select(attrs={"class": "cmn-input"}),
            "hear_about_us": forms.Select(attrs={"class": "cmn-input"}),
            "cleaning_frequency": forms.Select(attrs={"class": "cmn-input"}),
        })

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial values for office cleaning
        self.fields['cleaning_type'].initial = 'office_cleaning'
        self.fields['recurrence_pattern'].initial = 'one_time'
        
        # Make these fields not required since they're handled by custom HTML
        self.fields['business_type'].required = False
        self.fields['crew_size_hours'].required = False
        self.fields['cleaning_frequency'].required = False
        
        # Make other required fields optional since they're handled by custom HTML
        self.fields['service_cat'].required = False
        self.fields['date'].required = False
        self.fields['hour'].required = False
        self.fields['hours_requested'].required = False
        self.fields['num_cleaners'].required = False
        self.fields['square_feet_options'].required = False
        self.fields['home_types'].required = False

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        hour = cleaned_data.get('hour')
        hours_requested = cleaned_data.get('hours_requested', 2)
        
        if date and hour and hours_requested:
            # Check for time slot conflicts
            from .utils import check_time_slot_conflict
            # Convert hour string to time object
            try:
                hour_time = datetime.strptime(hour, "%H:%M").time()
                if check_time_slot_conflict(date, hour_time, hours_requested):
                    raise forms.ValidationError(
                        "This time slot is already booked. Please select a different time."
                    )
            except ValueError:
                # If hour format is invalid, let the clean_hour method handle it
                pass
        
        return cleaned_data


class HandymanQuoteForm(forms.ModelForm):
    """Form for handyman quote requests"""
    
    class Meta:
        model = HandymanQuote
        fields = ['name', 'email', 'phone_number', 'address', 'job_description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your full name',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email address',
                'required': True
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your phone number',
                'required': True
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter the address where handyman work is needed',
                'rows': 3,
                'required': True
            }),
            'job_description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Please describe the handyman job in detail...',
                'rows': 4,
                'required': True
            }),
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name.strip()) < 2:
            raise forms.ValidationError("Name must be at least 2 characters long.")
        return name.strip()
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            # Remove common formatting characters
            cleaned_phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            if not cleaned_phone.isdigit() or len(cleaned_phone) < 10:
                raise forms.ValidationError("Please enter a valid phone number.")
        return phone
    
    def clean_job_description(self):
        description = self.cleaned_data.get('job_description')
        if description and len(description.strip()) < 20:
            raise forms.ValidationError("Job description must be at least 20 characters long.")
        return description.strip()


class HomeCleaningQuoteRequestForm(forms.ModelForm):
    # Custom fields that need specific handling
    # bath_count is now dynamic from PriceVariable, so use CharField to accept any value (PriceVariable ID)
    bath_count = forms.CharField(
        label="Number of Bathrooms",
        required=True,
        widget=forms.Select(attrs={"class": "cmn-input"})
    )
    
    # cleaning_type is now dynamic from PriceVariable (variable_name), so use CharField to accept any value
    cleaning_type = forms.CharField(
        label="Cleaning Type",
        required=True,
        widget=forms.Select(attrs={"class": "cmn-input"})
    )
    
    get_in = forms.ChoiceField(
        label="How will we get into your home?",
        choices=[
            ("at_home", "I'll be at home"),
            ("doorman", "The key is with doorman"),
            ("lockbox", "Lockbox on premises"),
            ("call_organize", "Call to organize"),
            ("other", "Other"),
        ],
        required=False,
        widget=forms.RadioSelect(attrs={"class": "form-check-input"})
    )
    
    pet = forms.ChoiceField(
        label="Do you have any pets?",
        choices=[
            ("none", "None"),
            ("cat", "Cat"),
            ("dog", "Dog"),
            ("both", "Both"),
            ("other", "Other"),
        ],
        required=False,
        widget=forms.RadioSelect(attrs={"class": "form-check-input"})
    )
    
    name = forms.CharField(
        label="Name",
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={"class": "cmn-input", "placeholder": "Full Name"})
    )
    
    email = forms.EmailField(
        label="Email",
        required=True,
        widget=forms.EmailInput(attrs={"class": "cmn-input", "placeholder": "Email Address"})
    )
    
    phone = forms.CharField(
        label="Phone",
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={"class": "cmn-input", "placeholder": "Phone Number", "type": "tel"})
    )
    
    class Meta:
        model = HomeCleaningQuoteRequest
        fields = [
            "service",
            "home_types",
            "cleaning_type",
            "bath_count",
            "job_description",
            "address",
            "apartment",
            "city",
            "state",
            "zip_code",
            "date",
            "hour",
            "get_in",
            "parking",
            "pet",
            "cleaning_frequency",
            "name",
            "email",
            "phone",
        ]
        widgets = {
            "service": forms.HiddenInput(),
            "date": forms.HiddenInput(),
            "hour": forms.HiddenInput(),
            "city": forms.HiddenInput(),
            "state": forms.HiddenInput(),
            "job_description": forms.Textarea(attrs={"class": "cmn-input", "rows": 4, "placeholder": "Please describe the job in detail..."}),
            "address": forms.TextInput(attrs={"class": "cmn-input", "placeholder": "Street Address"}),
            "apartment": forms.TextInput(attrs={"class": "cmn-input", "placeholder": "Apt/Suite"}),
            "zip_code": forms.TextInput(attrs={"class": "cmn-input", "placeholder": "ZIP Code"}),
            "parking": forms.Textarea(attrs={"class": "cmn-input", "rows": 3, "placeholder": "Please provide parking instructions..."}),
            "home_types": forms.Select(attrs={"class": "cmn-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make optional fields align with template usage
        optional_fields = [
            "get_in",
            "parking",
            "pet",
            "cleaning_frequency",
            "apartment",
            "home_types",
        ]
        for fname in optional_fields:
            if fname in self.fields:
                self.fields[fname].required = False

        # Required fields
        required_fields = [
            "name",
            "email",
            "phone",
            "address",
            "zip_code",
            "bath_count",
            "cleaning_type",
        ]
        for fname in required_fields:
            if fname in self.fields:
                self.fields[fname].required = True
        
        # Make job_description optional
        if "job_description" in self.fields:
            self.fields["job_description"].required = False

        # Allow all services; validation handled in view and clean method
        self.fields["service"].queryset = Service.objects.all()
        self.fields["service"].required = False
        # Don't validate queryset - we'll handle service selection in clean method
        self.fields["service"].widget.attrs['data-allow-any'] = 'true'
        
        # Set default values for city and state
        if not self.initial.get('city'):
            self.initial['city'] = 'New York'
        if not self.initial.get('state'):
            self.initial['state'] = 'NY'

    def clean_service(self):
        """Automatically set service based on cleaning_type or default to Regular Cleaning"""
        service = self.cleaned_data.get('service')
        cleaning_type = self.data.get('cleaning_type') or self.cleaned_data.get('cleaning_type')
        
        # Get home category services
        from .models import ServiceCategory
        home_category = ServiceCategory.objects.filter(name__iexact='home').first()
        if not home_category:
            # Try alternative category names
            home_category = ServiceCategory.objects.filter(name__iexact='cleaning').first()
        
        if home_category:
            home_services = Service.objects.filter(category=home_category)
        else:
            home_services = Service.objects.all()
        
        # If service is valid and exists, return it
        if service:
            # Verify service still exists in database
            if Service.objects.filter(id=service.id).exists():
                return service
            # If service doesn't exist, we'll set a new one below
        
        # Service is not set or invalid, set it based on cleaning_type
        service_set = False
        selected_service = None
        
        if cleaning_type:
            # Map cleaning types to service names
            service_name_mapping = {
                'Regular Cleaning': ['Deep Cleaning', 'Regular Cleaning', 'Standard Cleaning'],
                'Deep Cleaning': ['Deep Cleaning'],
                'Move In/Out Cleaning': ['Move In/Out Cleaning', 'Move In Cleaning', 'Move Out Cleaning'],
                'Post Renovation': ['Post Renovation Cleaning', 'Post Renovation']
            }
            
            target_names = service_name_mapping.get(cleaning_type, [])
            
            # Try exact match first
            for service_obj in home_services:
                if service_obj.name in target_names:
                    selected_service = service_obj
                    service_set = True
                    break
            
            # If no exact match, try partial matching
            if not service_set:
                for service_obj in home_services:
                    service_name_lower = service_obj.name.lower()
                    if cleaning_type == 'Regular Cleaning' and ('deep' in service_name_lower or 'regular' in service_name_lower or 'standard' in service_name_lower):
                        selected_service = service_obj
                        service_set = True
                        break
                    elif cleaning_type == 'Deep Cleaning' and 'deep' in service_name_lower:
                        selected_service = service_obj
                        service_set = True
                        break
                    elif cleaning_type == 'Move In/Out Cleaning' and ('move' in service_name_lower and ('in' in service_name_lower or 'out' in service_name_lower)):
                        selected_service = service_obj
                        service_set = True
                        break
                    elif cleaning_type == 'Post Renovation' and 'renovation' in service_name_lower:
                        selected_service = service_obj
                        service_set = True
                        break
        
        # Default to first home service (Regular Cleaning equivalent) if still not set
        if not service_set:
            default_service = home_services.first()
            if default_service:
                selected_service = default_service
            else:
                # Last resort: get any service
                any_service = Service.objects.first()
                if any_service:
                    selected_service = any_service
        
        # Return the selected service (or None if no services exist - will be handled in clean method)
        return selected_service
    
    def clean(self):
        """Ensure service is always set"""
        cleaned_data = super().clean()
        
        # If service is still not set after clean_service, set a default
        if not cleaned_data.get('service'):
            from .models import ServiceCategory
            home_category = ServiceCategory.objects.filter(name__iexact='home').first()
            if not home_category:
                home_category = ServiceCategory.objects.filter(name__iexact='cleaning').first()
            
            if home_category:
                default_service = Service.objects.filter(category=home_category).first()
            else:
                default_service = Service.objects.first()
            
            if default_service:
                cleaned_data['service'] = default_service
        
        return cleaned_data




