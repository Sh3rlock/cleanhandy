"""Stripe payment links for a 50% deposit or the full quote, matching CleanHandy."""

import logging
from decimal import Decimal, ROUND_DOWN

import stripe
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.booking.models import QuotePayment, QuoteRequest
from apps.company.models import get_company
from apps.content.views import _seo

logger = logging.getLogger(__name__)


class StripeNotConfigured(Exception):
    pass


def split_amounts(total):
    total = Decimal(total).quantize(Decimal("0.01"))
    deposit = (total / 2).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    balance = (total - deposit).quantize(Decimal("0.01"))
    return deposit, balance


def _cents(amount):
    return int((Decimal(amount) * 100).to_integral_value())


def ensure_payment_links(quote, request):
    """Create or reuse Stripe payment links for the deposit and the full total."""
    if not settings.STRIPE_SECRET_KEY:
        raise StripeNotConfigured("Stripe secret key is not configured")
    if quote.total <= 0:
        return
    if quote.payments.filter(status=QuotePayment.Status.PAID).exists():
        return

    stripe.api_key = settings.STRIPE_SECRET_KEY
    deposit_amount, _balance = split_amounts(quote.total)
    redirect_url = request.build_absolute_uri(reverse("quote_payment_received", args=[quote.pk]))
    for kind, amount, description in (
        (QuotePayment.Kind.DEPOSIT, deposit_amount, f"50% deposit for {quote.service.name} quote #{quote.pk}"),
        (QuotePayment.Kind.FULL, quote.total, f"Full payment for {quote.service.name} quote #{quote.pk}"),
    ):
        existing = quote.payments.filter(kind=kind).first()
        if (
            existing
            and existing.status == QuotePayment.Status.PENDING
            and existing.amount == amount
            and existing.stripe_payment_link_url
        ):
            continue
        if existing and existing.stripe_payment_link_id:
            _deactivate(existing.stripe_payment_link_id)
        link = stripe.PaymentLink.create(
            line_items=[
                {
                    "price_data": {
                        "currency": settings.STRIPE_CURRENCY,
                        "product_data": {
                            "name": description,
                            "description": description,
                        },
                        "unit_amount": _cents(amount),
                    },
                    "quantity": 1,
                }
            ],
            metadata={
                "quote_id": str(quote.pk),
                "payment_type": kind,
                "customer_name": quote.contact_name or "Customer",
                "customer_email": quote.contact_email or "",
            },
            after_completion={"type": "redirect", "redirect": {"url": redirect_url}},
            allow_promotion_codes=True,
            billing_address_collection="required",
            phone_number_collection={"enabled": True},
        )
        QuotePayment.objects.update_or_create(
            quote=quote,
            kind=kind,
            defaults={
                "amount": amount,
                "stripe_payment_link_id": link.id,
                "stripe_payment_link_url": link.url,
                "status": QuotePayment.Status.PENDING,
                "paid_at": None,
            },
        )


def _deactivate(payment_link_id):
    try:
        stripe.PaymentLink.modify(payment_link_id, active=False)
    except stripe.error.StripeError:
        logger.exception("Could not deactivate payment link %s", payment_link_id)


def record_checkout_session(session):
    """Mark the matching quote payment paid after Stripe checkout completes."""
    metadata = session.get("metadata") or {}
    quote_id = metadata.get("quote_id")
    payment_type = metadata.get("payment_type")
    payment_link_id = session.get("payment_link") or ""
    payment = None
    if payment_link_id:
        payment = QuotePayment.objects.filter(stripe_payment_link_id=payment_link_id).select_related("quote").first()
    if payment is None and quote_id and payment_type:
        payment = (
            QuotePayment.objects.filter(quote_id=quote_id, kind=payment_type)
            .select_related("quote")
            .first()
        )
    if payment is None or payment.status == QuotePayment.Status.PAID:
        return payment
    payment.status = QuotePayment.Status.PAID
    payment.paid_at = timezone.now()
    payment.save(update_fields=["status", "paid_at"])
    if settings.STRIPE_SECRET_KEY:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        for other in payment.quote.payments.exclude(pk=payment.pk):
            if other.stripe_payment_link_id and other.status != QuotePayment.Status.PAID:
                _deactivate(other.stripe_payment_link_id)
    _notify_payment(payment)
    return payment


def _notify_payment(payment):
    try:
        company = get_company()
        inbox = (company.public_email or "").strip() or "support@thecleanhandy.com"
        quote = payment.quote
        html_content = render_to_string(
            "emails/quote_payment.html",
            {"quote": quote, "payment": payment},
        )
        message = EmailMultiAlternatives(
            subject=f"Quote #{quote.pk} payment received ({payment.get_kind_display()})",
            body=strip_tags(html_content),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[inbox],
        )
        message.attach_alternative(html_content, "text/html")
        message.send(fail_silently=False)
    except Exception:
        logger.exception("Could not notify staff about payment on quote %s", payment.quote_id)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    signature = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    if not settings.STRIPE_WEBHOOK_SECRET:
        return HttpResponse("Webhook secret is not configured", status=400)
    try:
        event = stripe.Webhook.construct_event(payload, signature, settings.STRIPE_WEBHOOK_SECRET)
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)
    if event["type"] == "checkout.session.completed":
        record_checkout_session(event["data"]["object"])
    return HttpResponse(status=200)


def quote_payment_received(request, quote_id):
    quote = get_object_or_404(QuoteRequest.objects.select_related("service"), pk=quote_id)
    company = get_company()
    return render(
        request,
        "booking/quote_payment_received.html",
        {
            "quote": quote,
            **_seo(
                request,
                company,
                title="Payment received | TheCleanHandy",
                description="TheCleanHandy received your quote payment.",
                path=request.path,
                noindex=True,
            ),
        },
    )
