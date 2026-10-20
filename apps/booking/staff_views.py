import logging
from calendar import Calendar, month_name
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from functools import wraps

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.db.models import Count, Max, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_http_methods

from apps.booking.forms import QuoteAdjustForm, TaxSettingsForm
from apps.booking.models import Job, PriceVariable, PriceVariableCategory, QuoteLineItem, QuotePayment, QuoteRequest, TaxSettings
from apps.booking.pricing import confirm_quote, money, recalculate_stored_quote
from apps.booking.quote_actions import send_quote_email
from apps.booking.quote_pdf import build_quote_pdf
from apps.company.forms import SocialLinksForm
from apps.company.models import get_company
from apps.content.models import NewsletterSubscriber, ServicePage
from apps.content.views import _seo


logger = logging.getLogger(__name__)


def staff_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), login_url=reverse("login"))
        if not request.user.is_staff:
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return wrapped


def _staff_page(request, title):
    company = get_company()
    return _seo(
        request,
        company,
        title=title,
        description="Staff quote desk for TheCleanHandy.",
        path=request.path,
        noindex=True,
    )


def _parse_decimal(raw):
    try:
        return Decimal(str(raw).strip())
    except (InvalidOperation, AttributeError):
        return None


@staff_required
@require_http_methods(["GET"])
def staff_quote_list(request):
    quotes = QuoteRequest.objects.select_related("service", "property", "destination")
    status = request.GET.get("status", "")
    service_id = request.GET.get("service", "")
    if status in QuoteRequest.Status.values:
        quotes = quotes.filter(status=status)
    if service_id.isdigit():
        quotes = quotes.filter(service_id=int(service_id))
    return render(
        request,
        "staff/quote_list.html",
        {
            "quotes": quotes,
            "statuses": QuoteRequest.Status.choices,
            "services": ServicePage.objects.filter(is_bookable=True).order_by("name"),
            "selected_status": status,
            "selected_service": service_id,
            **_staff_page(request, "Quote requests | TheCleanHandy"),
        },
    )


@staff_required
@require_http_methods(["GET", "POST"])
def staff_quote_detail(request, quote_id):
    quote = get_object_or_404(
        QuoteRequest.objects.select_related("service", "property", "destination", "estimate"),
        pk=quote_id,
    )
    locked = hasattr(quote, "job")
    if request.method == "POST" and not locked:
        form = QuoteAdjustForm(request.POST)
        amounts, error = _posted_amounts(quote, request.POST)
        if error:
            messages.error(request, error)
        elif form.is_valid():
            for line in quote.line_items.all():
                line.amount = amounts[line.pk]
                line.save(update_fields=["amount"])
            extra_label = form.cleaned_data["extra_label"].strip()
            extra_amount = form.cleaned_data["extra_amount"]
            if extra_amount is not None and not extra_label:
                extra_label = "Additional charge"
            if extra_label and extra_amount is not None:
                next_sort = (quote.line_items.aggregate(Max("sort_order"))["sort_order__max"] or 0) + 1
                QuoteLineItem.objects.create(
                    quote=quote,
                    label=extra_label,
                    amount=money(extra_amount),
                    sort_order=next_sort,
                )
            elif extra_label and extra_amount is None:
                messages.error(request, "Enter an amount for the extra charge.")
                return redirect("staff_quote_detail", quote_id=quote.pk)
            recalculate_stored_quote(
                quote,
                form.cleaned_data["discount_kind"],
                form.cleaned_data["discount_value"],
            )
            if request.POST.get("action") == "confirm":
                confirm_quote(quote, request.user)
                messages.success(request, "Quote confirmed. Send it by email so the customer can accept it.")
            else:
                messages.success(request, "Price updated. Confirm it when the customer should see this total.")
            return redirect("staff_quote_detail", quote_id=quote.pk)
    else:
        if quote.discount_kind == "percent":
            discount_value = quote.discount_rate
        else:
            discount_value = quote.discount_amount
        form = QuoteAdjustForm(initial={"discount_kind": quote.discount_kind, "discount_value": discount_value})
    quote.refresh_from_db()
    estimate = getattr(quote, "estimate", None)
    return render(
        request,
        "staff/quote_detail.html",
        {
            "quote": quote,
            "lines": quote.line_items.all(),
            "form": form,
            "locked": locked,
            "estimate": estimate,
            "price_differs": bool(estimate and estimate.price != quote.total),
            **_staff_page(request, f"Quote {quote.pk} | TheCleanHandy"),
        },
    )


