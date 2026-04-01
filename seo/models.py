from django.db import models


class SEOSchemaType(models.TextChoices):
    WEB_PAGE = "WebPage", "WebPage"
    ARTICLE = "Article", "Article"
    LOCAL_BUSINESS = "LocalBusiness", "LocalBusiness"
    SERVICE = "Service", "Service"
    FAQ_PAGE = "FAQPage", "FAQPage"
    BLOG_POSTING = "BlogPosting", "BlogPosting"


class SEOFields(models.Model):
    """
    Abstract SEO mixin for public content models.
    Fallback resolution is implemented in seo.utils (not on the model).
    """

    seo_title = models.CharField(
        max_length=255,
        blank=True,
        help_text="If empty, the page title or name is used.",
    )
    meta_description = models.TextField(
        blank=True,
        help_text="If empty, a short excerpt is generated from content when possible.",
    )
    meta_keywords = models.CharField(max_length=500, blank=True)
    og_title = models.CharField(
        max_length=255,
        blank=True,
        help_text="If empty, SEO title or page title is used.",
    )
    og_description = models.TextField(
        blank=True,
        help_text="If empty, meta description is used.",
    )
    og_image = models.ImageField(
        upload_to="seo/og/",
        blank=True,
        null=True,
        help_text="Recommended 1200×630px. Uses site default if empty.",
    )
    canonical_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="Full URL. If empty, the current public URL is used.",
    )
    robots_index = models.BooleanField(
        default=True,
        help_text="If unchecked, adds noindex.",
    )
    robots_follow = models.BooleanField(
        default=True,
        help_text="If unchecked, adds nofollow.",
    )
    schema_type = models.CharField(
        max_length=32,
        choices=SEOSchemaType.choices,
        default=SEOSchemaType.WEB_PAGE,
    )

    class Meta:
        abstract = True


class SitePageKey(models.TextChoices):
    """Built-in keys for templates that are not driven by a single model."""

    HOME = "home", "Home"
    ABOUT = "about", "About"
    CONTACT = "contact", "Contact"
    BLOG_INDEX = "blog_index", "Blog index"
    FAQ = "faq", "FAQ"
    TERMS = "terms", "Terms"
    PRIVACY = "privacy", "Privacy"
    CLEANING_SERVICES = "cleaning_services", "Cleaning services listing"
    COMMERCIAL_SERVICES = "commercial_services", "Commercial services listing"
    HANDYMAN_SERVICES = "handyman_services", "Handyman services listing"
    HOME_CLEANING_QUOTE = "home_cleaning_quote", "Home cleaning quote / booking"
    OFFICE_CLEANING_QUOTE = "office_cleaning_quote", "Office cleaning quote"
    OFFICE_CLEANING_BOOKING = "office_cleaning_booking", "Office cleaning booking"
    CLEANING_BOOKING = "cleaning_booking", "Cleaning booking"
    HANDYMAN_BOOKING = "handyman_booking", "Handyman booking"


class SitePageSEO(SEOFields):
    """
    Editable SEO for static routes. Use page_key to match a URL group.
    Optional: bind to one canonical path per key.
    """

    page_key = models.CharField(
        max_length=64,
        unique=True,
        choices=SitePageKey.choices,
        db_index=True,
    )
    notes = models.CharField(
        max_length=255,
        blank=True,
        help_text="Internal note for editors (not shown on site).",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site page SEO"
        verbose_name_plural = "Site page SEO"

    def __str__(self):
        return self.get_page_key_display()
