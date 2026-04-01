# SEO fields on BlogPost

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0002_blogpost_short_description"),
    ]

    operations = [
        migrations.AddField(
            model_name="blogpost",
            name="seo_title",
            field=models.CharField(blank=True, help_text="If empty, the page title or name is used.", max_length=255),
        ),
        migrations.AddField(
            model_name="blogpost",
            name="meta_description",
            field=models.TextField(blank=True, help_text="If empty, a short excerpt is generated from content when possible."),
        ),
        migrations.AddField(
            model_name="blogpost",
            name="meta_keywords",
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name="blogpost",
            name="og_title",
            field=models.CharField(blank=True, help_text="If empty, SEO title or page title is used.", max_length=255),
        ),
        migrations.AddField(
            model_name="blogpost",
            name="og_description",
            field=models.TextField(blank=True, help_text="If empty, meta description is used."),
        ),
        migrations.AddField(
            model_name="blogpost",
            name="og_image",
            field=models.ImageField(blank=True, help_text="Recommended 1200×630px. Uses site default if empty.", null=True, upload_to="seo/og/"),
        ),
        migrations.AddField(
            model_name="blogpost",
            name="canonical_url",
            field=models.URLField(blank=True, help_text="Full URL. If empty, the current public URL is used.", max_length=500),
        ),
        migrations.AddField(
            model_name="blogpost",
            name="robots_index",
            field=models.BooleanField(default=True, help_text="If unchecked, adds noindex."),
        ),
        migrations.AddField(
            model_name="blogpost",
            name="robots_follow",
            field=models.BooleanField(default=True, help_text="If unchecked, adds nofollow."),
        ),
        migrations.AddField(
            model_name="blogpost",
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
                default="BlogPosting",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="blogpost",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