@staff_required
@require_http_methods(["POST"])
def staff_send_quote_email(request, quote_id):
    quote = get_object_or_404(
        QuoteRequest.objects.select_related("service", "property", "destination", "estimate"),
        pk=quote_id,
    )
    estimate = getattr(quote, "estimate", None)
    if estimate is None:
        messages.error(request, "Confirm the quote before sending it.")
        return redirect("staff_quote_detail", quote_id=quote.pk)
    if estimate.price != quote.total:
        messages.error(request, "Confirm the updated total before sending the email.")
        return redirect("staff_quote_detail", quote_id=quote.pk)
    try:
        warning = send_quote_email(quote, request, request.POST.get("email_note", "").strip())
    except Exception:
        logger.exception("Could not email quote %s", quote.pk)
        messages.error(request, "The email could not be sent. Check the mail settings and try again.")
        return redirect("staff_quote_detail", quote_id=quote.pk)
    if warning:
        messages.warning(request, f"Quote emailed to {quote.contact_email}. {warning}")
    else:
        messages.success(request, f"Quote emailed to {quote.contact_email}.")
    return redirect("staff_quote_detail", quote_id=quote.pk)


@staff_required
@require_http_methods(["GET"])
def staff_quote_pdf(request, quote_id):
    quote = get_object_or_404(
        QuoteRequest.objects.select_related("service", "property", "destination", "estimate"),
        pk=quote_id,
    )
    response = HttpResponse(build_quote_pdf(quote), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="quote-{quote.pk}.pdf"'
    return response


def _posted_amounts(quote, post):
    amounts = {}
    for line in quote.line_items.all():
        parsed = _parse_decimal(post.get(f"amount_{line.pk}", ""))
        if parsed is None or parsed < 0:
            return None, f"Enter a valid amount for {line.label}."
        amounts[line.pk] = money(parsed)
    return amounts, ""


@staff_required
@require_http_methods(["GET", "POST"])
def staff_prices(request):
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "save-category":
            _save_category(request)
        elif action == "add-variable":
            _add_variable(request)
        elif action == "add-category":
            _add_category(request)
        return redirect("staff_prices")
    categories = (
        PriceVariableCategory.objects.exclude(slug="painting-size")
        .prefetch_related("variables", "services")
        .order_by("sort_order", "name")
    )
    services = ServicePage.objects.filter(is_active=True, is_bookable=True).order_by("name")
    return render(
        request,
        "staff/prices.html",
        {
            "groups": _price_groups(categories),
            "services": services,
            "input_types": (
                (PriceVariableCategory.InputType.SINGLE, "Customer must choose one"),
                (PriceVariableCategory.InputType.ADDON, "Optional add-on"),
            ),
            **_staff_page(request, "Price options | TheCleanHandy"),
        },
    )


def _price_groups(categories):
    families = (
        (ServicePage.Category.MOVING, "Moving"),
        (ServicePage.Category.MOVE_CLEANING, "Move-in and move-out cleaning"),
        (ServicePage.Category.COMMERCIAL, "Commercial cleaning"),
        (ServicePage.Category.ADDITIONAL, "Additional services"),
    )
    buckets = {key: [] for key, _label in families}
    shared = []
    unused = []
    for category in categories:
        linked = {service.category for service in category.services.all()}
        if not linked:
            unused.append(category)
        elif len(linked) == 1:
            buckets[linked.pop()].append(category)
        else:
            shared.append(category)
    groups = [{"label": label, "categories": buckets[key]} for key, label in families if buckets[key]]
    if shared:
        groups.append({"label": "Used by more than one kind of service", "categories": shared})
    if unused:
        groups.append({"label": "Not shown on a quote yet", "categories": unused})
    return groups


def _discount_is_valid(kind, price, discount):
    if kind not in ("amount", "percent"):
        return False
    if price is None or discount is None or price < 0 or discount < 0:
        return False
    return not (kind == "percent" and discount > 100)


def _apply_option_discount(variable, kind, discount):
    if kind == "amount":
        variable.discount_kind = "amount"
        variable.discount_amount = money(discount)
        variable.discount_percent = Decimal("0.00")
    else:
        variable.discount_kind = "percent"
        variable.discount_percent = money(discount)
        variable.discount_amount = Decimal("0.00")


def _save_category(request):
    category = get_object_or_404(PriceVariableCategory, pk=request.POST.get("category_id"))
    name = (request.POST.get("name") or "").strip()
    if name:
        category.name = name
    category.is_active = request.POST.get("is_active") == "on"
    category.save(update_fields=["name", "is_active"])
    posted_ids = request.POST.getlist("services")
    category.services.set(
        ServicePage.objects.filter(pk__in=posted_ids).filter(
            Q(is_bookable=True) | Q(pk__in=category.services.values("pk"))
        )
    )
    for variable in category.variables.all():
        prefix = f"var_{variable.pk}_"
        variable_name = (request.POST.get(prefix + "name") or "").strip()
        price = _parse_decimal(request.POST.get(prefix + "price"))
        discount = _parse_decimal(request.POST.get(prefix + "discount"))
        kind = request.POST.get(prefix + "discount_kind")
        if not variable_name or not _discount_is_valid(kind, price, discount):
            messages.error(request, f"Check the price and discount for {variable.name}.")
            continue
        _apply_option_discount(variable, kind, discount)
        variable.name = variable_name
        variable.price = money(price)
        variable.is_active = request.POST.get(prefix + "active") == "on"
        try:
            variable.save()
        except IntegrityError:
            messages.error(request, f"{variable_name} is already in {category.name}.")
    messages.success(request, f"Saved {category.name}.")


def _add_variable(request):
    category = get_object_or_404(PriceVariableCategory, pk=request.POST.get("category_id"))
    name = (request.POST.get("name") or "").strip()
    price = _parse_decimal(request.POST.get("price") or "0")
    discount = _parse_decimal(request.POST.get("discount") or "0")
    kind = request.POST.get("discount_kind")
    if not name or not _discount_is_valid(kind, price, discount):
        messages.error(request, "Enter a name, a price of 0 or more, and a discount. Percent discounts cannot be more than 100.")
        return
    if category.variables.filter(name=name).exists():
        messages.error(request, "That option already exists in this category.")
        return
    next_sort = (category.variables.aggregate(Max("sort_order"))["sort_order__max"] or 0) + 1
    variable = PriceVariable(category=category, name=name, price=money(price), sort_order=next_sort)
    _apply_option_discount(variable, kind, discount)
    variable.save()
    messages.success(request, f"Added {name}.")


def _add_category(request):
    name = (request.POST.get("name") or "").strip()
    input_type = request.POST.get("input_type")
    if not name or input_type not in PriceVariableCategory.InputType.values:
        messages.error(request, "Enter a category name and choose how the customer picks it.")
        return
    base = slugify(name)[:120] or "options"
    slug = base
    suffix = 2
    while PriceVariableCategory.objects.filter(slug=slug).exists():
        slug = f"{base}-{suffix}"
        suffix += 1
    next_sort = (PriceVariableCategory.objects.aggregate(Max("sort_order"))["sort_order__max"] or 0) + 10
    category = PriceVariableCategory.objects.create(name=name, slug=slug, input_type=input_type, sort_order=next_sort)
    category.services.set(ServicePage.objects.filter(pk__in=request.POST.getlist("services"), is_bookable=True))
    messages.success(request, f"Added {category.name}. Add priced options under it.")


@staff_required
@require_http_methods(["GET", "POST"])
def staff_social(request):
    company = get_company()
    if request.method == "POST":
        form = SocialLinksForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, "Social links saved. Blank fields stay off the site.")
            return redirect("staff_social")
    else:
        form = SocialLinksForm(instance=company)
    return render(
        request,
        "staff/social.html",
        {"form": form, **_staff_page(request, "Social links | TheCleanHandy")},
    )


