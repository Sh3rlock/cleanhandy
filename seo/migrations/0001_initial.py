# Generated manually for SEO app

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SitePageSEO",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("seo_title", models.CharField(blank=True, help_text="If empty, the page title or name is used.", max_length=255)),
                ("meta_description", models.TextField(blank=True, help_text="If empty, a short excerpt is generated from content when possible.")),
                ("meta_keywords", models.CharField(blank=True, max_length=500)),
                ("og_title", models.CharField(blank=True, help_text="If empty, SEO title or page title is used.", max_length=255)),
                ("og_description", models.TextField(blank=True, help_text="If empty, meta description is used.")),
                ("og_image", models.ImageField(blank=True, help_text="Recommended 1200×630px. Uses site default if empty.", null=True, upload_to="seo/og/")),
                ("canonical_url", models.URLField(blank=True, help_text="Full URL. If empty, the current public URL is used.", max_length=500)),
                ("robots_index", models.BooleanField(default=True, help_text="If unchecked, adds noindex.")),
                ("robots_follow", models.BooleanField(default=True, help_text="If unchecked, adds nofollow.")),
                ("schema_type", models.CharField(choices=[("WebPage", "WebPage"), ("Article", "Article"), ("LocalBusiness", "LocalBusiness"), ("Service", "Service"), ("FAQPage", "FAQPage"), ("BlogPosting", "BlogPosting")], default="WebPage", max_length=32)),
                ("page_key", models.CharField(choices=[("home", "Home"), ("about", "About"), ("contact", "Contact"), ("blog_index", "Blog index"), ("faq", "FAQ"), ("terms", "Terms"), ("privacy", "Privacy"), ("cleaning_services", "Cleaning services listing"), ("commercial_services", "Commercial services listing"), ("handyman_services", "Handyman services listing"), ("home_cleaning_quote", "Home cleaning quote / booking"), ("office_cleaning_quote", "Office cleaning quote"), ("office_cleaning_booking", "Office cleaning booking"), ("cleaning_booking", "Cleaning booking"), ("handyman_booking", "Handyman booking")], db_index=True, max_length=64, unique=True)),
                ("notes", models.CharField(blank=True, help_text="Internal note for editors (not shown on site).", max_length=255)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Site page SEO",
                "verbose_name_plural": "Site page SEO",
            },
        ),
    ]
