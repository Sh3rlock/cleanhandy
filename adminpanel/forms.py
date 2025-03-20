from django import forms
from quotes.models import Service, ServiceCategory

class ServiceCategoryForm(forms.ModelForm):
    class Meta:
        model = ServiceCategory
        fields = ["name"]

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ["category", "name", "description"]
