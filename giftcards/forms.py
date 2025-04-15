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

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount
