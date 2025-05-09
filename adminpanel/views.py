from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from quotes.models import Quote, Service, ServiceCategory, Booking, NewsletterSubscriber
from giftcards.models import GiftCard, DiscountCode
from quotes.forms import CleaningQuoteForm, HandymanQuoteForm
from customers.models import Customer
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from .forms import ServiceForm, ServiceCategoryForm

from django.http import JsonResponse
import json
import pytz
import csv

from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import make_aware
from datetime import datetime, timedelta
from django.utils.timezone import now
from django.utils import timezone

from django.template.loader import render_to_string
from django.http import HttpResponse
from django.urls import reverse

from .forms import AdminQuoteForm
from django.utils.timezone import localtime

from django.core.mail import send_mail
from django.contrib import messages
from django.shortcuts import redirect

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from django.contrib.sites.shortcuts import get_current_site
import secrets
from django.http import HttpResponseForbidden

from .models import BlockedTimeSlot
from django.contrib.auth.models import User

from django.http import JsonResponse, Http404



def admin_check(user):
    return user.is_staff  # Only allow staff users

@login_required
@user_passes_test(admin_check)
# 📌 ADMIN DASHBOARD VIEW
def admin_dashboard(request):
    # Fetch latest 10 records
    latest_quotes = Booking.objects.all().order_by("-created_at")[:10]
    latest_bookings = Booking.objects.all().order_by("-created_at")[:25]
    latest_customers = User.objects.all().order_by("-date_joined")[:10]
    latest_subscribers = NewsletterSubscriber.objects.all().order_by("-subscribed_at")[:10]

    discounts = DiscountCode.objects.all()
    giftcards = GiftCard.objects.all()

    total_quotes = Booking.objects.count()
    total_bookings = Booking.objects.count()
    total_customers = User.objects.count()
    total_subscribers = NewsletterSubscriber.objects.count()

    return render(request, "adminpanel/dashboard.html", {
        "latest_quotes": latest_quotes,
        "latest_bookings": latest_bookings,
        "latest_customers": latest_customers,
        "latest_subscribers": latest_subscribers,
        "discounts": discounts,
        "giftcards": giftcards,
        "total_quotes": total_quotes,
        "total_bookings": total_bookings,
        "total_customers": total_customers,
        "total_subscribers": total_subscribers,
    })


# 📌 QUOTES MANAGEMENT
from django.shortcuts import render
from django.utils import timezone
from quotes.models import Quote, Service

def quote_list(request):
    quotes = Booking.objects.all()

    # Filter: Service
    if service := request.GET.get("service"):
        quotes = quotes.filter(service_id=service)

    # Filter: Status
    if status := request.GET.get("status"):
        quotes = quotes.filter(status=status)

    # Filter: Date range
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")

    if from_date and to_date:
        try:
            from_dt = datetime.strptime(from_date, "%Y-%m-%d").date()
            to_dt = datetime.strptime(to_date, "%Y-%m-%d").date()

            if from_dt > to_dt:
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    return HttpResponse("Invalid date range", status=400)
                messages.warning(request, "From Date cannot be later than To Date.")
            else:
                quotes = quotes.filter(date__range=(from_dt, to_dt))

        except ValueError:
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return HttpResponse("Invalid date format", status=400)
            messages.warning(request, "Invalid date format.")
    else:
        if from_date:
            quotes = quotes.filter(date__gte=from_date)
        if to_date:
            quotes = quotes.filter(date__lte=to_date)

    quotes = quotes.order_by("date", "hour")

    for q in quotes:
        q.time_slot = format_time_slot(q)

    context = {
        "quotes": quotes,
        "services": Service.objects.all(),
        "status_choices": Booking._meta.get_field("status").choices,
    }

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return render(request, "adminpanel/partials/quote_table.html", context)

    return render(request, "adminpanel/quote_list.html", context)


@require_POST
def update_quote_status(request, quote_id):
    quote = get_object_or_404(Quote, pk=quote_id)
    status = request.POST.get("status")
    if status in dict(Quote._meta.get_field("status").choices):
        quote.status = status
        quote.save()
    return redirect(request.META.get("HTTP_REFERER", "/"))


def quote_detail(request, quote_id):
    quote = get_object_or_404(Quote, pk=quote_id)

    if request.method == "POST":
        form = AdminQuoteForm(request.POST, instance=quote)
        if form.is_valid():
            form.save()
            messages.success(request, "Quote updated successfully!")
            return redirect("quote_list")
    else:
        form = AdminQuoteForm(instance=quote)

    return render(request, "adminpanel/quote_detail.html", {
        "form": form,
        "quote": quote
    })

