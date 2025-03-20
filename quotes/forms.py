from django import forms
from .models import Quote, Service

class CleaningQuoteForm(forms.ModelForm):
    num_bedrooms = forms.IntegerField(label="Number of Bedrooms")
    square_feet = forms.IntegerField(label="Square Footage")

    class Meta:
        model = Quote
        fields = ["service", "num_bedrooms", "square_feet", "date"]
        widgets = {
            "date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service"].queryset = Service.objects.filter(category__name="Cleaning")

class HandymanQuoteForm(forms.ModelForm):
    hours_requested = forms.IntegerField(label="Hours to Book")

    class Meta:
        model = Quote
        fields = ["service", "hours_requested", "date"]
        widgets = {
            "date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service"].queryset = Service.objects.filter(category__name="Handyman")

