"""
Default SEO from URL name + SitePageSEO. View context `seo` overrides when provided.
"""
from django.conf import settings

from seo.utils import build_seo_context

URL_NAME_TO_PAGE_KEY = {
    "home": "home",
    "about": "about",
    "contact": "contact",
    "blog": "blog_index",
    "blog_list": "blog_index",
    "terms": "terms",
    "privacy": "privacy",
    "faq": "faq",
    "cleaning_services": "cleaning_services",
    "commercial_services": "commercial_services",
    "handyman_services": "handyman_services",
    "home_cleaning_quote": "home_cleaning_quote",
    "cleaning_booking": "cleaning_booking",
    "handyman_booking": "handyman_booking",
    "office_cleaning_booking": "office_cleaning_booking",
    "office_cleaning_quote": "office_cleaning_quote",
}

# Thin, transactional, or account-only pages — keep out of index by default
NOINDEX_URL_NAMES = frozenset(
    {
        "quote_submitted",
        "quote_submitted_handyman",
        "quote_submitted_post_event_cleaning",
        "home_cleaning_quote_submitted",
        "office_cleaning_quote_submitted",
        "booking_confirmation",
        "password_reset",
        "password_reset_done",
        "password_reset_confirm",
        "password_reset_complete",
        "login",
        "register",
        "profile",
        "my_bookings",
        "activate",
        "activation_pending",
        "booking_detail",
        "booking_submitted_cleaning",
        "booking_submitted_handyman",
        "reschedule_booking",
        "cancel_booking",
        "add_customer_address",
        "healthcheck",
        "health",
    }
)


def seo(request):
    site_name = getattr(settings, "SEO_SITE_NAME", "TheCleanHandy")
    match = getattr(request, "resolver_match", None)
    name = getattr(match, "url_name", None) if match else None
    force_noindex = bool(name and name in NOINDEX_URL_NAMES)
    page_key = URL_NAME_TO_PAGE_KEY.get(name) if name else None
    return build_seo_context(
        request,
        page_key=page_key,
        fallback_title=site_name,
        force_noindex=force_noindex,
    )
