from django import forms
from .models import Quote, Service
from django import forms
from .models import Quote, Service
from datetime import time, datetime, timedelta

class CleaningQuoteForm(forms.ModelForm):
    zip_code = forms.CharField(
        label="ZIP Code",
        max_length=10,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "ZIP Code"})
    )

    job_description = forms.CharField(
        label="Tell us about the job",
        required=True,
        widget=forms.Textarea(attrs={
            "class": "form-control",
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
            "class": "form-control",
            "placeholder": "Enter number of hours",
            "min": 2  # Enforces min value on the frontend
        })
    )

    date = forms.DateField(
        label="Select Date",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )

    hour = forms.ChoiceField(
        label="Select Hour",
        widget=forms.Select(attrs={"class": "form-select"})
    )

    class Meta:
        model = Quote
        fields = ["service", "zip_code", "job_description", "hours_requested", "date", "hour"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["service"].queryset = Service.objects.filter(category__name="Cleaning")

        # Default hour choices (9:00 to 17:00, every 30 min)
        time_slots = []
        t = datetime.strptime("09:00", "%H:%M")
        while t.time() <= time(17, 0):
            time_slots.append((t.strftime("%H:%M"), t.strftime("%H:%M")))
            t += timedelta(minutes=30)

        self.fields["hour"].choices = time_slots

class HandymanQuoteForm(forms.ModelForm):
    zip_code = forms.CharField(
        label="ZIP Code",
        max_length=10,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "ZIP Code"})
    )

    job_description = forms.CharField(
        label="Tell us about the job",
        required=True,
        widget=forms.Textarea(attrs={
            "class": "form-control",
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
            "class": "form-control",
            "placeholder": "Enter number of hours",
            "min": 2  # Enforces min value on the frontend
        })
    )

    date = forms.DateField(
        label="Select Date",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )

    hour = forms.ChoiceField(
        label="Select Hour",
        widget=forms.Select(attrs={"class": "form-select"})
    )

    class Meta:
        model = Quote
        fields = ["service", "zip_code", "job_description", "hours_requested", "date", "hour"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["service"].queryset = Service.objects.filter(category__name="Handyman")

        # Default hour choices (9:00 to 17:00, every 30 min)
        time_slots = []
        t = datetime.strptime("09:00", "%H:%M")
        while t.time() <= time(17, 0):
            time_slots.append((t.strftime("%H:%M"), t.strftime("%H:%M")))
            t += timedelta(minutes=30)

        self.fields["hour"].choices = time_slots




