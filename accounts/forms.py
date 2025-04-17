from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import CustomerProfile
from quotes.models import Booking
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

class CustomLoginForm(forms.Form):
    username = forms.CharField(
        label="Email or Username",
        widget=forms.TextInput(attrs={
            "class": "cmn-input",
            "placeholder": "Enter your username or email",
            "autofocus": "autofocus",
        })
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            "class": "cmn-input",
            "placeholder": "Enter your password",
        })
    )

class CustomUserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'cmn-input'

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("This email is already registered.")
        return email

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'cmn-input'

class CustomerProfileForm(forms.ModelForm):
    class Meta:
        model = CustomerProfile
        fields = ['full_name', 'phone']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'cmn-input'


class RescheduleBookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['date', 'hour']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'cmn-input'}),
            'hour': forms.TimeInput(attrs={'type': 'time', 'class': 'cmn-input'}),
        }

from django.contrib.auth.forms import PasswordResetForm

class StyledPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs.update({
            "class": "cmn-input",
            "placeholder": "Enter your email"
        })

from django.contrib.auth.forms import SetPasswordForm

class StyledSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "cmn-input",
                "placeholder": field.label,
            })