@staff_required
@require_http_methods(["GET", "POST"])
def staff_tax(request):
    settings_obj = TaxSettings.load()
    if request.method == "POST":
        form = TaxSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Tax rate saved. New calculations use this rate.")
            return redirect("staff_tax")
    else:
        form = TaxSettingsForm(instance=settings_obj)
    return render(
        request,
        "staff/tax.html",
        {"form": form, **_staff_page(request, "Tax settings | TheCleanHandy")},
    )


def _month_start(raw, today):
    if raw and len(raw) == 7 and raw[4] == "-":
        year_text, month_text = raw.split("-")
        if year_text.isdigit() and month_text.isdigit():
            year, month = int(year_text), int(month_text)
            if 1 <= month <= 12 and 2000 <= year <= 2100:
                return date(year, month, 1)
    return today.replace(day=1)


def _shift_month(current, delta):
    index = current.month - 1 + delta
    return date(current.year + index // 12, index % 12 + 1, 1)


def _calendar_event(quote, when, kind):
    status = quote.job.status if kind == "job" else quote.status
    status_label = quote.job.get_status_display() if kind == "job" else quote.get_status_display()
    return {
        "when": when,
        "kind": kind,
        "status_key": status,
        "status": status_label,
        "title": quote.contact_name,
        "service": quote.service.name,
        "area": quote.property.get_borough_display(),
        "url": reverse("staff_quote_detail", args=[quote.pk]),
    }


@staff_required
@require_http_methods(["GET"])
def staff_calendar(request):
    today = timezone.localdate()
    current = _month_start(request.GET.get("month", ""), today)
    weeks = Calendar(firstweekday=6).monthdatescalendar(current.year, current.month)
    start, end = weeks[0][0], weeks[-1][-1]
    hidden_quotes = [QuoteRequest.Status.DECLINED, QuoteRequest.Status.CANCELLED]

    jobs = (
        Job.objects.filter(scheduled_date__range=(start, end))
        .select_related("quote", "quote__service", "quote__property")
        .order_by("scheduled_date", "quote__contact_name")
    )
    open_quotes = (
        QuoteRequest.objects.filter(preferred_date__range=(start, end), job__isnull=True)
        .exclude(status__in=hidden_quotes)
        .select_related("service", "property")
        .order_by("preferred_date", "contact_name")
    )
    by_day = defaultdict(list)
    for job in jobs:
        by_day[job.scheduled_date].append(_calendar_event(job.quote, job.scheduled_date, "job"))
    for quote in open_quotes:
        by_day[quote.preferred_date].append(_calendar_event(quote, quote.preferred_date, "quote"))

    grid = []
    for week in weeks:
        grid.append(
            [
                {
                    "date": day,
                    "in_month": day.month == current.month,
                    "today": day == today,
                    "events": by_day[day],
                }
                for day in week
            ]
        )

    upcoming = []
    future_jobs = (
        Job.objects.filter(scheduled_date__gte=today)
        .exclude(status=Job.Status.CANCELLED)
        .select_related("quote", "quote__service", "quote__property")
        .order_by("scheduled_date", "quote__contact_name")[:12]
    )
    future_quotes = (
        QuoteRequest.objects.filter(preferred_date__gte=today, job__isnull=True)
        .exclude(status__in=hidden_quotes)
        .select_related("service", "property")
        .order_by("preferred_date", "contact_name")[:12]
    )
    for job in future_jobs:
        upcoming.append(_calendar_event(job.quote, job.scheduled_date, "job"))
    for quote in future_quotes:
        upcoming.append(_calendar_event(quote, quote.preferred_date, "quote"))
    upcoming.sort(key=lambda item: (item["when"], item["title"]))

    needs_date = list(
        Job.objects.filter(scheduled_date__isnull=True)
        .exclude(status=Job.Status.CANCELLED)
        .select_related("quote", "quote__service", "quote__property")
        .order_by("quote__contact_name")[:8]
    )
    return render(
        request,
        "staff/calendar.html",
        {
            "grid": grid,
            "weekdays": ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
            "month_label": f"{month_name[current.month]} {current.year}",
            "prev_month": _shift_month(current, -1).strftime("%Y-%m"),
            "next_month": _shift_month(current, 1).strftime("%Y-%m"),
            "upcoming": upcoming[:8],
            "needs_date": needs_date,
            **_staff_page(request, "Calendar | TheCleanHandy"),
        },
    )


@staff_required
@require_http_methods(["GET"])
def staff_dashboard(request):
    today = timezone.localdate()
    week_end = today + timedelta(days=6)
    month_start = today.replace(day=1)
    closed = [QuoteRequest.Status.DECLINED, QuoteRequest.Status.CANCELLED]
    counts = {
        row["status"]: row["total"]
        for row in QuoteRequest.objects.values("status").annotate(total=Count("id"))
    }
    recent = QuoteRequest.objects.select_related("service", "property").order_by("-created_at")[:6]
    week_jobs = (
        Job.objects.filter(scheduled_date__range=(today, week_end))
        .exclude(status=Job.Status.CANCELLED)
        .select_related("quote", "quote__service", "quote__property")
        .order_by("scheduled_date", "quote__contact_name")
    )
    week_quotes = (
        QuoteRequest.objects.filter(preferred_date__range=(today, week_end), job__isnull=True)
        .exclude(status__in=closed)
        .select_related("service", "property")
        .order_by("preferred_date", "contact_name")
    )
    agenda = [_calendar_event(job.quote, job.scheduled_date, "job") for job in week_jobs]
    agenda.extend(_calendar_event(quote, quote.preferred_date, "quote") for quote in week_quotes)
    agenda.sort(key=lambda item: (item["when"], item["title"]))
    collected = (
        QuotePayment.objects.filter(status=QuotePayment.Status.PAID, paid_at__date__gte=month_start).aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0")
    )
    jobs_ahead = Job.objects.filter(status=Job.Status.SCHEDULED).filter(
        Q(scheduled_date__gte=today) | Q(scheduled_date__isnull=True)
    ).count()
    return render(
        request,
        "staff/dashboard.html",
        {
            "today": today,
            "needs_price": counts.get(QuoteRequest.Status.REQUESTED, 0),
            "waiting": counts.get(QuoteRequest.Status.QUOTED, 0),
            "jobs_ahead": jobs_ahead,
            "collected": collected,
            "month_label": month_name[today.month],
            "recent": recent,
            "agenda": agenda,
            "subscribers": NewsletterSubscriber.objects.filter(is_active=True).count(),
            **_staff_page(request, "Dashboard | TheCleanHandy"),
        },
    )
