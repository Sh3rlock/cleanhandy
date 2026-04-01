from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from blog.models import BlogPost
from quotes.models import Service


class StaticViewSitemap(Sitemap):
    """Indexable public routes that are not tied to a queryset row."""

    priority = 0.6
    changefreq = "weekly"

    def items(self):
        return [
            "home",
            "about",
            "contact",
            "blog_list",
            "faq",
            "terms",
            "privacy",
            "cleaning_services",
            "commercial_services",
            "handyman_services",
            "home_cleaning_quote",
            "office_cleaning_quote",
            "cleaning_booking",
            "handyman_booking",
            "office_cleaning_booking",
        ]

    def location(self, item):
        return reverse(item)

    def lastmod(self, item):
        return None


class ServiceSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return Service.objects.filter(robots_index=True).select_related("category")

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()


class BlogPostSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return BlogPost.objects.filter(robots_index=True).order_by("-updated_at")

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()
