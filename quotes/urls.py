from django.urls import path
from django.views.generic import TemplateView
from django.http import JsonResponse
from .views import about, contact, blog, blog_detail, quote_submitted, request_cleaning_quote, request_handyman_quote, available_hours_api, quote_submitted_handyman, subscribe_newsletter, request_cleaning_booking, request_handyman_booking, cleaning_booking, handyman_booking, office_cleaning_booking, office_quote_submit, terms, privacy, faq, download_office_cleaning_pdf, office_cleaning_quote_submitted, cleaning_services, commercial_services, handyman_quote_submit, booking_confirmation, request_post_event_cleaning_quote, post_event_cleaning_quote_submit, quote_submitted_post_event_cleaning
from .stripe_views import create_payment_intent, stripe_webhook, webhook_test, manual_webhook_trigger, get_payment_status, create_checkout_session, check_and_fix_payment_status, fix_payment_intent_metadata, test_payment_link_webhook
from .debug_views import debug_booking_calculation

def healthcheck(request):
    """Simple healthcheck endpoint that doesn't require database access"""
    try:
        return JsonResponse({
            "status": "healthy", 
            "message": "CleanHandy API is running",
            "timestamp": "2025-10-24T13:00:00Z"
        })
    except Exception as e:
        return JsonResponse({
            "status": "error", 
            "message": str(e)
        }, status=500)


urlpatterns = [
    path("health/", healthcheck, name="healthcheck"),
    path("about", about, name="about"),
    path("contact", contact, name="contact"),
    path("blog", blog, name="blog"),
    path("blog-detail", blog_detail, name="blog_detail"),
    path("blog-detail-1/", TemplateView.as_view(template_name="blog_detail_1.html"), name="blog_detail_1"),
    path("blog-detail-2/", TemplateView.as_view(template_name="blog_detail_2.html"), name="blog_detail_2"),
    path("blog-detail-3/", TemplateView.as_view(template_name="blog_detail_3.html"), name="blog_detail_3"),

    path("cleaning/booking/", cleaning_booking, name="cleaning_booking"),
    path("handyman/booking/", handyman_booking, name="handyman_booking"),
    path("office/cleaning/booking/", office_cleaning_booking, name="office_cleaning_booking"),
    path("office/quote/submit/", office_quote_submit, name="office_quote_submit"),
    path("handyman/quote/submit/", handyman_quote_submit, name="handyman_quote_submit"),
    path("post-event-cleaning/quote/submit/", post_event_cleaning_quote_submit, name="post_event_cleaning_quote_submit"),
    path("office/cleaning/pdf/<int:booking_id>/", download_office_cleaning_pdf, name="download_office_cleaning_pdf"),
    path("office/cleaning/submitted/<int:booking_id>/", office_cleaning_quote_submitted, name="office_cleaning_quote_submitted"),
    path("booking/confirmation/<int:booking_id>/", booking_confirmation, name="booking_confirmation"),

    path("cleaning/request/<int:service_id>/", request_cleaning_quote, name="request_cleaning_quote"),
    path('handyman/request/<int:service_id>/', request_handyman_quote, name='request_handyman_quote'),
    path('post-event-cleaning/request/<int:service_id>/', request_post_event_cleaning_quote, name='request_post_event_cleaning_quote'),
    path("submitted/<int:quote_id>/", quote_submitted, name="quote_submitted"),
    path("submitted-handyman/<int:quote_id>/", quote_submitted_handyman, name="quote_submitted_handyman"),
    path("submitted-post-event-cleaning/<int:quote_id>/", quote_submitted_post_event_cleaning, name="quote_submitted_post_event_cleaning"),
    path("api/available-hours/", available_hours_api, name="available_hours_api"),

    path('subscribe/', subscribe_newsletter, name='subscribe_newsletter'),

    path("terms", terms, name="terms"),
    path("privacy", privacy, name="privacy"),
    path("faq", faq, name="faq"),
    
    # Stripe payment URLs
    path("api/create-payment-intent/", create_payment_intent, name="create_payment_intent"),
    path("api/create-checkout-session/", create_checkout_session, name="create_checkout_session"),
    path("api/webhook/stripe/", stripe_webhook, name="stripe_webhook"),
    path("api/webhook/test/", webhook_test, name="webhook_test"),
    path("api/webhook/trigger/<int:booking_id>/", manual_webhook_trigger, name="manual_webhook_trigger"),
    path("api/payment-status/<int:booking_id>/", get_payment_status, name="get_payment_status"),
    path("api/check-payment-status/", check_and_fix_payment_status, name="check_payment_status"),
    path("api/fix-payment-intent/", fix_payment_intent_metadata, name="fix_payment_intent"),
    path("api/test-payment-link-webhook/", test_payment_link_webhook, name="test_payment_link_webhook"),
    
    # Debug URLs
    path("debug/booking/<int:booking_id>/", debug_booking_calculation, name="debug_booking_calculation"),
]