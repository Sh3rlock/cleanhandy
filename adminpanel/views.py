from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.db import models
from django.core.paginator import Paginator
from quotes.models import Quote, Service, ServiceCategory, Booking, NewsletterSubscriber, OfficeQuote, HandymanQuote, PostEventCleaningQuote
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
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseBadRequest

# For PDF generation
from django.template.loader import get_template
from django.http import HttpResponse
from weasyprint import HTML
from django.conf import settings
import os


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
    latest_office_quotes = OfficeQuote.objects.all().order_by("-created_at")[:10]
    latest_handyman_quotes = HandymanQuote.objects.all().order_by("-created_at")[:10]

    discounts = DiscountCode.objects.all()
    giftcards = GiftCard.objects.all()

    total_quotes = Booking.objects.count()
    total_bookings = Booking.objects.count()
    total_customers = User.objects.count()
    total_subscribers = NewsletterSubscriber.objects.count()
    total_office_quotes = OfficeQuote.objects.count()
    total_handyman_quotes = HandymanQuote.objects.count()
    total_post_event_cleaning_quotes = PostEventCleaningQuote.objects.count()

    # Status counts for handyman quotes
    handyman_quote_status_counts = {
        'pending': HandymanQuote.objects.filter(status='pending').count(),
        'contacted': HandymanQuote.objects.filter(status='contacted').count(),
        'quoted': HandymanQuote.objects.filter(status='quoted').count(),
        'completed': HandymanQuote.objects.filter(status='completed').count(),
        'cancelled': HandymanQuote.objects.filter(status='cancelled').count(),
    }

    # Status counts for post event cleaning quotes
    post_event_cleaning_quote_status_counts = {
        'pending': PostEventCleaningQuote.objects.filter(status='pending').count(),
        'contacted': PostEventCleaningQuote.objects.filter(status='contacted').count(),
        'quoted': PostEventCleaningQuote.objects.filter(status='quoted').count(),
        'completed': PostEventCleaningQuote.objects.filter(status='completed').count(),
        'cancelled': PostEventCleaningQuote.objects.filter(status='cancelled').count(),
    }

    # Status counts for office quotes
    office_quote_status_counts = {
        'pending': OfficeQuote.objects.filter(status='pending').count(),
        'contacted': OfficeQuote.objects.filter(status='contacted').count(),
        'quoted': OfficeQuote.objects.filter(status='quoted').count(),
        'completed': OfficeQuote.objects.filter(status='completed').count(),
        'cancelled': OfficeQuote.objects.filter(status='cancelled').count(),
    }

    return render(request, "adminpanel/dashboard.html", {
        "latest_quotes": latest_quotes,
        "latest_bookings": latest_bookings,
        "latest_customers": latest_customers,
        "latest_subscribers": latest_subscribers,
        "latest_office_quotes": latest_office_quotes,
        "latest_handyman_quotes": latest_handyman_quotes,
        "discounts": discounts,
        "giftcards": giftcards,
        "total_quotes": total_quotes,
        "total_bookings": total_bookings,
        "total_customers": total_customers,
        "total_subscribers": total_subscribers,
        "total_office_quotes": total_office_quotes,
        "total_handyman_quotes": total_handyman_quotes,
        "total_post_event_cleaning_quotes": total_post_event_cleaning_quotes,
        "handyman_quote_status_counts": handyman_quote_status_counts,
        "post_event_cleaning_quote_status_counts": post_event_cleaning_quote_status_counts,
        "office_quote_status_counts": office_quote_status_counts,
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
    quote = get_object_or_404(Booking, pk=quote_id)

    if request.method == "POST":
        # Get data from POST and update the quote instance
        quote.status = request.POST.get("status", quote.status)
        quote.date = request.POST.get("date", quote.date)
        quote.hour = request.POST.get("hour", quote.hour)
        quote.hours_requested = request.POST.get("hours_requested", quote.hours_requested)
        quote.price = request.POST.get("price", quote.price)
        quote.address = request.POST.get("address", quote.address)
        quote.apartment = request.POST.get("apartment", quote.apartment)
        quote.zip_code = request.POST.get("zip_code", quote.zip_code)

        quote.save()
        messages.success(request, "Quote updated successfully!")
        return redirect("booking_list")

    return render(request, "adminpanel/quote_detail.html", {
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

    # Filter: Status
    selected_statuses = request.GET.getlist('status')
    if selected_statuses:
        bookings = bookings.filter(status__in=selected_statuses)

    selected_categories = request.GET.getlist('category')
    if selected_categories:
        bookings = bookings.filter(service_cat_id__in=selected_categories)

    status_list = ['pending', 'confirmed', 'completed', 'cancelled']

      # ⏳ Date filter
    date_filter = request.GET.get('date_filter')
    today = timezone.localdate()

    if date_filter == "today":
        bookings = bookings.filter(date=today)
    elif date_filter == "last_7":
        bookings = bookings.filter(date__gte=today - timedelta(days=7))
    elif date_filter == "last_30":
        bookings = bookings.filter(date__gte=today - timedelta(days=30))

    # Status and category filters
    selected_statuses = request.GET.getlist('status')
    selected_categories = request.GET.getlist('category')

    if selected_statuses:
        bookings = bookings.filter(status__in=selected_statuses)
    if selected_categories:
        bookings = bookings.filter(service_cat_id__in=selected_categories)

    return render(request, 'adminpanel/booking_list.html', {
        'bookings': bookings,
        'status_list': ['pending', 'confirmed', 'completed', 'cancelled'],
        'service_categories': ServiceCategory.objects.filter(name__in=['Home', 'Commercial']),
        'selected_statuses': selected_statuses,
        'selected_categories': selected_categories,
        'selected_date_filter': date_filter,
    })

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


@staff_member_required
def booking_detail_admin(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.method == 'POST':
        booking.status = request.POST.get('status')
        booking.date = request.POST.get('date')
        booking.hour = request.POST.get('hour')
        booking.num_cleaners = request.POST.get('num_cleaners')
        booking.hours_requested = request.POST.get('hours_requested')
        booking.price = request.POST.get('price')
        booking.address = request.POST.get('address')
        booking.apartment = request.POST.get('apartment')
        booking.zip_code = request.POST.get('zip_code')
        booking.save()
        return redirect('booking_detail_admin', booking_id=booking.id)
    
    return render(request, "adminpanel/booking_detail.html", {"booking": booking})


# 📌 CUSTOMERS MANAGEMENT
def customer_list(request):
    customers = User.objects.all().order_by("username")
    return render(request, "adminpanel/customer_list.html", {"customers": customers})

def office_quote_list(request):
    office_quotes = OfficeQuote.objects.all().order_by("-created_at")
    return render(request, "adminpanel/office_quote_list.html", {"office_quotes": office_quotes})

def office_quote_detail(request, quote_id):
    office_quote = get_object_or_404(OfficeQuote, pk=quote_id)
    
    if request.method == "POST":
        # Update the quote status and admin notes
        office_quote.status = request.POST.get("status", office_quote.status)
        office_quote.admin_notes = request.POST.get("admin_notes", office_quote.admin_notes)
        office_quote.save()
        messages.success(request, "Office quote updated successfully!")
        return redirect("office_quote_list")
    
    return render(request, "adminpanel/office_quote_detail.html", {
        "office_quote": office_quote
    })

from django.contrib.auth.models import User

def customer_detail(request, username):
    user = get_object_or_404(User, username=username)
    profile = user.profile
    quotes = Booking.objects.filter(email=user.email)  
    addresses = profile.addresses.all()
    
    return render(request, "adminpanel/customer_detail.html", {
        "user": user,
        "profile": profile,
        "quotes": quotes,
        "addresses": addresses
    })



def subscriber_list(request):
    subscribers = NewsletterSubscriber.objects.all().order_by("-subscribed_at")
    return render(request, "adminpanel/subscriber_list.html", {"subscribers": subscribers})


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
        "customer": quote.name,
        "service": quote.service_cat.name,
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
            "customer": quote.name,
            "service": quote.service_cat.name,
            "status": quote.status,
            "zip_code": quote.zip_code,
            "email": quote.email,
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
            q.name,
            q.email,
            q.service_cat.name,
            q.date,
            format_time_slot(q),
            q.zip_code,
            q.price or "",
            q.status
        ])

    return response


def send_quote_email_view(request, quote_id):
    quote = get_object_or_404(Booking, pk=quote_id)

    if request.method == "POST" and request.POST.get("email_action") == "send_quote_email":
        # Save price if provided
        price = request.POST.get("price")
        if price is not None and price != "":
            try:
                quote.price = float(price)
                quote.save(update_fields=["price"])
            except ValueError:
                pass  # Optionally, handle invalid price input

        customer = quote.name
        time_slot = quote.get_time_slots()  # or format_time_slot(quote)

        admin_note = request.POST.get("admin_note", "").strip()

        if not quote.approval_token:
            quote.approval_token = secrets.token_urlsafe(32)

        subject = "Your Quote from Clean & Handy Services"
        from_email = "matyass91@gmail.com"
        to_email = ["matyass91@gmail.com"]
        bcc = ["matyass91@gmail.com"]

        context = {
            "customer": customer,
            "quote": quote,
            "time_slot": time_slot,
            "admin_note": admin_note,
            "request_scheme": request.scheme,
            "domain": get_current_site(request).domain,
        }

        html_content = render_to_string("emails/quote_email.html", context)
        text_content = strip_tags(html_content)

        try:
            email = EmailMultiAlternatives(subject, text_content, from_email, to_email, bcc=bcc)
            email.attach_alternative(html_content, "text/html")
            email.send()

            quote.last_admin_note = admin_note
            quote.quote_email_sent_at = timezone.now()
            quote.save(update_fields=["last_admin_note", "quote_email_sent_at", "approval_token"])

            messages.success(request, f"📧 Email sent to {quote.email}")
        except Exception as e:
            messages.error(request, f"❌ Failed to send email: {str(e)}")

    return redirect("quote_detail", quote_id=quote.id)


# 📌 Quote Approval View
def quote_approval_view(request, quote_id, token):
    quote = get_object_or_404(Booking, id=quote_id)

    if quote.approval_token != token:
        return HttpResponseForbidden("Invalid token")

    if quote.status != "accepted":
        quote.status = "accepted"
        quote.save(update_fields=["status"])

    # Prepare email content
    subject = f"Quote Approved: #{quote.id} for {quote.name}"
    message = (
        f"The quote #{quote.id} for {quote.name} was approved.\n"
        f"Service: {quote.service_cat.name}\n"
        f"Date: {quote.date}\n"
        f"Time: {quote.hour}\n"
        f"Duration: {quote.hours_requested} hour(s)\n"
        f"Price: {quote.price}\n"
        f"Address: {quote.address}"
        f"{', Apt ' + quote.apartment if quote.apartment else ''}\n"
        f"ZIP: {quote.zip_code}\n"
        f"Status: {quote.status}\n"
        f"Email: {quote.email}\n"
        f"Phone: {quote.phone}\n"
        f"Job Description: {quote.job_description}"
    )
    from_email = "noreply@cleanhandy.com"
    recipients = [quote.email, "matyass91@gmail.com"]

    send_mail(
        subject=subject,
        message=message,
        from_email=from_email,
        recipient_list=recipients,
        fail_silently=False,
    )

    return render(request, "quotes/quote_approved.html", {"quote": quote})

# 📌 Quote Decline View
def quote_decline_view(request, quote_id, token):
    quote = get_object_or_404(Booking, id=quote_id)

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

@login_required
def add_subscriber(request):
    if request.method == "POST":
        try:
            NewsletterSubscriber.objects.create(
                email=request.POST.get("subscriber_email"),
            )

            next_url = request.POST.get("next")
            return redirect(next_url) if next_url else redirect("subscriber_list")

        except Exception as e:
            return HttpResponseBadRequest(f"Invalid data: {e}")

    return HttpResponseBadRequest("Invalid method")

def export_subscribers_csv(request):
    # Create the HttpResponse with CSV headers
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=subscribers.csv'

    writer = csv.writer(response)
    writer.writerow(['Email', 'Subscribed At'])  # Header row

    for subscriber in NewsletterSubscriber.objects.order_by('-subscribed_at')[:100]:
        writer.writerow([subscriber.email, subscriber.subscribed_at.strftime('%Y-%m-%d %H:%M')])

    return response

def export_office_quotes_csv(request):
    # Create the HttpResponse with CSV headers
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=office_quotes.csv'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Business Address', 'Square Footage', 'Job Description', 'Status', 'Created At', 'Admin Notes'])

    for quote in OfficeQuote.objects.all().order_by('-created_at'):
        writer.writerow([
            quote.id,
            quote.name,
            quote.email,
            quote.phone_number,
            quote.business_address,
            quote.square_footage,
            quote.job_description,
            quote.get_status_display(),
            quote.created_at.strftime('%Y-%m-%d %H:%M'),
            quote.admin_notes or ''
        ])

    return response

def send_office_quote_email(request, quote_id):
    office_quote = get_object_or_404(OfficeQuote, pk=quote_id)
    
    if request.method == "POST":
        email_type = request.POST.get("email_type")
        custom_message = request.POST.get("custom_message", "")
        
        if email_type == "quote_update":
            subject = f"Office Cleaning Quote Update - #{office_quote.id}"
            template_name = "emails/office_quote_update.html"
        elif email_type == "status_update":
            subject = f"Office Cleaning Quote Status Update - #{office_quote.id}"
            template_name = "emails/office_quote_status.html"
        else:
            subject = f"Office Cleaning Quote - #{office_quote.id}"
            template_name = "emails/office_quote_general.html"
        
        context = {
            "office_quote": office_quote,
            "custom_message": custom_message,
            "request_scheme": request.scheme,
            "domain": get_current_site(request).domain,
        }
        
        html_content = render_to_string(template_name, context)
        text_content = strip_tags(html_content)
        
        try:
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email="noreply@cleanhandy.com",
                to=[office_quote.email],
                bcc=["matyass91@gmail.com"]  # Admin copy
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            messages.success(request, f"📧 Email sent successfully to {office_quote.email}")
        except Exception as e:
            messages.error(request, f"❌ Failed to send email: {str(e)}")
    
    return redirect("office_quote_detail", quote_id=office_quote.id)

def generate_office_quote_pdf(request, quote_id):
    office_quote = get_object_or_404(OfficeQuote, pk=quote_id)
    
    # Generate PDF using WeasyPrint
    try:
        template = get_template("adminpanel/office_quote_pdf.html")
        context = {
            "office_quote": office_quote,
            "company_info": {
                "name": "Clean & Handy Services",
                "address": "123 Business Street, City, State 12345",
                "phone": "+1 (555) 123-4567",
                "email": "info@cleanhandy.com",
                "website": "www.cleanhandy.com"
            }
        }
        
        html_string = template.render(context)
        
        # Create PDF response
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f"attachment; filename=office_quote_{office_quote.id}.pdf"
        
        # Generate PDF
        HTML(string=html_string).write_pdf(response)
        
        return response
        
    except Exception as e:
        messages.error(request, f"❌ Failed to generate PDF: {str(e)}")
        return redirect("office_quote_detail", quote_id=office_quote.id)


# ============================================================================
# HANDYMAN QUOTE MANAGEMENT
# ============================================================================

def handyman_quote_list(request):
    """List all handyman quotes with filtering and search"""
    handyman_quotes = HandymanQuote.objects.all().order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        handyman_quotes = handyman_quotes.filter(status=status_filter)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        handyman_quotes = handyman_quotes.filter(
            models.Q(name__icontains=search_query) |
            models.Q(email__icontains=search_query) |
            models.Q(phone_number__icontains=search_query) |
            models.Q(address__icontains=search_query) |
            models.Q(job_description__icontains=search_query)
        )
    
    # Date range filter
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    
    if from_date:
        handyman_quotes = handyman_quotes.filter(created_at__date__gte=from_date)
    if to_date:
        handyman_quotes = handyman_quotes.filter(created_at__date__lte=to_date)
    
    # Status choices for filter dropdown
    status_choices = [
        ('pending', 'Pending'),
        ('contacted', 'Contacted'),
        ('quoted', 'Quoted'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    context = {
        'handyman_quotes': handyman_quotes,
        'status_choices': status_choices,
        'selected_status': status_filter,
        'search_query': search_query,
        'from_date': from_date,
        'to_date': to_date,
    }
    
    return render(request, 'adminpanel/handyman_quote_list.html', context)


def handyman_quote_detail(request, quote_id):
    """View and edit handyman quote details"""
    handyman_quote = get_object_or_404(HandymanQuote, pk=quote_id)
    
    if request.method == "POST":
        # Update the quote status and admin notes
        handyman_quote.status = request.POST.get("status", handyman_quote.status)
        handyman_quote.admin_notes = request.POST.get("admin_notes", handyman_quote.admin_notes)
        handyman_quote.save()
        messages.success(request, "Handyman quote updated successfully!")
        return redirect("handyman_quote_list")
    
    # Status choices for dropdown
    status_choices = [
        ('pending', 'Pending'),
        ('contacted', 'Contacted'),
        ('quoted', 'Quoted'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    return render(request, "adminpanel/handyman_quote_detail.html", {
        "handyman_quote": handyman_quote,
        "status_choices": status_choices,
    })


@require_POST
def update_handyman_quote_status(request, quote_id):
    """Update handyman quote status via AJAX"""
    handyman_quote = get_object_or_404(HandymanQuote, pk=quote_id)
    new_status = request.POST.get("status")
    
    if new_status in ['pending', 'contacted', 'quoted', 'completed', 'cancelled']:
        handyman_quote.status = new_status
        handyman_quote.save()
        
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "success": True,
                "message": f"Status updated to {new_status.title()}"
            })
        else:
            messages.success(request, f"Status updated to {new_status.title()}")
    else:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "success": False,
                "message": "Invalid status"
            }, status=400)
        else:
            messages.error(request, "Invalid status")
    
    return redirect(request.META.get("HTTP_REFERER", "handyman_quote_list"))


def export_handyman_quotes_csv(request):
    """Export handyman quotes to CSV"""
    handyman_quotes = HandymanQuote.objects.all().order_by('-created_at')
    
    # Apply filters if provided
    status_filter = request.GET.get('status')
    if status_filter:
        handyman_quotes = handyman_quotes.filter(status=status_filter)
    
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    
    if from_date:
        handyman_quotes = handyman_quotes.filter(created_at__date__gte=from_date)
    if to_date:
        handyman_quotes = handyman_quotes.filter(created_at__date__lte=to_date)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=handyman_quotes.csv'
    
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Name', 'Email', 'Phone', 'Address', 'Job Description', 
        'Status', 'Admin Notes', 'Created At'
    ])
    
    for quote in handyman_quotes:
        writer.writerow([
            quote.id,
            quote.name,
            quote.email,
            quote.phone_number,
            quote.address,
            quote.job_description,
            quote.get_status_display(),
            quote.admin_notes or '',
            quote.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return response


def send_handyman_quote_email(request, quote_id):
    """Send email to handyman quote customer"""
    handyman_quote = get_object_or_404(HandymanQuote, pk=quote_id)
    
    if request.method == "POST":
        email_type = request.POST.get("email_type")
        custom_message = request.POST.get("custom_message", "")
        
        if email_type == "quote_update":
            subject = f"Handyman Quote Update - #{handyman_quote.id}"
            template_name = "emails/handyman_quote_update.html"
        elif email_type == "status_update":
            subject = f"Handyman Quote Status Update - #{handyman_quote.id}"
            template_name = "emails/handyman_quote_status.html"
        else:
            subject = f"Handyman Quote - #{handyman_quote.id}"
            template_name = "emails/handyman_quote_general.html"
        
        context = {
            "handyman_quote": handyman_quote,
            "custom_message": custom_message,
            "request_scheme": request.scheme,
            "domain": get_current_site(request).domain,
        }
        
        html_content = render_to_string(template_name, context)
        text_content = strip_tags(html_content)
        
        try:
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email="noreply@cleanhandy.com",
                to=[handyman_quote.email],
                bcc=["matyass91@gmail.com"]  # Admin copy
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            messages.success(request, f"📧 Email sent successfully to {handyman_quote.email}")
        except Exception as e:
            messages.error(request, f"❌ Failed to send email: {str(e)}")
    
    return redirect("handyman_quote_detail", quote_id=handyman_quote.id)


def generate_handyman_quote_pdf(request, quote_id):
    """Generate PDF for handyman quote"""
    handyman_quote = get_object_or_404(HandymanQuote, pk=quote_id)
    
    try:
        template = get_template("adminpanel/handyman_quote_pdf.html")
        context = {
            "handyman_quote": handyman_quote,
            "company_info": {
                "name": "Clean & Handy Services",
                "address": "123 Business Street, City, State 12345",
                "phone": "+1 (555) 123-4567",
                "email": "info@cleanhandy.com",
                "website": "www.cleanhandy.com"
            }
        }
        
        html_string = template.render(context)
        
        # Create PDF response
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f"attachment; filename=handyman_quote_{handyman_quote.id}.pdf"
        
        # Generate PDF
        HTML(string=html_string).write_pdf(response)
        
        return response
        
    except Exception as e:
        messages.error(request, f"❌ Failed to generate PDF: {str(e)}")
        return redirect("handyman_quote_detail", quote_id=handyman_quote.id)


@require_POST
def delete_handyman_quote(request, quote_id):
    """Delete handyman quote"""
    handyman_quote = get_object_or_404(HandymanQuote, pk=quote_id)
    handyman_quote.delete()
    messages.success(request, "Handyman quote deleted successfully.")
    return redirect("handyman_quote_list")


# ============================================================================
# POST EVENT CLEANING QUOTE MANAGEMENT
# ============================================================================

def post_event_cleaning_quote_list(request):
    """List all post event cleaning quotes with filtering and search"""
    post_event_quotes = PostEventCleaningQuote.objects.all().order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        post_event_quotes = post_event_quotes.filter(status=status_filter)
    
    # Filter by event type
    event_type_filter = request.GET.get('event_type')
    if event_type_filter:
        post_event_quotes = post_event_quotes.filter(event_type=event_type_filter)
    
    # Filter by venue size
    venue_size_filter = request.GET.get('venue_size')
    if venue_size_filter:
        post_event_quotes = post_event_quotes.filter(venue_size=venue_size_filter)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        post_event_quotes = post_event_quotes.filter(
            models.Q(name__icontains=search_query) |
            models.Q(email__icontains=search_query) |
            models.Q(phone_number__icontains=search_query) |
            models.Q(address__icontains=search_query) |
            models.Q(event_description__icontains=search_query) |
            models.Q(special_requirements__icontains=search_query)
        )
    
    # Date range filter
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    if from_date:
        post_event_quotes = post_event_quotes.filter(created_at__date__gte=from_date)
    if to_date:
        post_event_quotes = post_event_quotes.filter(created_at__date__lte=to_date)
    
    # Pagination
    paginator = Paginator(post_event_quotes, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_quotes = PostEventCleaningQuote.objects.count()
    pending_quotes = PostEventCleaningQuote.objects.filter(status='pending').count()
    completed_quotes = PostEventCleaningQuote.objects.filter(status='completed').count()
    
    context = {
        'page_obj': page_obj,
        'total_quotes': total_quotes,
        'pending_quotes': pending_quotes,
        'completed_quotes': completed_quotes,
        'status_choices': PostEventCleaningQuote.STATUS_CHOICES,
        'event_type_choices': PostEventCleaningQuote.EVENT_TYPE_CHOICES,
        'venue_size_choices': PostEventCleaningQuote.VENUE_SIZE_CHOICES,
        'current_filters': {
            'status': status_filter,
            'event_type': event_type_filter,
            'venue_size': venue_size_filter,
            'search': search_query,
            'from_date': from_date,
            'to_date': to_date,
        }
    }
    
    return render(request, 'adminpanel/post_event_cleaning_quote_list.html', context)


def post_event_cleaning_quote_detail(request, quote_id):
    """Display detailed view of a post event cleaning quote"""
    quote = get_object_or_404(PostEventCleaningQuote, id=quote_id)
    
    if request.method == 'POST':
        # Update quote status
        new_status = request.POST.get('status')
        admin_notes = request.POST.get('admin_notes', '')
        
        if new_status and new_status in [choice[0] for choice in PostEventCleaningQuote.STATUS_CHOICES]:
            quote.status = new_status
            quote.admin_notes = admin_notes
            quote.save()
            messages.success(request, f"Quote status updated to {quote.get_status_display()}")
            return redirect('post_event_cleaning_quote_detail', quote_id=quote.id)
    
    return render(request, 'adminpanel/post_event_cleaning_quote_detail.html', {'quote': quote})


def update_post_event_cleaning_quote_status(request, quote_id):
    """Update post event cleaning quote status via AJAX"""
    if request.method == 'POST':
        quote = get_object_or_404(PostEventCleaningQuote, id=quote_id)
        new_status = request.POST.get('status')
        
        if new_status and new_status in [choice[0] for choice in PostEventCleaningQuote.STATUS_CHOICES]:
            quote.status = new_status
            quote.save()
            return JsonResponse({'success': True, 'status': quote.get_status_display()})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})


def export_post_event_cleaning_quotes_csv(request):
    """Export post event cleaning quotes to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="post_event_cleaning_quotes.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Name', 'Email', 'Phone', 'Address', 'Event Type', 'Venue Size',
        'Event Date', 'Cleaning Date', 'Event Description', 'Special Requirements',
        'Status', 'Admin Notes', 'Created At'
    ])
    
    quotes = PostEventCleaningQuote.objects.all().order_by('-created_at')
    for quote in quotes:
        writer.writerow([
            quote.id,
            quote.name,
            quote.email,
            quote.phone_number,
            quote.address,
            quote.get_event_type_display(),
            quote.get_venue_size_display(),
            quote.event_date,
            quote.cleaning_date,
            quote.event_description,
            quote.special_requirements or '',
            quote.get_status_display(),
            quote.admin_notes or '',
            quote.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return response


def send_post_event_cleaning_quote_email(request, quote_id):
    """Send email to customer about their post event cleaning quote"""
    quote = get_object_or_404(PostEventCleaningQuote, id=quote_id)
    
    try:
        # Send email to customer
        subject = f"Post Event Cleaning Quote Update - #{quote.id}"
        message = f"""
        Dear {quote.name},
        
        Thank you for your post event cleaning quote request. We have reviewed your requirements and will contact you soon.
        
        Quote Details:
        - Event Type: {quote.get_event_type_display()}
        - Venue Size: {quote.get_venue_size_display()}
        - Event Date: {quote.event_date}
        - Preferred Cleaning Date: {quote.cleaning_date}
        - Status: {quote.get_status_display()}
        
        If you have any questions, please don't hesitate to contact us.
        
        Best regards,
        CleanHandy Team
        """
        
        send_mail(
            subject,
            message,
            'noreply@cleanhandy.com',
            [quote.email],
            fail_silently=False,
        )
        
        messages.success(request, f"Email sent successfully to {quote.email}")
    except Exception as e:
        messages.error(request, f"Failed to send email: {str(e)}")
    
    return redirect('post_event_cleaning_quote_detail', quote_id=quote.id)


def generate_post_event_cleaning_quote_pdf(request, quote_id):
    """Generate PDF for post event cleaning quote"""
    quote = get_object_or_404(PostEventCleaningQuote, id=quote_id)
    
    try:
        # Generate PDF using the template
        template = get_template('adminpanel/post_event_cleaning_quote_pdf.html')
        context = {'quote': quote}
        html = template.render(context)
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="post_event_cleaning_quote_{quote.id}.pdf"'
        
        # Use weasyprint for PDF generation
        HTML(string=html).write_pdf(response)
        
        return response
    except Exception as e:
        messages.error(request, f"Failed to generate PDF: {str(e)}")
        return redirect('post_event_cleaning_quote_detail', quote_id=quote.id)


def delete_post_event_cleaning_quote(request, quote_id):
    """Delete a post event cleaning quote"""
    quote = get_object_or_404(PostEventCleaningQuote, id=quote_id)
    quote.delete()
    messages.success(request, "Post event cleaning quote deleted successfully.")
    return redirect("post_event_cleaning_quote_list")










