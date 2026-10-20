from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.content.models import Article, LocationPage, ServicePage, SolutionPage


class NamedPath:
    def __init__(self, path, updated_at=None):
        self.path = path
        self.updated_at = updated_at

    def get_absolute_url(self):
        return self.path


class PublicSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        pages = [
            NamedPath("/"),
            NamedPath("/pricing/"),
            NamedPath("/about/"),
            NamedPath("/reviews/"),
            NamedPath("/our-work/"),
            NamedPath("/faq/"),
            NamedPath("/contact/"),
            NamedPath("/terms/"),
            NamedPath("/privacy/"),
            NamedPath("/areas/"),
            NamedPath("/resources/"),
            NamedPath("/solutions/property-managers/"),
        ]
        services = list(ServicePage.objects.filter(is_active=True, noindex=False))
        locations = list(LocationPage.objects.filter(noindex=False))
        solutions = list(SolutionPage.objects.filter(noindex=False))
        articles = list(Article.objects.filter(noindex=False).select_related("service"))
        return pages + services + locations + solutions + articles

    def location(self, item):
        return item.get_absolute_url()

    def lastmod(self, item):
        return getattr(item, "updated_at", None)


def static_reverse(name):
    return reverse(name)
