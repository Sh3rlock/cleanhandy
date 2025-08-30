from django import forms
from django.forms import ModelForm
from .models import Booking, ExtraService, ServiceType
from django.core.exceptions import ValidationError
from datetime import date, timedelta


class HomeCleaningForm(forms.ModelForm):
    """Complete Home Cleaning booking form with all steps"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Handle ExtraService field safely
        try:
            self.fields['extra_services'] = forms.ModelMultipleChoiceField(
                queryset=ExtraService.objects.all(),
                widget=forms.CheckboxSelectMultiple(attrs={'class': 'extra-service-checkbox'}),
                required=False
            )
        except:
            # If ExtraService model doesn't exist, create a simple choice field
            self.fields['extra_services'] = forms.MultipleChoiceField(
                choices=[],
                widget=forms.CheckboxSelectMultiple(attrs={'class': 'extra-service-checkbox'}),
                required=False
            )
    
    # Step 1: Service Details
    service_type = forms.ModelChoiceField(
        queryset=ServiceType.objects.filter(name='Home Cleaning'),
        widget=forms.HiddenInput(),
        initial=1
    )
    bedrooms = forms.ChoiceField(
        choices=Booking._meta.get_field('bedrooms').choices or [],
        widget=forms.RadioSelect(attrs={'class': 'bedroom-radio'}),
        required=True
    )
    bathrooms = forms.ChoiceField(
        choices=Booking._meta.get_field('bathrooms').choices or [],
        widget=forms.RadioSelect(attrs={'class': 'bathroom-radio'}),
        required=True
    )
    cleaning_type = forms.ChoiceField(
        choices=Booking._meta.get_field('cleaning_type').choices or [],
        widget=forms.RadioSelect(attrs={'class': 'cleaning-type-radio'}),
        required=True
    )
    has_pets = forms.ChoiceField(
        choices=Booking._meta.get_field('has_pets').choices or [],
        widget=forms.RadioSelect(attrs={'class': 'pets-radio'}),
        required=True
    )
    additional_details = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any specific cleaning requirements or special instructions?'
        }),
        required=False
    )
    
    # Step 3: Frequency
    frequency = forms.ChoiceField(
        choices=Booking._meta.get_field('frequency').choices or [],
        widget=forms.RadioSelect(attrs={'class': 'frequency-radio'}),
        required=True
    )
    
    # Step 4: Date and Time
    date_of_service = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'min': 'today'
        }),
        required=True
    )
    time_slot = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        }),
        required=True
    )
    timezone_choice = forms.ChoiceField(
        choices=Booking._meta.get_field('timezone_choice').choices or [],
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    
    # Step 5: Contact Information
    first_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        }),
        required=True
    )
    last_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        }),
        required=True
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address'
        }),
        required=True
    )
    phone_country_code = forms.ChoiceField(
        choices=Booking._meta.get_field('phone_country_code').choices or [],
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    phone_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone Number'
        }),
        required=True
    )
    access_method = forms.ChoiceField(
        choices=Booking._meta.get_field('access_method').choices or [],
        widget=forms.RadioSelect(attrs={'class': 'access-method-radio'}),
        required=True
    )
    referral_source = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}, choices=[
            ('', 'Select an option'),
            ('google', 'Google'),
            ('facebook', 'Facebook'),
            ('instagram', 'Instagram'),
            ('friend', 'Friend/Family'),
            ('yelp', 'Yelp'),
            ('other', 'Other'),
        ])
    )
    
    # Step 6: Location
    street_address = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Street Address'
        }),
        required=True
    )
    unit_apt_suite = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Unit, Apt, Suite (Optional)'
        })
    )
    city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'City'
        }),
        required=True
    )
    state = forms.ChoiceField(
        choices=Booking._meta.get_field('state').choices or [],
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    zip_code = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'ZIP Code'
        }),
        required=True
    )
    
    # Step 7: Terms
    terms_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = Booking
        exclude = ['status', 'created_at', 'updated_at', 'base_price', 'extra_services_total', 'discount_amount', 'total_price']
    
    def clean_date_of_service(self):
        date_of_service = self.cleaned_data.get('date_of_service')
        if date_of_service and date_of_service < date.today():
            raise forms.ValidationError("Date cannot be in the past.")
        return date_of_service
    
    def clean(self):
        cleaned_data = super().clean()
        # Add any cross-field validation here
        return cleaned_data


class OfficeCleaningForm(forms.ModelForm):
    """Complete Office Cleaning booking form with all steps"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Handle ExtraService field safely
        try:
            self.fields['extra_services'] = forms.ModelMultipleChoiceField(
                queryset=ExtraService.objects.all(),
                widget=forms.CheckboxSelectMultiple(attrs={'class': 'extra-service-checkbox'}),
                required=False
            )
        except:
            # If ExtraService model doesn't exist, create a simple choice field
            self.fields['extra_services'] = forms.MultipleChoiceField(
                choices=[],
                widget=forms.CheckboxSelectMultiple(attrs={'class': 'extra-service-checkbox'}),
                required=False
            )
    
    # Step 1: Service Details
    service_type = forms.ModelChoiceField(
        queryset=ServiceType.objects.filter(name='Office Cleaning'),
        widget=forms.HiddenInput(),
        initial=2
    )
    business_type = forms.ChoiceField(
        choices=Booking._meta.get_field('business_type').choices or [],
        widget=forms.RadioSelect(attrs={'class': 'business-type-radio'}),
        initial='office',
        required=True
    )
    crew_size_hours = forms.ChoiceField(
        choices=Booking._meta.get_field('crew_size_hours').choices or [],
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    
    # Step 1b: Office Space
    num_restrooms = forms.IntegerField(
        min_value=0,
        max_value=50,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control space-quantity',
            'min': '0',
            'max': '50'
        }),
        required=True
    )
    num_kitchen_areas = forms.IntegerField(
        min_value=0,
        max_value=20,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control space-quantity',
            'min': '0',
            'max': '20'
        }),
        required=True
    )
    num_conference_rooms = forms.IntegerField(
        min_value=0,
        max_value=30,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control space-quantity',
            'min': '0',
            'max': '30'
        }),
        required=True
    )
    num_private_offices = forms.IntegerField(
        min_value=0,
        max_value=100,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control space-quantity',
            'min': '0',
            'max': '100'
        }),
        required=True
    )
    additional_details = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any specific cleaning requirements or special instructions?'
        }),
        required=False
    )
    
    # Step 3: Frequency
    frequency = forms.ChoiceField(
        choices=Booking._meta.get_field('frequency').choices or [],
        widget=forms.RadioSelect(attrs={'class': 'frequency-radio'}),
        required=True
    )
    
    # Step 4: Date and Time
    date_of_service = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'min': 'today'
        }),
        required=True
    )
    time_slot = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        }),
        required=True
    )
    timezone_choice = forms.ChoiceField(
        choices=Booking._meta.get_field('timezone_choice').choices or [],
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    
    # Step 5: Contact Information
    first_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        }),
        required=True
    )
    last_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        }),
        required=True
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address'
        }),
        required=True
    )
    phone_country_code = forms.ChoiceField(
        choices=Booking._meta.get_field('phone_country_code').choices or [],
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    phone_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone Number'
        }),
        required=True
    )
    access_method = forms.ChoiceField(
        choices=Booking._meta.get_field('access_method').choices or [],
        widget=forms.RadioSelect(attrs={'class': 'access-method-radio'}),
        required=True
    )
    referral_source = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}, choices=[
            ('', 'Select an option'),
            ('google', 'Google'),
            ('facebook', 'Facebook'),
            ('instagram', 'Instagram'),
            ('friend', 'Friend/Family'),
            ('yelp', 'Yelp'),
            ('other', 'Other'),
        ])
    )
    
    # Step 6: Location
    street_address = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Street Address'
        }),
        required=True
    )
    unit_apt_suite = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Unit, Apt, Suite (Optional)'
        })
    )
    city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'City'
        }),
        required=True
    )
    state = forms.ChoiceField(
        choices=Booking._meta.get_field('state').choices or [],
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    zip_code = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'ZIP Code'
        }),
        required=True
    )
    
    # Step 7: Terms
    terms_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = Booking
        exclude = ['status', 'created_at', 'updated_at', 'base_price', 'extra_services_total', 'discount_amount', 'total_price']
    
    def clean_date_of_service(self):
        date_of_service = self.cleaned_data.get('date_of_service')
        if date_of_service and date_of_service < date.today():
            raise forms.ValidationError("Date cannot be in the past.")
        return date_of_service
    
    def clean(self):
        cleaned_data = super().clean()
        # Add any cross-field validation here
        return cleaned_data
