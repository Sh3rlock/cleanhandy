# SEO fields on Service and AboutContent

from django.db import migrations, models


def populate_service_slugs(apps, schema_editor):
    from django.utils.text import slugify

    Service = apps.get_model("quotes", "Service")
    for s in Service.objects.all():
        if s.slug:
            continue
        base = slugify(s.name or f"service-{s.pk}")
        slug = base
        n = 1
        while Service.objects.filter(slug=slug).exclude(pk=s.pk).exists():
            slug = f"{base}-{n}"
            n += 1
        s.slug = slug
        s.save(update_fields=["slug"])


class Migration(migrations.Migration):

    dependencies = [
        ("quotes", "0059_add_payment_status_to_quotes"),
    ]

    operations = [
        migrations.AddField(
            model_name="service",
            name="seo_title",
            field=models.CharField(blank=True, help_text="If empty, the page title or name is used.", max_length=255),
        ),
        migrations.AddField(
            model_name="service",
            name="meta_description",
            field=models.TextField(blank=True, help_text="If empty, a short excerpt is generated from content when possible."),
        ),
        migrations.AddField(
            model_name="service",
            name="meta_keywords",
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name="service",
            name="og_title",
            field=models.CharField(blank=True, help_text="If empty, SEO title or page title is used.", max_length=255),
        ),
        migrations.AddField(
            model_name="service",
            name="og_description",
            field=models.TextField(blank=True, help_text="If empty, meta description is used."),
        ),
        migrations.AddField(
            model_name="service",
            name="og_image",
            field=models.ImageField(blank=True, help_text="Recommended 1200×630px. Uses site default if empty.", null=True, upload_to="seo/og/"),
        ),
        migrations.AddField(
            model_name="service",
            name="canonical_url",
            field=models.URLField(blank=True, help_text="Full URL. If empty, the current public URL is used.", max_length=500),
        ),
        migrations.AddField(
            model_name="service",
            name="robots_index",
            field=models.BooleanField(default=True, help_text="If unchecked, adds noindex."),
        ),
        migrations.AddField(
            model_name="service",
            name="robots_follow",
            field=models.BooleanField(default=True, help_text="If unchecked, adds nofollow."),
        ),
        migrations.AddField(
            model_name="service",
            name="schema_type",
            field=models.CharField(
                choices=[
                    ("WebPage", "WebPage"),
                    ("Article", "Article"),
                    ("LocalBusiness", "LocalBusiness"),
                    ("Service", "Service"),
                    ("FAQPage", "FAQPage"),
                    ("BlogPosting", "BlogPosting"),
                ],
                default="Service",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="service",
            name="slug",
            field=models.SlugField(blank=True, db_index=True, max_length=120, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="service",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.RunPython(populate_service_slugs, migrations.RunPython.noop),
        migrations.AddField(
            model_name="aboutcontent",
            name="seo_title",
            field=models.CharField(blank=True, help_text="If empty, the page title or name is used.", max_length=255),
        ),
        migrations.AddField(
            model_name="aboutcontent",
            name="meta_description",
            field=models.TextField(blank=True, help_text="If empty, a short excerpt is generated from content when possible."),
        ),
        migrations.AddField(
            model_name="aboutcontent",
            name="meta_keywords",
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name="aboutcontent",
            name="og_title",
            field=models.CharField(blank=True, help_text="If empty, SEO title or page title is used.", max_length=255),
        ),
        migrations.AddField(
            model_name="aboutcontent",
            name="og_description",
            field=models.TextField(blank=True, help_text="If empty, meta description is used."),
        ),
        migrations.AddField(
            model_name="aboutcontent",
            name="og_image",
            field=models.ImageField(blank=True, help_text="Recommended 1200×630px. Uses site default if empty.", null=True, upload_to="seo/og/"),
        ),
        migrations.AddField(
            model_name="aboutcontent",
            name="canonical_url",
            field=models.URLField(blank=True, help_text="Full URL. If empty, the current public URL is used.", max_length=500),
        ),
        migrations.AddField(
            model_name="aboutcontent",
            name="robots_index",
            field=models.BooleanField(default=True, help_text="If unchecked, adds noindex."),
        ),
        migrations.AddField(
            model_name="aboutcontent",
            name="robots_follow",
            field=models.BooleanField(default=True, help_text="If unchecked, adds nofollow."),
        ),
        migrations.AddField(
            model_name="aboutcontent",
            name="schema_type",
            field=models.CharField(
                choices=[
                    ("WebPage", "WebPage"),
                    ("Article", "Article"),
                    ("LocalBusiness", "LocalBusiness"),
                    ("Service", "Service"),
                    ("FAQPage", "FAQPage"),
                    ("BlogPosting", "BlogPosting"),
                ],
                default="LocalBusiness",
                max_length=32,
            ),
        ),
    ]