@require_POST
def delete_quote(request, quote_id):
    quote = get_object_or_404(Quote, pk=quote_id)
    quote.delete()
    messages.success(request, "Quote deleted.")
    return redirect("quote_list")

def update_quote_detail_status(request, quote_id):
    quote = get_object_or_404(Quote, id=quote_id)
    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status and new_status != quote.status:
            quote.status = new_status
            quote.save()
    return redirect("quote_detail", quote_id=quote.id)


# 📌 BOOKINGS MANAGEMENT
from django.contrib import messages  # Optional: show error messages in template

def booking_list(request):
    bookings = Booking.objects.all().order_by('-created_at')

    context = {
        "bookings": bookings,
    }
    return render(request, "adminpanel/booking_list.html", context)

def get_booking_detail(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id)
        data = {
            "service": booking.service_cat.name,
            "date": booking.date.strftime('%Y-%m-%d'),
            "duration": booking.hours_requested,
            "price": str(booking.price),
            "status": booking.status,
            "description": booking.job_description,
        }
        return JsonResponse(data)
    except Booking.DoesNotExist:
        raise Http404("Booking not found")


def booking_detail_admin(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    return render(request, "adminpanel/booking_detail.html", {"booking": booking})

# 📌 CUSTOMERS MANAGEMENT
def customer_list(request):
    customers = Customer.objects.all().order_by("name")
    return render(request, "adminpanel/customer_list.html", {"customers": customers})

def customer_detail(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    quotes = Quote.objects.filter(customer=customer)  # Fetch quotes linked to this customer
    return render(request, "adminpanel/customer_detail.html", {"customer": customer, "quotes": quotes})


# 📌 List All Service Categories & Services
def service_list(request):
    categories = ServiceCategory.objects.all()
    services = Service.objects.all()
    return render(request, "adminpanel/service_list.html", {"categories": categories, "services": services})

# 📌 Add a New Service Category
def add_service_category(request):
    if request.method == "POST":
        form = ServiceCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("service_list")
    else:
        form = ServiceCategoryForm()
    return render(request, "adminpanel/service_category_form.html", {"form": form})

# 📌 Edit an Existing Service Category
def edit_service_category(request, category_id):
    category = get_object_or_404(ServiceCategory, id=category_id)
    if request.method == "POST":
        form = ServiceCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect("service_list")
    else:
        form = ServiceCategoryForm(instance=category)
    return render(request, "adminpanel/service_category_form.html", {"form": form})

# 📌 Delete a Service Category
def delete_service_category(request, category_id):
    category = get_object_or_404(ServiceCategory, id=category_id)
    category.delete()
    return redirect("service_list")

# 📌 Add a New Sub-Service
def add_service(request):
    if request.method == "POST":
        form = ServiceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("service_list")
    else:
        form = ServiceForm()
    return render(request, "adminpanel/service_form.html", {"form": form})

# 📌 Edit an Existing Sub-Service
def edit_service(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    if request.method == "POST":
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            return redirect("service_list")
    else:
        form = ServiceForm(instance=service)
    return render(request, "adminpanel/service_form.html", {"form": form})

# 📌 Delete a Sub-Service
def delete_service(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    service.delete()
    return redirect("service_list")

def format_time_slot(quote):
    start = datetime.combine(quote.date, quote.hour)
    duration = timedelta(hours=quote.hours_requested or 2)
    end = (start + duration).time()
    return f"{quote.hour.strftime('%H:%M')} - {end.strftime('%H:%M')}"

def generate_time_choices(start="09:00", end="17:00", step_minutes=30):
    times = []
    t = datetime.strptime(start, "%H:%M")
    end_time = datetime.strptime(end, "%H:%M")
    while t <= end_time:
        times.append(t.strftime("%H:%M"))
        t += timedelta(minutes=step_minutes)
    return times

STATUS_CHOICES = Booking._meta.get_field("status").choices
# 📌 Booking Calendar View
def booking_calendar(request):
    services = Service.objects.all()  

    time_choices = generate_time_choices()

    upcoming_quotes = Booking.objects.filter(
        status__in=["pending", "approved", "accepted"]
    ).filter(date__gte=timezone.now().date()).order_by("date", "hour")[:5]

    booked_quotes = Booking.objects.filter(
        status="booked",
        date__gte=timezone.now().date()
    ).order_by("date", "hour")[:5]

    # Add time_slot to each quote object
    for quote in upcoming_quotes:
        quote.time_slot = format_time_slot(quote)
    
    for quote in booked_quotes:
        quote.time_slot = format_time_slot(quote)

    return render(request, "adminpanel/booking_calendar.html", {
        "services": services,
        "upcoming_quotes": upcoming_quotes,
        "booked_quotes": booked_quotes,
        "status_choices": STATUS_CHOICES,
        "time_choices": time_choices,
    })

# 📌 API to Fetch Existing Bookings
def get_bookings(request):
    # Fetch all confirmed bookings
    bookings = Booking.objects.all()

    # Fetch all quotes (including unconfirmed ones)
    quotes = Booking.objects.all()

    events = []

    # Add bookings to calendar
    for booking in bookings:
        events.append({
            "id": f"booking-{booking.id}",
            "title": f"Booking - {booking.name}",
            "start": booking.quote.date.strftime("%Y-%m-%dT%H:%M:%S"),
            "color": "blue"  # Set color for bookings
        })

    # Add quotes to calendar
    for quote in quotes:
        events.append({
            "id": f"quote-{quote.id}",
            "title": f"Quote - {quote.name}",
            "start": quote.date.strftime("%Y-%m-%dT%H:%M:%S"),
            "color": "gray"  # Set color for quotes
        })

    return JsonResponse(events, safe=False)


# 📌 API to Create a Booking
def add_booking(request):
    if request.method == "POST":
        data = json.loads(request.body)
        date = data.get("date")
        quote_id = data.get("quote")
        confirmed = data.get("confirmed", False)

        try:
            quote = Quote.objects.get(id=quote_id)
            booking = Booking.objects.create(quote=quote, confirmed=confirmed)
            return JsonResponse({"message": "Booking added", "booking_id": booking.id})
        except Quote.DoesNotExist:
            return JsonResponse({"error": "Quote not found"}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=400)

# 📌 API to Fetch Quote Details by Booking ID
def get_quote_details(request):
    booking_id = request.GET.get("booking_id")

    if not booking_id:
        return JsonResponse({"error": "Booking ID is required"}, status=400)

    booking = get_object_or_404(Booking, id=booking_id)
    quote = booking.quote

    quote_data = {
        "quote_id": quote.id,  # Pass quote ID for approval
        "customer": quote.customer.name,
        "service": quote.service.name,
        "date": quote.date.strftime("%Y-%m-%d %H:%M"),
        "status": quote.status,
        "price": quote.price if quote.price else None,
    }

    return JsonResponse(quote_data)

# 📌 API to Create a New Quote
@csrf_exempt
def add_quote(request):
    if request.method == "POST":
        data = json.loads(request.body)
        try:
            # Get or create customer with email as unique key
            customer, created = Customer.objects.get_or_create(
                email=data["customer_email"],
                defaults={
                    "name": data["customer_name"],
                    "phone": data["customer_phone"]
                }
            )

            quote = Booking.objects.create(
                customer=data["customer_name"],
                zip_code=data["zip_code"],
                job_description=data["job_description"],
                hours_requested=int(data["hours_requested"]),
                date=data["date"],
                hour=data["hour"],
                service_id=data["service"],
            )
            return JsonResponse({"success": True, "quote_id": quote.id})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid method"})


def get_quotes_for_calendar(request):
    events = []

    # 🟢 1. Add all Quotes
    for quote in Booking.objects.all():
        duration = max(quote.hours_requested or 2, 2)  # Minimum 2 hours
        start_time = datetime.combine(quote.date, quote.hour)
        end_time = start_time + timedelta(hours=duration)

        events.append({
            "id": f"quote-{quote.id}",
            "title": f"{quote.name} - {quote.service_cat.name}",
            "start": start_time.isoformat(),
            "end": end_time.isoformat(),
            "color": "#28a745" if quote.status == "booked" else "#ffc107",
            "extendedProps": {
                "customer": quote.name if quote.name else "N/A",
                "zip_code": quote.zip_code or "N/A",
                "email": quote.email if quote.name else "N/A",
                "service": quote.service_cat.name,
                "job_description": quote.job_description or "N/A",
                "time_slots": f"{quote.hour.strftime('%H:%M')} - {end_time.strftime('%H:%M')}",
                "price": str(quote.price) if quote.price else "N/A",
                "status": quote.status,
            }
        })

    # 🔴 2. Add Blocked Time Slots
    for block in BlockedTimeSlot.objects.all():
        if block.all_day:
            events.append({
                "id": f"blocked-{block.id}",
                "title": f"⛔ Blocked: {block.reason or 'Unavailable'} (All Day)",
                "start": block.date.isoformat(),
                "allDay": True,
                "backgroundColor": "#dc3545",
                "borderColor": "#dc3545",
                "textColor": "white",
                "editable": False,
                "extendedProps": {
                    "is_blocked": True,
                    "reason": block.reason or "N/A",
                    "time_slot": "All Day",
                }
            })
        else:
            time_range = f"{block.start_time.strftime('%H:%M')} – {block.end_time.strftime('%H:%M')}"
            events.append({
                "id": f"blocked-{block.id}",
                "title": f"⛔ {block.reason or 'Blocked'}\n{time_range}",
                "start": datetime.combine(block.date, block.start_time).isoformat(),
                "end": datetime.combine(block.date, block.end_time).isoformat(),
                "backgroundColor": "#dc3545",
                "borderColor": "#dc3545",
                "textColor": "white",
                "editable": False,
                "display": "block",
                "extendedProps": {
                    "is_blocked": True,
                    "reason": block.reason or "N/A",
                    "time_slot": time_range,
                }
            })

    return JsonResponse(events, safe=False)



def get_event_details(request):
    quote_id = request.GET.get("event_id")
    try:
        quote = Booking.objects.select_related("customer", "service").get(pk=quote_id)
    except Booking.DoesNotExist:
        return JsonResponse({"error": "Quote not found"}, status=404)

    # Format time slot
    start = datetime.combine(quote.date, quote.hour)
    end = (start + timedelta(hours=quote.hours_requested or 2)).time()
    time_slot = f"{quote.hour.strftime('%H:%M')} - {end.strftime('%H:%M')}"

    return JsonResponse({
        "customer": quote.name,
        "email": quote.email,
        "service": quote.service_cat,
        "date": quote.date.strftime("%b %d"),
        "status": quote.status,
        "price": float(quote.price) if quote.price else None,
        "zip_code": quote.zip_code,
        "description": quote.job_description,
        "time_slots": time_slot,
        "event_id": quote.id,
    })


@csrf_exempt
def book_quote(request):
    if request.method == "POST":
        data = json.loads(request.body)
        quote_id = data.get("quote_id")

        try:
            quote = Quote.objects.get(id=quote_id)
            quote.status = "booked"
            quote.save()
            return JsonResponse({"success": True, "message": "Quote marked as booked!"})
        except Quote.DoesNotExist:
            return JsonResponse({"error": "Quote not found"}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=400)

@csrf_exempt
def decline_quote(request):
    if request.method == "POST":
        data = json.loads(request.body)
        quote_id = data.get("quote_id")

        try:
            quote = Quote.objects.get(id=quote_id)
            quote.status = "declined"
            quote.save()
            return JsonResponse({"success": True, "message": "Quote declined successfully!"})
        except Quote.DoesNotExist:
            return JsonResponse({"error": "Quote not found"}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=400)

def format_time_slot(quote):
    start = datetime.combine(quote.date, quote.hour)
    duration = timedelta(hours=quote.hours_requested or 2)
    end = (start + duration).time()
    return f"{quote.hour.strftime('%H:%M')} - {end.strftime('%H:%M')}"

def get_upcoming_quotes(request):
    upcoming_quotes = Booking.objects.filter(
        status__in=["pending", "approved", "accepted"],
        date__gte=timezone.now().date()
    ).order_by("date", "hour")[:5]

    data = []
    for quote in upcoming_quotes:
        data.append({
            "id": quote.id,
            "customer": quote.customer.name,
            "service": quote.service.name,
            "status": quote.status,
            "zip_code": quote.zip_code,
            "email": quote.customer.email,
            "description": quote.job_description,
            "price": float(quote.price) if quote.price else None,
            "time_slot": format_time_slot(quote),
            "date": quote.date.strftime("%b %d")
        })

    return JsonResponse(data, safe=False)

def ajax_filtered_quotes(request):
    quotes = Quote.objects.filter(status="booked")

    # Service filter
    if service := request.GET.get("service"):
        quotes = quotes.filter(service_id=service)

    # Status filter
    if status := request.GET.get("status"):
        quotes = quotes.filter(status=status)

    # Date range filter
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")

    if from_date:
        quotes = quotes.filter(date__gte=from_date)

    if to_date:
        quotes = quotes.filter(date__lte=to_date)

    quotes = quotes.order_by("date", "hour")

    for q in quotes:
        q.time_slot = format_time_slot(q)

    context = {
        "booked_quotes": quotes,
        "services": Service.objects.all(),
        "status_choices": Quote._meta.get_field("status").choices,
    }

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return render(request, "adminpanel/partials/quote_table.html", context)

    return render(request, "adminpanel/booking_list.html", context)

# 📌 Export Booked Quotes to CSV
def export_quotes_csv(request):
    quotes = Booking.objects.filter(status="booked")

    # Apply filters (same as booking_list)
    service = request.GET.get("service")
    if service:
        quotes = quotes.filter(service_id=service)

    status = request.GET.get("status")
    if status:
        quotes = quotes.filter(status=status)

    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")

    if from_date:
        quotes = quotes.filter(date__gte=from_date)
    if to_date:
        quotes = quotes.filter(date__lte=to_date)

    # CSV response
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=booked_quotes.csv"

    writer = csv.writer(response)
    writer.writerow(["Customer", "Email", "Service", "Date", "Time Slot", "ZIP", "Price", "Status"])

    for q in quotes.select_related("customer", "service"):
        writer.writerow([
            q.customer.name,
            q.customer.email,
            q.service.name,
            q.date,
            format_time_slot(q),
            q.zip_code,
            q.price or "",
            q.status
        ])

    return response


def send_quote_email_view(request, quote_id):
    quote = get_object_or_404(Quote, pk=quote_id)
    customer = quote.customer
    time_slot = format_time_slot(quote)
    # 📝 Get the custom admin message from form
    admin_note = request.POST.get("admin_note", "").strip()

     # ✅ Save timestamp and admin note to the quote
    if not quote.approval_token:
        quote.approval_token = secrets.token_urlsafe(32)

    subject = "Your Quote from Clean & Handy Services"
    from_email = "matyass91@gmail.com"
    to_email = [customer.email]
    bcc = ["matyass91@gmail.com"]  # 👈 Add admin here

    context = {
        "customer": customer,
        "quote": quote,
        "time_slot": time_slot,
        "admin_note": admin_note,
        "request_scheme": request.scheme,
        "domain": get_current_site(request).domain,
    }

    # Render HTML email from template
    html_content = render_to_string("emails/quote_email.html", context)
    text_content = strip_tags(html_content)

    try:
        email = EmailMultiAlternatives(subject, text_content, from_email, to_email, bcc=bcc)
        email.attach_alternative(html_content, "text/html")
        email.send()

        quote.last_admin_note = admin_note
        quote.quote_email_sent_at = timezone.now()
        quote.save(update_fields=["last_admin_note", "quote_email_sent_at", "approval_token"])

        messages.success(request, f"📧 Email sent to {customer.email}")
    except Exception as e:
        messages.error(request, f"❌ Failed to send email: {str(e)}")

    return redirect("quote_detail", quote_id=quote.id)

# 📌 Quote Approval View
def quote_approval_view(request, quote_id, token):
    quote = get_object_or_404(Quote, id=quote_id)

    if quote.approval_token != token:
        return HttpResponseForbidden("Invalid token")

    if quote.status != "accepted":
        quote.status = "accepted"
        quote.save(update_fields=["status"])
    
    send_mail(
        subject="Quote Approved by Customer",
        message=f"The quote #{quote.id} for {quote.customer.name} was approved.\nService: {quote.service.name}\nDate: {quote.date}\nPrice: {quote.price}",
        from_email="noreply@cleanhandy.com",
        recipient_list=["admin@email.com"]
    )

    return render(request, "quotes/quote_approved.html", {"quote": quote})

# 📌 Quote Decline View
def quote_decline_view(request, quote_id, token):
    quote = get_object_or_404(Quote, id=quote_id)

    if quote.approval_token != token:
        return HttpResponseForbidden("Invalid token")

    if quote.status != "declined":
        quote.status = "declined"
        quote.save(update_fields=["status"])

    return render(request, "quotes/quote_declined.html", {"quote": quote})


@require_POST
def block_time_slot(request):
    date = request.POST.get("date")
    start_time = request.POST.get("start_time")
    end_time = request.POST.get("end_time")
    reason = request.POST.get("reason")
    all_day = request.POST.get("all_day") == "on"

    if all_day:
        start_time = None
        end_time = None

    BlockedTimeSlot.objects.create(
        date=date,
        start_time=start_time,
        end_time=end_time,
        reason=reason,
        all_day=all_day
    )
    messages.success(request, "⛔ Time slot blocked.")
    return redirect("booking_calendar")


def giftcard_discount(request):
    discount_codes = DiscountCode.objects.all()
    giftcards = GiftCard.objects.all()

    return render(request, "adminpanel/giftcard_discount.html", {
        "discount_codes": discount_codes,
        "giftcards": giftcards,
    })










