import logging
from urllib.parse import unquote

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.signing import BadSignature, Signer
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags

from apps.booking.models import Job, QuoteRequest
from apps.booking.payments import StripeNotConfigured, ensure_payment_links
from apps.company.models import get_company
from apps.content.views import _seo

logger = logging.getLogger(__name__)


def quote_signer():
    return Signer(salt="thecleanhandy-quote")


def accept_token(quote):
    return quote_signer().sign(str(quote.pk))


def decline_token(quote):
    return quote_signer().sign(f"decline-{quote.pk}")


def _unsigned(token):
    token = unquote(token)
    if "%" in token:
        token = unquote(token)
    try:
        return quote_signer().unsign(token)
    except BadSignature:
        return None


def accept_quoted_request(quote):
    """Schedule the job from a confirmed quote. Returns accepted, already, or not_ready."""
    if hasattr(quote, "job"):
        return "already"
    if quote.status not in (QuoteRequest.Status.QUOTED, QuoteRequest.Status.DECLINED):
        return "not_ready"
    if not hasattr(quote, "estimate"):
        return "not_ready"
    Job.objects.create(
        quote=quote,
        scheduled_date=quote.preferred_date,
        status=Job.Status.SCHEDULED,
    )
    quote.status = QuoteRequest.Status.SCHEDULED
    quote.save(update_fields=["status"])
    notify_staff(quote, "accepted")
    return "accepted"


def decline_quoted_request(quote):
    """Mark a confirmed quote declined. Returns declined, already, or not_ready."""
    if hasattr(quote, "job"):
        return "already"
    if quote.status == QuoteRequest.Status.DECLINED:
        return "declined"
    if quote.status != QuoteRequest.Status.QUOTED or not hasattr(quote, "estimate"):
        return "not_ready"
    quote.status = QuoteRequest.Status.DECLINED
    quote.save(update_fields=["status"])
    notify_staff(quote, "declined")
    return "declined"


def staff_inbox():
    company = get_company()
    address = (company.public_email or "").strip() or "support@thecleanhandy.com"
    return address


OWNER_QUOTE_EMAIL = "matyass91@gmail.com"


def incoming_quote_recipients():
    recipients = []
    for address in (staff_inbox(), OWNER_QUOTE_EMAIL):
        cleaned = (address or "").strip()
        if cleaned and cleaned.lower() not in {item.lower() for item in recipients}:
            recipients.append(cleaned)
    return recipients


def notify_incoming_quote(quote, request):
    try:
        context = {
            "quote": quote,
            "pickup_lines": _address_lines(quote.property),
            "dropoff_lines": _address_lines(quote.destination) if quote.destination_id else [],
            "staff_url": request.build_absolute_uri(reverse("staff_quote_detail", args=[quote.pk])),
        }
        html_content = render_to_string("emails/quote_received.html", context)
        message = EmailMultiAlternatives(
            subject=f"New quote #{quote.pk}: {quote.service.name}",
            body=strip_tags(html_content),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=incoming_quote_recipients(),
        )
        message.attach_alternative(html_content, "text/html")
        message.send(fail_silently=False)
    except Exception:
        logger.exception("Could not notify staff about incoming quote %s", quote.pk)


def _address_lines(place):
    street = place.street
    if place.unit:
        street = f"{street}, {place.unit}"
    return [
        f"{place.get_kind_display()}, {place.get_borough_display()}",
        street,
        place.get_sqft_band_display(),
    ]


def quote_context(quote, request):
    company = get_company()
    accept_url = request.build_absolute_uri(reverse("quote_email_accept", args=[quote.pk, accept_token(quote)]))
    decline_url = request.build_absolute_uri(reverse("quote_email_decline", args=[quote.pk, decline_token(quote)]))
    return {
        "quote": quote,
        "lines": list(quote.line_items.all()),
        "company": company,
        "pickup_lines": _address_lines(quote.property),
        "dropoff_lines": _address_lines(quote.destination) if quote.destination_id else [],
        "accept_url": accept_url,
        "decline_url": decline_url,
        "deposit_payment": quote.payments.filter(kind="deposit").first(),
        "full_payment": quote.payments.filter(kind="full").first(),
        "phone": company.phone or "(347) 652-6165",
        "support_email": staff_inbox(),
    }


def send_quote_email(quote, request, note):
    quote.email_note = note
    quote.save(update_fields=["email_note"])
    warning = ""
    try:
        ensure_payment_links(quote, request)
    except StripeNotConfigured:
        warning = "Stripe is not configured, so the email has no payment link."
    except Exception:
        logger.exception("Could not create Stripe payment links for quote %s", quote.pk)
        warning = "The payment link could not be created. The quote email was still sent."
    context = quote_context(quote, request)
    html_content = render_to_string("emails/quote_email.html", context)
    text_content = render_to_string("emails/quote_email.txt", context)
    message = EmailMultiAlternatives(
        subject=f"Your {quote.service.name} quote #{quote.pk}",
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[quote.contact_email],
        bcc=[staff_inbox()],
    )
    message.attach_alternative(html_content, "text/html")
    message.send(fail_silently=False)
    quote.quote_email_sent_at = timezone.now()
    quote.save(update_fields=["quote_email_sent_at"])
    return warning


def notify_staff(quote, action):
    try:
        context = {"quote": quote, "action": action, "customer_name": quote.contact_name}
        html_content = render_to_string("emails/quote_status.html", context)
        message = EmailMultiAlternatives(
            subject=f"Quote #{quote.pk} {action} by {quote.contact_name}",
            body=strip_tags(html_content),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[staff_inbox()],
        )
        message.attach_alternative(html_content, "text/html")
        message.send(fail_silently=False)
    except Exception:
        logger.exception("Could not notify staff about quote %s", quote.pk)


def _response(request, quote, action, message, status=200):
    company = get_company()
    return render(
        request,
        "booking/quote_email_response.html",
        {
            "quote": quote,
            "action": action,
            "message": message,
            **_seo(
                request,
                company,
                title="Your quote | TheCleanHandy",
                description="Response to your TheCleanHandy quote.",
                path=request.path,
                noindex=True,
            ),
        },
        status=status,
    )


def quote_email_accept(request, quote_id, token):
    quote = get_object_or_404(QuoteRequest.objects.select_related("service", "estimate"), pk=quote_id)
    if _unsigned(token) != str(quote.pk):
        return HttpResponseForbidden("This link is not valid.")
    result = accept_quoted_request(quote)
    if result == "accepted":
        return _response(
            request,
            quote,
            "accepted",
            "Thank you. Your quote is accepted. TheCleanHandy will confirm the schedule.",
        )
    if result == "already":
        return _response(request, quote, "accepted", "This quote is already accepted.")
    return _response(request, quote, "not_ready", "This quote is not ready to accept yet.", status=403)


def quote_email_decline(request, quote_id, token):
    quote = get_object_or_404(QuoteRequest.objects.select_related("service", "estimate"), pk=quote_id)
    if _unsigned(token) != f"decline-{quote.pk}":
        return HttpResponseForbidden("This link is not valid.")
    result = decline_quoted_request(quote)
    if result == "declined":
        return _response(
            request,
            quote,
            "declined",
            "This quote is declined. Contact TheCleanHandy if you would like a new one.",
        )
    if result == "already":
        return _response(request, quote, "accepted", "This quote was already accepted, so it cannot be declined.")
    return _response(request, quote, "not_ready", "This quote is not ready to decline yet.", status=403)
