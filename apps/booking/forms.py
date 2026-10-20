from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Prefetch
from django.utils import timezone

from apps.accounts.models import User
from apps.booking.models import PriceVariable, PriceVariableCategory, Property, TaxSettings
from apps.booking.pricing import service_needs_destination
from apps.content.models import ServicePage


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={"autocomplete": "email"}))


class SignupForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"placeholder": "you@example.com", "autocomplete": "email"}),
    )
    phone = forms.CharField(
        max_length=32,
        required=False,
        label="Phone",
        widget=forms.TextInput(attrs={"placeholder": "(347) 555-0100", "autocomplete": "tel"}),
    )
    password = forms.CharField(
        label="Password",
        min_length=8,
        widget=forms.PasswordInput(attrs={"placeholder": "At least 8 characters", "autocomplete": "new-password"}),
    )
    role = forms.ChoiceField(
        label="This account is for",
        choices=[
            (User.Role.CUSTOMER, "Booking for myself"),
            (User.Role.PROPERTY_MANAGER, "Managing properties"),
        ],
        initial=User.Role.CUSTOMER,
        widget=forms.RadioSelect,
    )

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists. Log in instead.")
        return email


class QuoteServiceForm(forms.Form):
    service = forms.ModelChoiceField(queryset=ServicePage.objects.none(), empty_label=None)

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)
        self.fields["service"].queryset = ServicePage.objects.filter(is_active=True, is_bookable=True).order_by("name")


class QuotePropertyForm(forms.Form):
    saved_property = forms.ModelChoiceField(queryset=Property.objects.none(), required=False, empty_label="Enter a new address")
    street = forms.CharField(
        max_length=200,
        required=False,
        label="Street",
        widget=forms.TextInput(attrs={"placeholder": "123 Example Street", "autocomplete": "street-address"}),
    )
    borough = forms.ChoiceField(choices=Property.Borough.choices, label="Area")
    kind = forms.ChoiceField(choices=Property.Kind.choices, label="Property type")
    sqft_band = forms.ChoiceField(choices=Property.SqftBand.choices, label="Size")
    preferred_date = forms.DateField(
        required=False,
        label="Preferred day",
        help_text="Optional. Staff confirm this before the job is booked.",
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
    )

    def __init__(self, *args, user=None, service=None, option_ids=None, **kwargs):
        self.service = service
        self.needs_destination = service_needs_destination(service)
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)
        if user is not None and getattr(user, "is_authenticated", False):
            self.fields["saved_property"].queryset = user.properties.all()
        else:
            self.fields.pop("saved_property", None)
        if self.needs_destination:
            self.fields["dest_street"] = forms.CharField(
                max_length=200,
                required=False,
                label="Street",
                widget=forms.TextInput(attrs={"placeholder": "123 Example Street", "autocomplete": "street-address"}),
            )
            self.fields["dest_borough"] = forms.ChoiceField(choices=Property.Borough.choices, label="Area")
            self.fields["dest_kind"] = forms.ChoiceField(choices=Property.Kind.choices, label="Property type")
            self.fields["dest_sqft_band"] = forms.ChoiceField(choices=Property.SqftBand.choices, label="Size")
        self.fields["preferred_date"].widget.attrs["min"] = timezone.localdate().isoformat()
        self.price_categories = []
        if service is None:
            return
        selected = {int(pk) for pk in (option_ids or []) if str(pk).isdigit()}
        categories = (
            PriceVariableCategory.objects.filter(is_active=True, services=service)
            .prefetch_related(Prefetch("variables", queryset=PriceVariable.objects.filter(is_active=True)))
            .order_by("sort_order", "name")
        )
        for category in categories:
            variables = list(category.variables.all())
            if not variables:
                continue
            field_name = f"option_{category.pk}"
            if category.input_type == PriceVariableCategory.InputType.ADDON:
                self.fields[field_name] = forms.MultipleChoiceField(
                    required=False,
                    label=category.name,
                    choices=[(str(variable.pk), variable.name) for variable in variables],
                    widget=forms.CheckboxSelectMultiple,
                )
                self.fields[field_name].initial = [str(variable.pk) for variable in variables if variable.pk in selected]
            else:
                self.fields[field_name] = forms.ChoiceField(
                    required=True,
                    label=category.name,
                    choices=[(str(variable.pk), variable.name) for variable in variables],
                    widget=forms.RadioSelect,
                )
                match = next((str(variable.pk) for variable in variables if variable.pk in selected), "")
                self.fields[field_name].initial = match
            self.price_categories.append(category)
        self.fields["parking_notes"] = forms.CharField(
            required=False,
            label="Parking instructions",
            widget=forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Where the crew should park, a garage code, or a loading zone.",
                }
            ),
        )

    def option_fields(self):
        return [self[f"option_{category.pk}"] for category in self.price_categories]

    def selected_option_ids(self):
        ids = []
        for category in self.price_categories:
            raw = self.cleaned_data.get(f"option_{category.pk}")
            if category.input_type == PriceVariableCategory.InputType.ADDON:
                ids.extend(int(pk) for pk in (raw or []))
            elif raw:
                ids.append(int(raw))
        return ids

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("saved_property") and not (cleaned.get("street") or "").strip():
            self.add_error("street", "Enter the street address.")
        if self.needs_destination and not (cleaned.get("dest_street") or "").strip():
            self.add_error("dest_street", "Enter the drop-off street.")
        preferred = cleaned.get("preferred_date")
        if preferred and preferred < timezone.localdate():
            self.add_error("preferred_date", "Choose today or a later day.")
        return cleaned

    def origin_data(self):
        return {
            "label": "",
            "street": self.cleaned_data["street"].strip(),
            "unit": "",
            "borough": self.cleaned_data["borough"],
            "kind": self.cleaned_data["kind"],
            "sqft_band": self.cleaned_data["sqft_band"],
        }

    def destination_data(self):
        return {
            "label": "",
            "street": self.cleaned_data["dest_street"].strip(),
            "unit": "",
            "borough": self.cleaned_data["dest_borough"],
            "kind": self.cleaned_data["dest_kind"],
            "sqft_band": self.cleaned_data["dest_sqft_band"],
        }


