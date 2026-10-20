import re

from django.db import models


class CompanyProfile(models.Model):
    legal_name = models.CharField(max_length=200, default="TheCleanHandy")
    phone = models.CharField(max_length=40, blank=True)
    public_email = models.EmailField(blank=True)
    info_email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    service_area = models.CharField(max_length=200, blank=True)
    street_address = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=120, blank=True)
    region = models.CharField("state", max_length=80, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    hours = models.CharField(max_length=200, blank=True)
    facebook_url = models.URLField(blank=True, help_text="Full profile URL. Leave blank to hide the icon.")
    instagram_url = models.URLField(blank=True, help_text="Full profile URL. Leave blank to hide the icon.")
    youtube_url = models.URLField(blank=True, help_text="Full channel URL. Leave blank to hide the icon.")
    linkedin_url = models.URLField(blank=True, help_text="Full profile URL. Leave blank to hide the icon.")
    founded_year = models.PositiveIntegerField(null=True, blank=True)
    about = models.TextField(blank=True)
    provides_truck = models.BooleanField(
        default=False,
        help_text="When on, moving pages may say a company truck or van is part of the service.",
    )
    provides_packing = models.BooleanField(
        default=False,
        help_text="When on, moving pages may say packing is included.",
    )
    provides_insurance = models.BooleanField(
        default=False,
        help_text="When on, moving pages may say the company carries insurance for the job.",
    )

    class Meta:
        verbose_name = "Company profile"
        verbose_name_plural = "Company profile"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.legal_name

    @property
    def phone_tel(self):
        digits = re.sub(r"\D", "", self.phone)
        if len(digits) == 10:
            return f"+1{digits}"
        if digits:
            return f"+{digits}"
        return ""

    @property
    def has_street_address(self):
        return bool(self.street_address.strip())

    @property
    def headquarters_line(self):
        parts = [self.street_address, self.city, self.region, self.postal_code]
        return ", ".join(part for part in parts if part)

    def moving_capability_lines(self):
        lines = ["TheCleanHandy crews do the moving work. This is not a marketplace that hands the job to an outside pro."]
        if self.provides_truck:
            lines.append("A company truck or van is available when the move needs one.")
        if self.provides_packing:
            lines.append("Packing help can be included in the quote.")
        if self.provides_insurance:
            lines.append("The company can note insurance coverage on the written quote.")
        if not (self.provides_truck or self.provides_packing or self.provides_insurance):
            lines.append(
                "Truck, packing, and insurance details stay off this page until they are turned on in the company profile."
            )
        return lines

    def organization_ready(self):
        return bool(self.legal_name and self.phone and self.website)

    def social_links(self):
        links = []
        for key, label, url in (
            ("facebook", "Facebook", self.facebook_url),
            ("instagram", "Instagram", self.instagram_url),
            ("youtube", "YouTube", self.youtube_url),
            ("linkedin", "LinkedIn", self.linkedin_url),
        ):
            if url.strip():
                links.append({"key": key, "label": label, "url": url.strip()})
        return links


def get_company():
    profile = CompanyProfile.objects.filter(pk=1).first()
    if profile is None:
        profile = CompanyProfile.objects.create(
            pk=1,
            legal_name="TheCleanHandy",
            phone="(347) 652-6165",
            public_email="support@thecleanhandy.com",
            info_email="info@thecleanhandy.com",
            website="https://thecleanhandy.com",
            service_area="New York City, Long Island, and New Jersey",
            city="Astoria",
            region="NY",
            postal_code="11106",
            hours="By appointment",
            about=(
                "TheCleanHandy is a New York City cleaning and moving services company "
                "specializing in move-in and move-out cleaning, moving support, and commercial cleaning. "
                "The company serves residential customers, landlords, property managers, and businesses throughout NYC."
            ),
        )
    return profile
