from django.contrib import admin

from .models import SitePageSEO


@admin.register(SitePageSEO)
class SitePageSEOAdmin(admin.ModelAdmin):
    list_display = ("page_key", "seo_title", "robots_index", "robots_follow", "updated_at")
    list_filter = ("page_key", "robots_index", "robots_follow")
    search_fields = ("seo_title", "meta_description", "meta_keywords", "notes")
    readonly_fields = ("updated_at",)
    fieldsets = (
        (
            "Page",
            {
                "fields": ("page_key", "notes"),
                "description": "One row per built-in page (home, contact, FAQ, etc.).",
            },
        ),
        (
            "SEO",
            {
                "fields": (
                    "seo_title",
                    "meta_description",
                    "meta_keywords",
                    "og_title",
                    "og_description",
                    "og_image",
                    "canonical_url",
                    "robots_index",
                    "robots_follow",
                    "schema_type",
                ),
            },
        ),
        ("Timestamps", {"fields": ("updated_at",), "classes": ("collapse",)}),
    )