class TaxSettingsForm(forms.ModelForm):
    class Meta:
        model = TaxSettings
        fields = ["tax_rate", "is_active"]
        labels = {
            "tax_rate": "Tax percent",
            "is_active": "Add tax to quotes",
        }
        help_texts = {
            "tax_rate": "8.875 means 8.875 percent. Tax is added after the discount.",
            "is_active": "Turn this off to charge no tax on new calculations.",
        }

    def clean_tax_rate(self):
        rate = self.cleaned_data["tax_rate"]
        if rate < 0 or rate > 100:
            raise forms.ValidationError("Enter a tax rate from 0 to 100.")
        return rate


class QuoteContactForm(forms.Form):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)

    contact_name = forms.CharField(
        max_length=160,
        label="Name",
        widget=forms.TextInput(attrs={"placeholder": "Full name", "autocomplete": "name"}),
    )
    contact_email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"placeholder": "you@example.com", "autocomplete": "email"}),
    )
    contact_phone = forms.CharField(
        max_length=32,
        label="Phone",
        widget=forms.TextInput(attrs={"placeholder": "(347) 555-0100", "autocomplete": "tel"}),
    )
    notes = forms.CharField(
        required=False,
        label="Notes",
        widget=forms.Textarea(attrs={"rows": 4, "placeholder": "Building rules, elevator window, or anything else the crew should know."}),
    )
    create_account = forms.BooleanField(required=False, label="Create an account so I can see this quote later")
    password = forms.CharField(
        required=False,
        label="Password",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("create_account") and not cleaned.get("password"):
            self.add_error("password", "Choose a password to create an account.")
        return cleaned


class QuoteAdjustForm(forms.Form):
    discount_kind = forms.ChoiceField(
        choices=[("amount", "Amount ($)"), ("percent", "Percent (%)")],
        initial="amount",
        label="Discount type",
    )
    discount_value = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0, label="Discount")
    extra_label = forms.CharField(max_length=200, required=False, label="Extra charge label")
    extra_amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0, required=False, label="Extra charge amount")

    def clean(self):
        cleaned = super().clean()
        kind = cleaned.get("discount_kind")
        value = cleaned.get("discount_value")
        if kind == "percent" and value is not None and value > 100:
            self.add_error("discount_value", "A percent discount cannot be more than 100.")
        return cleaned


class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = ["label", "street", "unit", "borough", "kind", "sqft_band"]
        labels = {"borough": "Area", "kind": "Property type", "sqft_band": "Size"}
