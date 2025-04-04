from django import forms
from .models import Quote, Service, HomeType, SquareFeetOption
from datetime import time, datetime, timedelta

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
        widget=forms.DateInput(attrs={"type": "date", "class": "cmn-input"})
    )

    hour = forms.ChoiceField(
        label="Select Hour",
        widget=forms.Select(attrs={"class": "cmn-input"})
    )

    class Meta:
        model = Quote
        fields = [
            "service",
            "square_feet_options",  # new ManyToMany
            "home_types",           # new ManyToMany
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
        while t.time() <= time(17, 0):
            time_slots.append((t.strftime("%H:%M"), t.strftime("%H:%M")))
            t += timedelta(minutes=30)

        self.fields["hour"].choices = time_slots


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
        while t.time() <= time(17, 0):
            time_slots.append((t.strftime("%H:%M"), t.strftime("%H:%M")))
            t += timedelta(minutes=30)

        self.fields["hour"].choices = time_slots




