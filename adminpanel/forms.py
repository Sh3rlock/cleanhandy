from django import forms
from quotes.models import Service, ServiceCategory, Quote
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

        if self.instance and self.instance.hour and self.instance.hours_requested:
            start = self.instance.hour
            end = (datetime.combine(date.today(), start) + timedelta(hours=self.instance.hours_requested)).time()
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

