from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path

from apps.accounts.views import (
    AccountLoginView,
    AccountLogoutView,
    accept_quote,
    account_home,
    add_property,
    signup,
)
from apps.booking.payments import quote_payment_received, stripe_webhook
from apps.booking.quote_actions import quote_email_accept, quote_email_decline
from apps.booking.staff_views import (
    staff_calendar,
    staff_dashboard,
    staff_prices,
    staff_quote_detail,
    staff_quote_list,
    staff_quote_pdf,
    staff_send_quote_email,
    staff_social,
    staff_tax,
)
from apps.booking.views import quote_contact, quote_done, quote_property, quote_service, track_event
from apps.content.sitemaps import PublicSitemap
from apps.content.newsletter import staff_newsletter, subscribe, unsubscribe
from apps.content.views import (
    about,
    article_index,
    article_page,
    contact,
    faq_page,
    home,
    llms_txt,
    location_index,
    location_page,
    our_work,
    page_not_found,
    pricing,
    reviews_page,
    robots,
    service_page,
    solution_page,
    privacy,
    terms,
)

admin.site.site_header = "TheCleanHandy"
admin.site.site_title = "TheCleanHandy"
admin.site.index_title = "Content, quotes, and jobs"

sitemaps = {"public": PublicSitemap}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("robots.txt", robots, name="robots"),
    path("llms.txt", llms_txt, name="llms"),
    path("events/", track_event, name="track_event"),
    path("", home, name="home"),
    path("about/", about, name="about"),
    path("pricing/", pricing, name="pricing"),
    path("reviews/", reviews_page, name="reviews"),
    path("our-work/", our_work, name="our_work"),
    path("faq/", faq_page, name="faq"),
    path("contact/", contact, name="contact"),
    path("terms/", terms, name="terms"),
    path("privacy/", privacy, name="privacy"),
    path("areas/", location_index, name="location_index"),
    path("areas/<slug:slug>/", location_page, name="location_page"),
    path("solutions/<slug:slug>/", solution_page, name="solution_page"),
    path("resources/", article_index, name="article_index"),
    path("resources/<slug:slug>/", article_page, name="article_page"),
    path("get-a-quote/", quote_service, name="quote_start"),
    path("get-a-quote/property/", quote_property, name="quote_property"),
    path("get-a-quote/contact/", quote_contact, name="quote_contact"),
    path("get-a-quote/received/", quote_done, name="quote_done"),
    path("quotes/<int:quote_id>/accept/<str:token>/", quote_email_accept, name="quote_email_accept"),
    path("quotes/<int:quote_id>/decline/<str:token>/", quote_email_decline, name="quote_email_decline"),
    path("quotes/<int:quote_id>/paid/", quote_payment_received, name="quote_payment_received"),
    path("stripe/webhook/", stripe_webhook, name="stripe_webhook"),
    path("staff/", staff_dashboard, name="staff_dashboard"),
    path("staff/calendar/", staff_calendar, name="staff_calendar"),
    path("staff/quotes/", staff_quote_list, name="staff_quotes"),
    path("staff/quotes/<int:quote_id>/", staff_quote_detail, name="staff_quote_detail"),
    path("staff/quotes/<int:quote_id>/email/", staff_send_quote_email, name="staff_send_quote_email"),
    path("staff/quotes/<int:quote_id>/pdf/", staff_quote_pdf, name="staff_quote_pdf"),
    path("staff/prices/", staff_prices, name="staff_prices"),
    path("staff/social/", staff_social, name="staff_social"),
    path("staff/tax/", staff_tax, name="staff_tax"),
    path("staff/newsletter/", staff_newsletter, name="staff_newsletter"),
    path("newsletter/subscribe/", subscribe, name="newsletter_subscribe"),
    path("newsletter/unsubscribe/<uuid:token>/", unsubscribe, name="newsletter_unsubscribe"),
    path("account/login/", AccountLoginView.as_view(), name="login"),
    path("account/logout/", AccountLogoutView.as_view(), name="logout"),
    path("account/signup/", signup, name="signup"),
    path("account/", account_home, name="account_home"),
    path("account/properties/add/", add_property, name="add_property"),
    path("account/quotes/<int:quote_id>/accept/", accept_quote, name="accept_quote"),
    path("<slug:slug>/", service_page, name="service_page"),
]

handler404 = page_not_found
