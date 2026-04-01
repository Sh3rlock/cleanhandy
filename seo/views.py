from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.http import require_GET


@require_GET
def robots_txt(request):
    site = getattr(settings, "SITE_URL", "https://thecleanhandy.com").rstrip("/")
    sitemap_url = f"{site}/sitemap.xml"
    lines = [
        "User-agent: *",
        "Allow: /",
        "",
        "Disallow: /django-admin/",
        "Disallow: /admin/",
        "Disallow: /accounts/",
        "Disallow: /api/",
        "Disallow: /healthz/",
        "Disallow: /health/",
        "Disallow: /quotes/health/",
        "",
        f"Sitemap: {sitemap_url}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")
