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
                "description": (
                    "One row per site section (home, contact, service hubs, booking flows). "
                    "Run: python manage.py seed_site_page_seo — to create starter copy, then edit here. "
                    "For blog posts and individual services, edit SEO on each Blog post / Service."
                ),
            },
        ),
        (
            "Core SEO",
            {
                "description": (
                    "SEO title: shown in search results (often 50–60 characters). "
                    "A suffix like “ | The CleanHandy” may be added from settings if the brand is not already in the title. "
                    "Meta description: snippet text; about 150–160 characters is a good target. "
                    "Keywords: optional, comma-separated."
                ),
                "fields": ("seo_title", "meta_description", "meta_keywords"),
            },
        ),
        (
            "Social / sharing (Open Graph)",
            {
                "description": (
                    "Used when links are shared (Facebook, LinkedIn, etc.). "
                    "If empty, the site uses SEO title, meta description, and SEO_DEFAULT_OG_IMAGE from settings."
                ),
                "fields": ("og_title", "og_description", "og_image"),
            },
        ),
        (
            "Indexing & URL",
            {
                "fields": ("canonical_url", "robots_index", "robots_follow", "schema_type"),
                "description": (
                    "Leave canonical URL empty to use the real page URL. "
                    "Uncheck index or follow only for pages you want excluded from search. "
                    "Schema type drives JSON-LD (e.g. FAQPage for the FAQ page)."
                ),
            },
        ),
        ("Timestamps", {"fields": ("updated_at",), "classes": ("collapse",)}),
    )
