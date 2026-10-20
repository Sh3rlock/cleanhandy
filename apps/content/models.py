import uuid

from django.db import models
from django.urls import reverse


def _lines(text):
    items = []
    for line in (text or "").splitlines():
        cleaned = line.strip().lstrip("-").strip()
        if cleaned:
            items.append(cleaned)
    return items


class SEOFields(models.Model):
    seo_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    canonical_path = models.CharField(max_length=300, blank=True)
    og_title = models.CharField(max_length=120, blank=True)
    og_description = models.CharField(max_length=300, blank=True)
    og_image = models.URLField(blank=True)
    noindex = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def public_path(self):
        if self.canonical_path:
            path = self.canonical_path
            return path if path.startswith("/") else f"/{path}"
        return self.get_absolute_url()


class ServicePage(SEOFields):
    class Category(models.TextChoices):
        MOVING = "moving", "Moving"
        MOVE_CLEANING = "move_cleaning", "Move-in / move-out cleaning"
        COMMERCIAL = "commercial", "Commercial cleaning"
        ADDITIONAL = "additional", "Additional services"

    class Menu(models.TextChoices):
        NONE = "", "Not in the header"
        MOVING = "moving", "Moving"
        CLEANING = "cleaning", "Cleaning"
        COMMERCIAL = "commercial", "Commercial"

    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=160, unique=True)
    category = models.CharField(max_length=32, choices=Category.choices)
    menu = models.CharField(max_length=32, choices=Menu.choices, blank=True, default="")
    menu_order = models.PositiveIntegerField(default=0)
    short_description = models.TextField()
    who_it_is_for = models.TextField(blank=True)
    included = models.TextField(blank=True, help_text="One item per line.")
    checklist = models.TextField(blank=True, help_text="One item per line.")
    add_ons = models.TextField(blank=True, help_text="One item per line.")
    timeline = models.TextField(blank=True)
    pricing_factors = models.TextField(blank=True)
    primary_keyword = models.CharField(max_length=120, blank=True)
    secondary_keywords = models.TextField(blank=True, help_text="Comma-separated. Used in admin, not as a keywords meta tag.")
    is_bookable = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    related_services = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        related_name="related_from",
    )
    locations = models.ManyToManyField("content.LocationPage", blank=True, related_name="services")
    solutions = models.ManyToManyField("content.SolutionPage", blank=True, related_name="services")

    class Meta:
        ordering = ["menu_order", "name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("service_page", kwargs={"slug": self.slug})

    def included_items(self):
        return _lines(self.included)

    def checklist_items(self):
        return _lines(self.checklist)

    def addon_items(self):
        return _lines(self.add_ons)


class LocationPage(SEOFields):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120, unique=True)
    introduction = models.TextField()
    neighborhoods = models.TextField(help_text="One neighborhood per line.")
    body = models.TextField()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("location_page", kwargs={"slug": self.slug})

    def neighborhood_items(self):
        return _lines(self.neighborhoods)


class SolutionPage(SEOFields):
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=160, unique=True)
    introduction = models.TextField()
    body = models.TextField()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("solution_page", kwargs={"slug": self.slug})


class Article(SEOFields):
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=180, unique=True)
    service = models.ForeignKey(ServicePage, on_delete=models.PROTECT, related_name="articles")
    introduction = models.TextField()
    body = models.TextField(help_text="One paragraph per line. Lines starting with '- ' become a list.")

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("article_page", kwargs={"slug": self.slug})

    def body_blocks(self):
        blocks = []
        list_items = []
        for line in self.body.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("- "):
                list_items.append(stripped[2:].strip())
                continue
            if list_items:
                blocks.append(("list", list_items))
                list_items = []
            blocks.append(("p", stripped))
        if list_items:
            blocks.append(("list", list_items))
        return blocks


class FAQ(models.Model):
    question = models.CharField(max_length=240)
    answer = models.TextField()
    service = models.ForeignKey(ServicePage, null=True, blank=True, on_delete=models.CASCADE, related_name="faqs")
    location = models.ForeignKey(LocationPage, null=True, blank=True, on_delete=models.CASCADE, related_name="faqs")
    solution = models.ForeignKey(SolutionPage, null=True, blank=True, on_delete=models.CASCADE, related_name="faqs")
    show_on_homepage = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "FAQ"

    def __str__(self):
        return self.question


class Review(models.Model):
    customer_label = models.CharField(max_length=160, help_text="Who hired the company, without inventing a star rating.")
    situation = models.TextField()
    service = models.ForeignKey(ServicePage, on_delete=models.PROTECT, related_name="reviews")
    borough = models.CharField(max_length=80)
    result = models.TextField()
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.customer_label


class CaseStudy(models.Model):
    title = models.CharField(max_length=180)
    situation = models.TextField()
    service = models.ForeignKey(ServicePage, on_delete=models.PROTECT, related_name="case_studies")
    borough = models.CharField(max_length=80)
    result = models.TextField()
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Case studies"

    def __str__(self):
        return self.title


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-subscribed_at"]

    def __str__(self):
        return self.email
