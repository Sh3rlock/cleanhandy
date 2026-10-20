from django import forms

from apps.company.models import CompanyProfile


class SocialLinksForm(forms.ModelForm):
    class Meta:
        model = CompanyProfile
        fields = ["facebook_url", "instagram_url", "youtube_url", "linkedin_url"]
        labels = {
            "facebook_url": "Facebook",
            "instagram_url": "Instagram",
            "youtube_url": "YouTube",
            "linkedin_url": "LinkedIn",
        }
        help_texts = {
            "facebook_url": "Full profile address. Leave blank to hide the icon.",
            "instagram_url": "Full profile address. Leave blank to hide the icon.",
            "youtube_url": "Full channel address. Leave blank to hide the icon.",
            "linkedin_url": "Full profile address. Leave blank to hide the icon.",
        }
