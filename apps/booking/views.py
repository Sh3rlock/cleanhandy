from datetime import date

from django.contrib.auth import login
from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from apps.accounts.models import User
from apps.booking.forms import QuoteContactForm, QuotePropertyForm, QuoteServiceForm
from apps.booking.models import ConversionEvent, Property, QuoteRequest
from apps.booking.pricing import normalize_selection, selection_is_complete, service_needs_destination, store_calculated_quote
from apps.booking.quote_actions import notify_incoming_quote
from apps.company.models import get_company
from apps.content.models import ServicePage
from apps.content.views import _seo


DRAFT_KEY = "quote_draft"


def _noindex(request, title):
    company = get_company()
    return {
        "company": company,
        **_seo(
            request,
            company,
            title=title,
            description="Request a quote from TheCleanHandy.",
            path=request.path,
            noindex=True,
        ),
    }


def _draft(request):
    return request.session.get(DRAFT_KEY) or {}


@require_http_methods(["GET", "POST"])
def quote_service(request):
    initial = {}
    service_slug = request.GET.get("service") or _draft(request).get("service_slug")
    if service_slug:
        service = ServicePage.objects.filter(slug=service_slug, is_active=True, is_bookable=True).first()
        if service:
            initial["service"] = service.pk
    if request.method == "POST":
        form = QuoteServiceForm(request.POST)
        if form.is_valid():
            service = form.cleaned_data["service"]
            request.session[DRAFT_KEY] = {"service_id": service.pk, "service_slug": service.slug}
            request.session.modified = True
            return redirect("quote_property")
    else:
        form = QuoteServiceForm(initial=initial)
    return render(request, "booking/quote_service.html", {"form": form, "step": 1, **_noindex(request, "Get a Quote | TheCleanHandy")})


@require_http_methods(["GET", "POST"])
def quote_property(request):
    draft = _draft(request)
    if "service_id" not in draft:
        return redirect("quote_start")
    service = get_object_or_404(ServicePage, pk=draft["service_id"], is_active=True, is_bookable=True)
    if request.method == "POST":
        form = QuotePropertyForm(request.POST, user=request.user, service=service)
        if form.is_valid():
            saved = form.cleaned_data.get("saved_property")
            if saved is not None:
                draft["property_id"] = saved.pk
                draft.pop("property", None)
            else:
                draft.pop("property_id", None)
                draft["property"] = form.origin_data()
            if form.needs_destination:
                draft["destination"] = form.destination_data()
            else:
                draft.pop("destination", None)
            draft["option_ids"] = form.selected_option_ids()
            draft["parking_notes"] = form.cleaned_data.get("parking_notes", "")
            preferred = form.cleaned_data.get("preferred_date")
            draft["preferred_date"] = preferred.isoformat() if preferred else ""
            request.session[DRAFT_KEY] = draft
            request.session.modified = True
            return redirect("quote_contact")
    else:
        initial = dict(draft.get("property") or {})
        if draft.get("property_id"):
            initial["saved_property"] = draft["property_id"]
        destination = draft.get("destination") or {}
        for key, value in destination.items():
            initial[f"dest_{key}"] = value
        if draft.get("parking_notes"):
            initial["parking_notes"] = draft["parking_notes"]
        if draft.get("preferred_date"):
            initial["preferred_date"] = draft["preferred_date"]
        form = QuotePropertyForm(
            user=request.user,
            service=service,
            option_ids=draft.get("option_ids"),
            initial=initial,
        )
    return render(
        request,
        "booking/quote_property.html",
        {
            "form": form,
            "service": service,
            "needs_destination": form.needs_destination,
            "step": 2,
            **_noindex(request, "Job details | TheCleanHandy"),
        },
    )


@require_http_methods(["GET", "POST"])
def quote_contact(request):
    draft = _draft(request)
    if "service_id" not in draft or ("property" not in draft and "property_id" not in draft):
        return redirect("quote_start")
    service = get_object_or_404(ServicePage, pk=draft["service_id"], is_active=True, is_bookable=True)
    if service_needs_destination(service) and "destination" not in draft:
        return redirect("quote_property")
    initial = {}
    if request.user.is_authenticated:
        initial = {
            "contact_name": request.user.get_full_name(),
            "contact_email": request.user.email,
            "contact_phone": request.user.phone,
        }
    if request.method == "POST":
        form = QuoteContactForm(request.POST, initial=initial)
        if request.user.is_authenticated:
            form.fields.pop("create_account")
            form.fields.pop("password")
        if form.is_valid():
            variables = normalize_selection(service, draft.get("option_ids"))
            if not selection_is_complete(service, variables):
                messages.error(request, "Choose the options for this service.")
                return redirect("quote_property")
            quote = _create_quote(request, draft, form.cleaned_data, service, variables)
            request.session.pop(DRAFT_KEY, None)
            request.session["last_quote_id"] = quote.pk
            return redirect("quote_done")
    else:
        form = QuoteContactForm(initial=initial)
        if request.user.is_authenticated:
            form.fields.pop("create_account")
            form.fields.pop("password")
    return render(
        request,
        "booking/quote_contact.html",
        {"form": form, "service": service, "step": 3, **_noindex(request, "Contact details | TheCleanHandy")},
    )


def _preferred_day(raw):
    if not raw:
        return None
    return date.fromisoformat(raw)


def _create_quote(request, draft, cleaned, service, variables):
    user = request.user if request.user.is_authenticated else None
    with transaction.atomic():
        if user is None and cleaned.get("create_account"):
            user = User.objects.create_user(
                email=cleaned["contact_email"],
                password=cleaned["password"],
                phone=cleaned["contact_phone"],
            )
            user.first_name = cleaned["contact_name"]
            user.save(update_fields=["first_name", "phone"])
            login(request, user)
        if draft.get("property_id"):
            property_obj = get_object_or_404(Property, pk=draft["property_id"])
        else:
            property_obj = Property.objects.create(owner=user, **draft["property"])
        destination = None
        if service_needs_destination(service):
            destination = Property.objects.create(owner=user, **draft["destination"])
        quote = QuoteRequest.objects.create(
            user=user,
            service=service,
            property=property_obj,
            destination=destination,
            preferred_date=_preferred_day(draft.get("preferred_date")),
            parking_notes=draft.get("parking_notes", ""),
            notes=cleaned.get("notes", ""),
            contact_name=cleaned["contact_name"],
            contact_email=cleaned["contact_email"],
            contact_phone=cleaned["contact_phone"],
        )
        store_calculated_quote(quote, variables)
        ConversionEvent.objects.create(
            kind=ConversionEvent.Kind.QUOTE,
            path=service.get_absolute_url(),
            user=user,
            quote=quote,
        )
    notify_incoming_quote(quote, request)
    return quote


def quote_done(request):
    quote_id = request.session.get("last_quote_id")
    quote = QuoteRequest.objects.filter(pk=quote_id).select_related("service").first() if quote_id else None
    return render(request, "booking/quote_done.html", {"quote": quote, **_noindex(request, "Quote received | TheCleanHandy")})


@require_POST
def track_event(request):
    kind = request.POST.get("kind", "")
    allowed = {ConversionEvent.Kind.PHONE, ConversionEvent.Kind.EMAIL}
    if kind not in allowed:
        return redirect(request.META.get("HTTP_REFERER") or "/")
    ConversionEvent.objects.create(
        kind=kind,
        path=(request.POST.get("path") or "")[:300],
        user=request.user if request.user.is_authenticated else None,
    )
    from django.http import HttpResponse

    return HttpResponse(status=204)
