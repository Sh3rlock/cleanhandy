from django import forms
from quotes.models import Service, ServiceCategory, Quote, PriceVariable, PriceVariableCategory, TaxSettings
from datetime import datetime, timedelta, date

class ServiceCategoryForm(forms.ModelForm):
    class Meta:
        model = ServiceCategory
        fields = ["name"]

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ["category", "name", "description"]

def generate_time_choices():
    t = datetime.strptime("08:00", "%H:%M")
    end = datetime.strptime("18:00", "%H:%M")
    choices = []
    while t <= end:
        label = t.strftime("%H:%M")
        choices.append((label, label))
        t += timedelta(minutes=30)
    return choices

class AdminQuoteForm(forms.ModelForm):
    start_hour = forms.ChoiceField(
        label="Start Hour",
        choices=generate_time_choices(),
        widget=forms.Select(attrs={"class": "form-select"})
    )
    end_hour = forms.ChoiceField(
        label="End Hour",
        choices=generate_time_choices(),
        widget=forms.Select(attrs={"class": "form-select"})
    )

    class Meta:
        model = Quote
        fields = [
            "service", "zip_code", "job_description", "price", "status",
            "date", "start_hour", "end_hour"
        ]
        widgets = {
            "service": forms.Select(attrs={"class": "form-select"}),
            "zip_code": forms.TextInput(attrs={"class": "form-control"}),
            "job_description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "price": forms.NumberInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["service"].queryset = Service.objects.all()

        # If we're editing an existing quote, pre-fill the fields
        if self.instance and self.instance.hour and self.instance.hours_requested:
            start = self.instance.hour
            # Convert Decimal to float for timedelta calculation
            hours = float(self.instance.hours_requested) if self.instance.hours_requested else 2.0
            end_dt = (
                datetime.combine(date.today(), start)
                + timedelta(hours=hours)
            )
            end = end_dt.time()

            self.fields["start_hour"].initial = start.strftime("%H:%M")
            self.fields["end_hour"].initial = end.strftime("%H:%M")

    def clean(self):
        cleaned_data = super().clean()
        start_str = cleaned_data.get("start_hour")
        end_str = cleaned_data.get("end_hour")

        if start_str and end_str:
            start = datetime.strptime(start_str, "%H:%M")
            end = datetime.strptime(end_str, "%H:%M")
            if end <= start:
                raise forms.ValidationError("End hour must be after start hour.")

        return cleaned_data

    def save(self, commit=True):
        start = datetime.strptime(self.cleaned_data["start_hour"], "%H:%M").time()
        end = datetime.strptime(self.cleaned_data["end_hour"], "%H:%M").time()
        duration = (datetime.combine(date.today(), end) - datetime.combine(date.today(), start)).seconds // 3600

        self.instance.hour = start
        self.instance.hours_requested = duration
        return super().save(commit)

class PriceVariableCategoryForm(forms.ModelForm):
    class Meta:
        model = PriceVariableCategory
        fields = ["name", "description", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "cmn-input", "placeholder": "e.g., Crew/Size/Hours, Home type, Number of Bathrooms"}),
            "description": forms.Textarea(attrs={"class": "cmn-input", "rows": 3, "placeholder": "Optional description"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set is_active to True by default when creating a new instance
        if not self.instance.pk:
            self.fields["is_active"].initial = True

class PriceVariableForm(forms.ModelForm):
    class Meta:
        model = PriceVariable
        fields = ["category", "variable_name", "price", "duration", "description", "is_active"]
        widgets = {
            "category": forms.Select(attrs={"class": "cmn-input"}),
            "variable_name": forms.TextInput(attrs={"class": "cmn-input", "placeholder": "e.g., Studio, 1 Bathroom, Manhattan Parking fee"}),
            "price": forms.NumberInput(attrs={"class": "cmn-input", "step": "0.01", "min": "0"}),
            "duration": forms.NumberInput(attrs={"class": "cmn-input", "min": "0", "placeholder": "Duration in minutes (optional)"}),
            "description": forms.Textarea(attrs={"class": "cmn-input", "rows": 3, "placeholder": "Optional description or notes"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter to only show active categories
        self.fields["category"].queryset = PriceVariableCategory.objects.filter(is_active=True).order_by("name")
        # Set is_active to True by default when creating a new instance
        if not self.instance.pk:
            self.fields["is_active"].initial = True

class TaxSettingsForm(forms.ModelForm):
    class Meta:
        model = TaxSettings
        fields = ["tax_rate", "description", "is_active"]
        widgets = {
            "tax_rate": forms.NumberInput(attrs={"class": "cmn-input", "step": "0.001", "min": "0", "placeholder": "e.g., 8.750 for 8.750%"}),
            "description": forms.TextInput(attrs={"class": "cmn-input", "placeholder": "e.g., NYC Sales Tax"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

