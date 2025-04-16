# giftcards/forms.py
from django import forms
from .models import GiftCard

class GiftCardPurchaseForm(forms.ModelForm):
    class Meta:
        model = GiftCard
        fields = ["amount", "purchaser_email", "recipient_email", "message"]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing_classes = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing_classes} cmn-input".strip()

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount

