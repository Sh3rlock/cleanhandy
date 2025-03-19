from django import forms
from .models import Quote

class QuoteForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = ["name", "email", "phone", "service", "date"]
        widgets = {
            "date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }