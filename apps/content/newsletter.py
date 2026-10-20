import logging
from urllib.parse import urlparse

from django import forms
from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from django.views.decorators.http import require_http_methods, require_POST

from apps.booking.staff_views import staff_required
from apps.company.models import get_company
from apps.content.models import NewsletterSubscriber
from apps.content.views import _seo

logger = logging.getLogger(__name__)


class SubscribeForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"placeholder": "Email address", "autocomplete": "email"}),
    )

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()


class NewsletterSendForm(forms.Form):
    subject = forms.CharField(max_length=140, widget=forms.TextInput(attrs={"placeholder": "Subject"}))
    body = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 8, "placeholder": "Write the note. Each paragraph is a new line."}),
    )


def safe_next(value):
    if not value or not value.startswith("/") or value.startswith("//"):
        return "/"
    parsed = urlparse(value)
    if parsed.scheme or parsed.netloc:
        return "/"
    return value


def _send(subscriber, subject, template, context):
    company = context["company"]
    html_content = render_to_string(template, context)
    message = EmailMultiAlternatives(
        subject=subject,
        body=strip_tags(html_content),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[subscriber.email],
    )
    message.attach_alternative(html_content, "text/html")
    message.send(fail_silently=False)
    return company


def send_welcome(subscriber, request):
    company = get_company()
    try:
        _send(
            subscriber,
            f"You're on the {company.legal_name} list",
            "emails/newsletter_welcome.html",
            {
                "company": company,
                "subscriber": subscriber,
                "unsubscribe_url": request.build_absolute_uri(
                    reverse("newsletter_unsubscribe", args=[subscriber.token])
                ),
            },
        )
    except Exception:
        logger.exception("Could not send newsletter welcome to %s", subscriber.email)


def send_issue(subject, body, request):
    company = get_company()
    paragraphs = [line.strip() for line in body.splitlines() if line.strip()]
    sent = 0
    failed = 0
    for subscriber in NewsletterSubscriber.objects.filter(is_active=True):
        try:
            _send(
                subscriber,
                subject,
                "emails/newsletter_issue.html",
                {
                    "company": company,
                    "paragraphs": paragraphs,
                    "unsubscribe_url": request.build_absolute_uri(
                        reverse("newsletter_unsubscribe", args=[subscriber.token])
                    ),
                },
            )
            sent += 1
        except Exception:
            logger.exception("Could not send newsletter to %s", subscriber.email)
            failed += 1
    return sent, failed


@require_POST
def subscribe(request):
    form = SubscribeForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Enter a valid email address.")
        return HttpResponseRedirect(safe_next(request.POST.get("next")))
    email = form.cleaned_data["email"]
    subscriber, created = NewsletterSubscriber.objects.get_or_create(email=email)
    if created or not subscriber.is_active:
        subscriber.is_active = True
        subscriber.unsubscribed_at = None
        subscriber.save(update_fields=["is_active", "unsubscribed_at"])
        send_welcome(subscriber, request)
        messages.success(request, "You're subscribed. We'll send occasional notes about moving and cleaning.")
    else:
        messages.info(request, "That email is already on the list.")
    return HttpResponseRedirect(safe_next(request.POST.get("next")))


@require_http_methods(["GET", "POST"])
def unsubscribe(request, token):
    subscriber = get_object_or_404(NewsletterSubscriber, token=token)
    company = get_company()
    if request.method == "POST" and subscriber.is_active:
        subscriber.is_active = False
        subscriber.unsubscribed_at = timezone.now()
        subscriber.save(update_fields=["is_active", "unsubscribed_at"])
    return render(
        request,
        "content/newsletter_unsubscribe.html",
        {
            "subscriber": subscriber,
            **_seo(
                request,
                company,
                title="Unsubscribe | TheCleanHandy",
                description="Stop newsletter email from TheCleanHandy.",
                path=request.path,
                noindex=True,
            ),
        },
    )


@staff_required
@require_http_methods(["GET", "POST"])
def staff_newsletter(request):
    form = NewsletterSendForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        active = NewsletterSubscriber.objects.filter(is_active=True).count()
        if active == 0:
            messages.error(request, "There are no active subscribers to write to.")
        else:
            sent, failed = send_issue(form.cleaned_data["subject"], form.cleaned_data["body"], request)
            if sent:
                messages.success(request, f"Sent to {sent} subscriber{'s' if sent != 1 else ''}.")
            if failed:
                messages.error(request, f"{failed} message{'s' if failed != 1 else ''} could not be delivered.")
            if sent:
                return redirect("staff_newsletter")
    company = get_company()
    subscribers = NewsletterSubscriber.objects.all()
    return render(
        request,
        "staff/newsletter.html",
        {
            "form": form,
            "subscribers": subscribers,
            "active_count": subscribers.filter(is_active=True).count(),
            **_seo(
                request,
                company,
                title="Newsletter | TheCleanHandy",
                description="Newsletter subscribers.",
                path="/staff/newsletter/",
                noindex=True,
            ),
        },
    )
