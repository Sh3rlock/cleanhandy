from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.db import models
from django.core.paginator import Paginator
from quotes.models import Quote, Service, ServiceCategory, Booking, NewsletterSubscriber, OfficeQuote, HandymanQuote, PostEventCleaningQuote, HomeCleaningQuoteRequest, PriceVariable, PriceVariableCategory, TaxSettings
from giftcards.models import GiftCard, DiscountCode
from quotes.forms import CleaningQuoteForm, HandymanQuoteForm
from customers.models import Customer
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from .forms import ServiceForm, ServiceCategoryForm, PriceVariableForm, PriceVariableCategoryForm, TaxSettingsForm

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

# Import payment link functions
from quotes.stripe_views import create_final_payment_link, send_final_payment_email

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
    total_office_cleaning_quotes = OfficeQuote.objects.count()  # Office Cleaning Quotes use OfficeQuote model
    total_handyman_quotes = HandymanQuote.objects.count()
    total_post_event_cleaning_quotes = PostEventCleaningQuote.objects.count()
    total_home_cleaning_quotes = HomeCleaningQuoteRequest.objects.count()

    # Status counts for office cleaning quotes (using OfficeQuote model)
    office_cleaning_quote_status_counts = {
        'pending': OfficeQuote.objects.filter(status='pending').count(),
        'reviewed': OfficeQuote.objects.filter(status='reviewed').count(),
        'quoted': OfficeQuote.objects.filter(status='quoted').count(),
        'accepted': OfficeQuote.objects.filter(status='accepted').count(),
        'declined': OfficeQuote.objects.filter(status='declined').count(),
    }

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

    # Status counts for home cleaning quotes
    # Note: HomeCleaningQuoteRequest doesn't have a status field, so we show all as pending
    home_cleaning_quote_status_counts = {
        'pending': total_home_cleaning_quotes,
        'reviewed': 0,
        'quoted': 0,
        'accepted': 0,
        'declined': 0,
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
        "total_home_cleaning_quotes": total_home_cleaning_quotes,
        "total_office_cleaning_quotes": total_office_cleaning_quotes,
        "handyman_quote_status_counts": handyman_quote_status_counts,
        "post_event_cleaning_quote_status_counts": post_event_cleaning_quote_status_counts,
        "office_quote_status_counts": office_quote_status_counts,
        "office_cleaning_quote_status_counts": office_cleaning_quote_status_counts,
        "home_cleaning_quote_status_counts": home_cleaning_quote_status_counts,
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

    # Get outstanding payments (completed bookings that are not fully paid)
    outstanding_payments = Booking.objects.filter(
        status='completed'
    ).exclude(
        payment_status='paid'
    ).order_by('-created_at')

    return render(request, 'adminpanel/booking_list.html', {
        'bookings': bookings,
        'outstanding_payments': outstanding_payments,
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

# 📌 Price Variable Category Management Views
def price_variable_category_list(request):
    categories = PriceVariableCategory.objects.all()
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        categories = categories.filter(is_active=True)
    elif status_filter == 'inactive':
        categories = categories.filter(is_active=False)
    
    # Search filter
    search_query = request.GET.get('search', '')
    if search_query:
        categories = categories.filter(name__icontains=search_query)
    
    # Sort options
    sort_by = request.GET.get('sort_by', 'name')
    sort_order = request.GET.get('sort_order', 'asc')
    
    # For count sorting, we need to annotate with the count
    if sort_by == 'count':
        from django.db.models import Count
        categories = categories.annotate(var_count=Count('pricevariable'))
        order_field = 'var_count'
    elif sort_by == 'name':
        order_field = 'name'
    elif sort_by == 'created':
        order_field = 'created_at'
    elif sort_by == 'updated':
        order_field = 'updated_at'
    else:
        order_field = 'name'
    
    if sort_order == 'desc':
        order_field = f'-{order_field}'
    
    categories = categories.order_by(order_field)
    
    return render(request, "adminpanel/price_variable_category_list.html", {
        "categories": categories,
        "status_filter": status_filter,
        "search_query": search_query,
        "sort_by": sort_by,
        "sort_order": sort_order,
    })

# 📌 Add a New Price Variable Category
def add_price_variable_category(request):
    if request.method == "POST":
        form = PriceVariableCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Price variable category added successfully!")
            return redirect("price_variable_category_list")
    else:
        form = PriceVariableCategoryForm()
    return render(request, "adminpanel/price_variable_category_form.html", {"form": form, "action": "Add"})

# 📌 Edit an Existing Price Variable Category
def edit_price_variable_category(request, category_id):
    category = get_object_or_404(PriceVariableCategory, id=category_id)
    if request.method == "POST":
        form = PriceVariableCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Price variable category updated successfully!")
            return redirect("price_variable_category_list")
    else:
        form = PriceVariableCategoryForm(instance=category)
    return render(request, "adminpanel/price_variable_category_form.html", {"form": form, "action": "Edit", "category": category})

# 📌 Delete a Price Variable Category
def delete_price_variable_category(request, category_id):
    category = get_object_or_404(PriceVariableCategory, id=category_id)
    if request.method == "POST":
        # Check if there are any price variables using this category
        if PriceVariable.objects.filter(category=category).exists():
            messages.error(request, f"Cannot delete category '{category.name}' because it has associated price variables. Please remove or reassign those variables first.")
            return redirect("price_variable_category_list")
        category.delete()
        messages.success(request, "Price variable category deleted successfully!")
        return redirect("price_variable_category_list")
    return render(request, "adminpanel/price_variable_category_confirm_delete.html", {"category": category})

# 📌 Price Variable Management Views
def price_variable_list(request):
    price_variables = PriceVariable.objects.all()
    
    # Filter by category
    category_filter = request.GET.get('category', '')
    if category_filter:
        if category_filter == 'none':
            # Filter for variables with no category
            price_variables = price_variables.filter(category__isnull=True)
        else:
            try:
                category_id = int(category_filter)
                price_variables = price_variables.filter(category_id=category_id)
            except (ValueError, TypeError):
                pass
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        price_variables = price_variables.filter(is_active=True)
    elif status_filter == 'inactive':
        price_variables = price_variables.filter(is_active=False)
    
    # Search filter
    search_query = request.GET.get('search', '')
    if search_query:
        price_variables = price_variables.filter(variable_name__icontains=search_query)
    
    # Sort options
    sort_by = request.GET.get('sort_by', 'category')
    sort_order = request.GET.get('sort_order', 'asc')
    
    if sort_by == 'category':
        order_field = 'category__name'
    elif sort_by == 'name':
        order_field = 'variable_name'
    elif sort_by == 'price':
        order_field = 'price'
    elif sort_by == 'created':
        order_field = 'created_at'
    elif sort_by == 'updated':
        order_field = 'updated_at'
    else:
        order_field = 'category__name'
    
    if sort_order == 'desc':
        order_field = f'-{order_field}'
    
    price_variables = price_variables.order_by(order_field)
    
    # Get all categories for the filter dropdown
    all_categories = PriceVariableCategory.objects.filter(is_active=True).order_by('name')
    
    return render(request, "adminpanel/price_variable_list.html", {
        "price_variables": price_variables,
        "all_categories": all_categories,
        "category_filter": category_filter,
        "status_filter": status_filter,
        "search_query": search_query,
        "sort_by": sort_by,
        "sort_order": sort_order,
    })

# 📌 Add a New Price Variable
def add_price_variable(request):
    if request.method == "POST":
        form = PriceVariableForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Price variable added successfully!")
            return redirect("price_variable_list")
    else:
        form = PriceVariableForm()
    return render(request, "adminpanel/price_variable_form.html", {"form": form, "action": "Add"})

# 📌 Edit an Existing Price Variable
def edit_price_variable(request, price_variable_id):
    price_variable = get_object_or_404(PriceVariable, id=price_variable_id)
    if request.method == "POST":
        form = PriceVariableForm(request.POST, instance=price_variable)
        if form.is_valid():
            form.save()
            messages.success(request, "Price variable updated successfully!")
            return redirect("price_variable_list")
    else:
        form = PriceVariableForm(instance=price_variable)
    return render(request, "adminpanel/price_variable_form.html", {"form": form, "action": "Edit", "price_variable": price_variable})

# 📌 Delete a Price Variable
def delete_price_variable(request, price_variable_id):
    price_variable = get_object_or_404(PriceVariable, id=price_variable_id)
    if request.method == "POST":
        price_variable.delete()
        messages.success(request, "Price variable deleted successfully!")
        return redirect("price_variable_list")
    return render(request, "adminpanel/price_variable_confirm_delete.html", {"price_variable": price_variable})

# 📌 Tax Settings Management View
def tax_settings(request):
    # Get or create the singleton tax settings instance
    tax_settings_obj, created = TaxSettings.objects.get_or_create(pk=1, defaults={'tax_rate': 0.000})
    
    if request.method == "POST":
        form = TaxSettingsForm(request.POST, instance=tax_settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Tax settings updated successfully!")
            return redirect("tax_settings")
    else:
        form = TaxSettingsForm(instance=tax_settings_obj)
    
    return render(request, "adminpanel/tax_settings.html", {"form": form, "tax_settings": tax_settings_obj})

def format_time_slot(quote):
    start = datetime.combine(quote.date, quote.hour)
    # Convert Decimal to float for timedelta calculation
    hours = float(quote.hours_requested) if quote.hours_requested else 2.0
    duration = timedelta(hours=hours)
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
    
    # Debug: Print total bookings count
    total_bookings = Booking.objects.count()
    print(f"🔍 Total bookings in database: {total_bookings}")

    # 🟢 1. Add all Bookings (existing quotes)
    for quote in Booking.objects.all():
        try:
            # Convert Decimal to float for timedelta calculation
            hours = float(quote.hours_requested) if quote.hours_requested else 2.0
            duration = max(hours, 2.0)  # Minimum 2 hours
            start_time = datetime.combine(quote.date, quote.hour)
            end_time = start_time + timedelta(hours=duration)

            events.append({
                "id": f"booking-{quote.id}",
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
                    "type": "booking"
                }
            })
            print(f"✅ Added event for booking {quote.id}: {quote.name}")
        except Exception as e:
            print(f"❌ Error processing booking {quote.id}: {e}")
            continue

    # 🏠 2. Add Home Cleaning Quote Requests
    for quote in HomeCleaningQuoteRequest.objects.filter(date__isnull=False, hour__isnull=False):
        try:
            # Default to 2 hours if not specified
            hours = 2.0
            start_time = datetime.combine(quote.date, quote.hour)
            end_time = start_time + timedelta(hours=hours)

            # Determine color based on status
            status_colors = {
                "pending": "#ffc107",  # Yellow
                "email_sent": "#17a2b8",  # Cyan
                "accepted": "#6f42c1",  # Purple
                "completed": "#28a745",  # Green
                "declined": "#dc3545",  # Red
            }
            color = status_colors.get(quote.status, "#ffc107")

            events.append({
                "id": f"home-quote-{quote.id}",
                "title": f"🏠 {quote.name or 'Home Cleaning'} - Home Cleaning",
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "color": color,
                "extendedProps": {
                    "customer": quote.name or "N/A",
                    "zip_code": quote.zip_code or "N/A",
                    "email": quote.email or "N/A",
                    "phone": quote.phone or "N/A",
                    "service": "Home Cleaning",
                    "cleaning_type": quote.cleaning_type or "N/A",
                    "home_type": quote.home_types.name if quote.home_types else "N/A",
                    "bath_count": quote.bath_count or "N/A",
                    "job_description": quote.job_description or "N/A",
                    "time_slots": f"{quote.hour.strftime('%H:%M')} - {end_time.strftime('%H:%M')}",
                    "status": quote.status,
                    "type": "home_cleaning_quote"
                }
            })
            print(f"✅ Added event for home cleaning quote {quote.id}: {quote.name}")
        except Exception as e:
            print(f"❌ Error processing home cleaning quote {quote.id}: {e}")
            continue

    # 🏢 3. Add Office Cleaning Quote Requests
    for quote in OfficeQuote.objects.all():
        try:
            # Parse admin_notes JSON to get date and time
            if quote.admin_notes:
                try:
                    additional_data = json.loads(quote.admin_notes)
                    selected_date = additional_data.get('selected_date')
                    selected_time = additional_data.get('selected_time')
                    
                    if selected_date and selected_time:
                        # Parse date and time
                        quote_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
                        quote_time = datetime.strptime(selected_time, '%H:%M').time()
                        
                        # Calculate duration from crew_size_hours if available
                        hours = 2.0  # Default
                        crew_size_hours = additional_data.get('crew_size_hours', '')
                        if crew_size_hours:
                            # Parse format like "1_cleaner_2_hours_500" or "2_cleaners_3_hours_2500"
                            parts = crew_size_hours.split('_')
                            for i, part in enumerate(parts):
                                if part in ['hours', 'hour'] and i > 0:
                                    try:
                                        hours = float(parts[i-1])
                                        break
                                    except ValueError:
                                        pass
                        
                        start_time = datetime.combine(quote_date, quote_time)
                        end_time = start_time + timedelta(hours=hours)

                        # Determine color based on status
                        status_colors = {
                            "pending": "#ffc107",  # Yellow
                            "email_sent": "#17a2b8",  # Cyan
                            "accepted": "#6f42c1",  # Purple
                            "completed": "#28a745",  # Green
                            "declined": "#dc3545",  # Red
                        }
                        color = status_colors.get(quote.status, "#ffc107")

                        events.append({
                            "id": f"office-quote-{quote.id}",
                            "title": f"🏢 {quote.name} - Office Cleaning",
                            "start": start_time.isoformat(),
                            "end": end_time.isoformat(),
                            "color": color,
                            "extendedProps": {
                                "customer": quote.name or "N/A",
                                "email": quote.email or "N/A",
                                "phone": quote.phone_number or "N/A",
                                "service": "Office Cleaning",
                                "business_type": additional_data.get('business_type', 'N/A'),
                                "crew_size_hours": crew_size_hours or "N/A",
                                "square_footage": quote.square_footage or "N/A",
                                "job_description": quote.job_description or "N/A",
                                "time_slots": f"{quote_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}",
                                "status": quote.status,
                                "type": "office_cleaning_quote"
                            }
                        })
                        print(f"✅ Added event for office cleaning quote {quote.id}: {quote.name}")
                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    print(f"⚠️ Could not parse admin_notes for office quote {quote.id}: {e}")
                    continue
        except Exception as e:
            print(f"❌ Error processing office cleaning quote {quote.id}: {e}")
            continue

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

    # Debug: Print total events being returned
    print(f"🔍 Total events being returned: {len(events)}")
    for i, event in enumerate(events[:3]):  # Print first 3 events
        print(f"Event {i+1}: {event.get('title', 'No title')} - {event.get('start', 'No start')}")
    
    return JsonResponse(events, safe=False)



def get_event_details(request):
    quote_id = request.GET.get("event_id")
    try:
        quote = Booking.objects.select_related("customer", "service").get(pk=quote_id)
    except Booking.DoesNotExist:
        return JsonResponse({"error": "Quote not found"}, status=404)

    # Format time slot
    start = datetime.combine(quote.date, quote.hour)
    # Convert Decimal to float for timedelta calculation
    hours = float(quote.hours_requested) if quote.hours_requested else 2.0
    end = (start + timedelta(hours=hours)).time()
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
    # Convert Decimal to float for timedelta calculation
    hours = float(quote.hours_requested) if quote.hours_requested else 2.0
    duration = timedelta(hours=hours)
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
        from_email = "support@thecleanhandy.com"
        to_email = ["support@thecleanhandy.com"]
        bcc = ["support@thecleanhandy.com"]

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
    from django.conf import settings
    from_email = settings.DEFAULT_FROM_EMAIL
    recipients = [quote.email, "support@thecleanhandy.com"]

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
            from django.conf import settings
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[office_quote.email],
                bcc=["support@thecleanhandy.com"]  # Admin copy
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
            from django.conf import settings
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[handyman_quote.email],
                bcc=["support@thecleanhandy.com"]  # Admin copy
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
        
        from django.conf import settings
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
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


@login_required
@require_POST
@csrf_exempt
def send_payment_link(request):
    """Send payment link email to customer"""
    try:
        data = json.loads(request.body)
        booking_id = data.get('booking_id')
        payment_type = data.get('payment_type')  # 'final' or 'full'
        
        if not booking_id or not payment_type:
            return JsonResponse({'success': False, 'error': 'Missing booking_id or payment_type'}, status=400)
        
        # Get the booking
        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Booking not found'}, status=404)
        
        # Check if booking has payment split
        try:
            split = booking.get_payment_split()
        except:
            return JsonResponse({'success': False, 'error': 'No payment split found for this booking'}, status=400)
        
        payment_link_url = None
        email_sent = False
        
        if payment_type == 'final':
            # Send final payment link (50%)
            if not split.deposit_paid:
                return JsonResponse({'success': False, 'error': 'Deposit must be paid before sending final payment link'}, status=400)
            
            if split.final_paid:
                return JsonResponse({'success': False, 'error': 'Final payment already completed'}, status=400)
            
            # Create or get existing payment link
            payment_link_result = create_final_payment_link(booking)
            if payment_link_result and payment_link_result.get('payment_link_url'):
                payment_link_url = payment_link_result['payment_link_url']
                email_sent = send_final_payment_email(booking, payment_link_url)
            else:
                return JsonResponse({'success': False, 'error': 'Failed to create payment link'}, status=500)
                
        elif payment_type == 'full':
            # Send full payment link (100%)
            if split.deposit_paid or split.final_paid:
                return JsonResponse({'success': False, 'error': 'Partial payments already made. Cannot send full payment link.'}, status=400)
            
            # Create full payment link
            payment_link_result = create_full_payment_link(booking)
            if payment_link_result and payment_link_result.get('payment_link_url'):
                payment_link_url = payment_link_result['payment_link_url']
                email_sent = send_full_payment_email(booking, payment_link_url)
            else:
                return JsonResponse({'success': False, 'error': 'Failed to create payment link'}, status=500)
        else:
            return JsonResponse({'success': False, 'error': 'Invalid payment type'}, status=400)
        
        if email_sent:
            message = f'Payment link sent successfully to {booking.email}'
            if payment_type == 'final':
                message += ' (Final 50% payment)'
            else:
                message += ' (Full 100% payment)'
            
            return JsonResponse({
                'success': True, 
                'message': message,
                'payment_link_url': payment_link_url
            })
        else:
            return JsonResponse({'success': False, 'error': 'Payment link created but email failed to send'}, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'}, status=500)


# Home Cleaning Quotes Management
@login_required
@user_passes_test(admin_check)
def home_cleaning_quote_list(request):
    """List all home cleaning quotes with filtering and search"""
    home_cleaning_quotes = HomeCleaningQuoteRequest.objects.all().order_by('-created_at')

    # Filter by cleaning type
    cleaning_type_filter = request.GET.get('cleaning_type', '')
    if cleaning_type_filter:
        home_cleaning_quotes = home_cleaning_quotes.filter(cleaning_type=cleaning_type_filter)

    # Filter by frequency
    frequency_filter = request.GET.get('frequency', '')
    if frequency_filter:
        home_cleaning_quotes = home_cleaning_quotes.filter(cleaning_frequency=frequency_filter)

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        home_cleaning_quotes = home_cleaning_quotes.filter(
            models.Q(name__icontains=search_query) |
            models.Q(email__icontains=search_query) |
            models.Q(phone__icontains=search_query) |
            models.Q(address__icontains=search_query) |
            models.Q(job_description__icontains=search_query)
        )

    # Date range filter
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')

    if from_date:
        try:
            from datetime import datetime
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
            home_cleaning_quotes = home_cleaning_quotes.filter(created_at__date__gte=from_date_obj)
        except (ValueError, TypeError):
            pass
    
    if to_date:
        try:
            from datetime import datetime
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
            home_cleaning_quotes = home_cleaning_quotes.filter(created_at__date__lte=to_date_obj)
        except (ValueError, TypeError):
            pass

    # Cleaning type choices for filter dropdown
    cleaning_type_choices = [
        ('Regular Cleaning', 'Regular Cleaning'),
        ('Deep Cleaning', 'Deep Cleaning'),
        ('Move In/Out Cleaning', 'Move In/Out Cleaning'),
        ('Post Renovation', 'Post Renovation'),
    ]

    # Frequency choices
    frequency_choices = [
        ('one_time', 'One Time'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('bi_weekly', 'Bi Weekly'),
        ('monthly', 'Monthly'),
    ]

    # Convert queryset to list to ensure it's evaluated (for debugging and to ensure filters work)
    # Actually, Django templates handle querysets fine, so we'll keep it as queryset for efficiency
    
    context = {
        'home_cleaning_quotes': home_cleaning_quotes,
        'cleaning_type_choices': cleaning_type_choices,
        'frequency_choices': frequency_choices,
        'selected_cleaning_type': cleaning_type_filter,
        'selected_frequency': frequency_filter,
        'search_query': search_query,
        'from_date': from_date,
        'to_date': to_date,
    }

    return render(request, 'adminpanel/home_cleaning_quote_list.html', context)


@login_required
@user_passes_test(admin_check)
def home_cleaning_quote_detail(request, quote_id):
    """View home cleaning quote details"""
    from decimal import Decimal
    from quotes.utils import get_hourly_rate
    
    home_cleaning_quote = get_object_or_404(HomeCleaningQuoteRequest, pk=quote_id)

    if request.method == "POST":
        # Check if this is an email form submission
        if request.POST.get("email_action") == "send_quote_email":
            return send_home_cleaning_quote_email(request, quote_id)
        
        # Update status if provided
        new_status = request.POST.get("status")
        if new_status:
            home_cleaning_quote.status = new_status
            home_cleaning_quote.save(update_fields=['status'])
            messages.success(request, "Status updated successfully!")
            return redirect("home_cleaning_quote_detail", quote_id=quote_id)

    # Parse email history from admin_notes if it exists
    email_sent_at = None
    email_sent_to = None
    email_history = []
    if hasattr(home_cleaning_quote, 'admin_notes') and home_cleaning_quote.admin_notes:
        try:
            notes_data = json.loads(home_cleaning_quote.admin_notes)
            if isinstance(notes_data, dict):
                # Get latest email sent time
                if 'quote_email_sent_at' in notes_data:
                    from django.utils.dateparse import parse_datetime
                    email_sent_at = parse_datetime(notes_data['quote_email_sent_at'])
                    email_sent_to = notes_data.get('customer_email')
                
                # Get email history log
                if 'email_history' in notes_data and isinstance(notes_data['email_history'], list):
                    from django.utils.dateparse import parse_datetime
                    for entry in notes_data['email_history']:
                        if isinstance(entry, dict) and 'sent_at' in entry:
                            parsed_time = parse_datetime(entry['sent_at'])
                            if parsed_time:
                                email_history.append({
                                    'sent_at': parsed_time,
                                    'customer_email': entry.get('customer_email', ''),
                                    'price': entry.get('price'),
                                    'discount': entry.get('discount'),
                                    'discount_type': entry.get('discount_type'),
                                })
                    # Sort by most recent first
                    email_history.sort(key=lambda x: x['sent_at'], reverse=True)
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
    
    # Also check if quote_email_sent_at field exists (for backward compatibility)
    if not email_sent_at and hasattr(home_cleaning_quote, 'quote_email_sent_at') and home_cleaning_quote.quote_email_sent_at:
        email_sent_at = home_cleaning_quote.quote_email_sent_at
        if not email_history:
            email_history.append({
                'sent_at': email_sent_at,
                'customer_email': home_cleaning_quote.email,
                'price': None,
                'discount': None,
                'discount_type': None,
            })
    
    # Calculate estimated time, price, and parking fee based on selected PriceVariables
    calculated_estimated_time = ""
    calculated_price = None
    calculated_parking_fee = None
    selected_variables = []
    
    # Check admin_notes for stored PriceVariable IDs (similar to office quotes)
    form_data = {}
    if hasattr(home_cleaning_quote, 'admin_notes') and home_cleaning_quote.admin_notes:
        try:
            notes_data = json.loads(home_cleaning_quote.admin_notes)
            if isinstance(notes_data, dict):
                form_data = notes_data
        except (json.JSONDecodeError, ValueError):
            pass
    
    # Get PriceVariable IDs from form_data (stored in admin_notes) or direct fields
    home_type_id = form_data.get('home_type_id') or form_data.get('home_types_id')
    bath_count_id = form_data.get('bath_count_id')
    cleaning_type_name = home_cleaning_quote.cleaning_type
    parking_option_id = form_data.get('parking_option_id') or form_data.get('parking_option')
    
    # Fallback: Check bath_count field directly - could be PriceVariable ID (numeric string) or old format
    if not bath_count_id and home_cleaning_quote.bath_count:
        try:
            bath_count_id = int(home_cleaning_quote.bath_count)
        except (ValueError, TypeError):
            # Old format string or not a number, skip PriceVariable lookup
            pass
    
    # Also try to get home_type_id from form_data if home_types field is numeric
    if not home_type_id and form_data.get('home_types'):
        try:
            home_type_id = int(form_data['home_types'])
        except (ValueError, TypeError):
            pass
    
    # Look up PriceVariables
    if home_type_id:
        try:
            home_type_var = PriceVariable.objects.get(id=home_type_id, is_active=True)
            selected_variables.append(home_type_var)
        except PriceVariable.DoesNotExist:
            pass
    
    if bath_count_id:
        try:
            bath_var = PriceVariable.objects.get(id=bath_count_id, is_active=True)
            selected_variables.append(bath_var)
        except PriceVariable.DoesNotExist:
            pass
    
    if cleaning_type_name:
        try:
            cleaning_type_var = PriceVariable.objects.filter(
                variable_name=cleaning_type_name, 
                category__name__iexact="Cleaning Type",
                is_active=True
            ).first()
            if cleaning_type_var:
                selected_variables.append(cleaning_type_var)
        except Exception:
            pass
    
    if parking_option_id:
        try:
            parking_var = PriceVariable.objects.get(id=parking_option_id, is_active=True)
            calculated_parking_fee = float(parking_var.price) if parking_var.price else None
        except (PriceVariable.DoesNotExist, ValueError, TypeError):
            pass
    
    # Calculate total duration and price from selected variables
    if selected_variables:
        total_duration_minutes = sum(var.duration for var in selected_variables if var.duration)
        total_price = sum(float(var.price) for var in selected_variables if var.price)
        
        # Convert duration to hours for display
        if total_duration_minutes:
            if total_duration_minutes >= 60:
                hours = total_duration_minutes / 60.0
                # Format nicely: show whole number if it's a whole number, otherwise 1 decimal place
                if hours == int(hours):
                    calculated_estimated_time = f"{int(hours)} hour{'s' if int(hours) != 1 else ''}"
                else:
                    calculated_estimated_time = f"{hours:.1f} hours"
            else:
                calculated_estimated_time = f"{total_duration_minutes} minute{'s' if total_duration_minutes != 1 else ''}"
        
        # Calculate price - use sum of prices if available, otherwise calculate from hourly rate
        if total_price > 0:
            calculated_price = total_price
        elif total_duration_minutes:
            # Calculate from hourly rate
            try:
                hourly_rate = get_hourly_rate('home_cleaning')
                if hourly_rate:
                    duration_hours = Decimal(total_duration_minutes) / Decimal('60')
                    calculated_price = float(hourly_rate * duration_hours)
            except Exception as e:
                print(f"Error calculating price from hourly rate: {e}")
    
    # Add cleaning supply price if cleaning_supply is "yes"
    if home_cleaning_quote.cleaning_supply and home_cleaning_quote.cleaning_supply.lower() == 'yes':
        try:
            # Find PriceVariable where category is "Extras" and variable_name contains "Cleaning Supply"
            extras_category = PriceVariableCategory.objects.filter(name__iexact="Extras", is_active=True).first()
            if extras_category:
                cleaning_supply_var = PriceVariable.objects.filter(
                    category=extras_category,
                    variable_name__icontains="Cleaning Supply",
                    is_active=True
                ).first()
                if cleaning_supply_var and cleaning_supply_var.price:
                    cleaning_supply_price = float(cleaning_supply_var.price)
                    if calculated_price:
                        calculated_price += cleaning_supply_price
                    else:
                        calculated_price = cleaning_supply_price
        except Exception as e:
            print(f"Error adding cleaning supply price: {e}")
    
    # Calculate discount based on cleaning_frequency
    calculated_discount = None
    cleaning_frequency = home_cleaning_quote.cleaning_frequency or form_data.get('cleaning_frequency', 'one_time')
    if calculated_price and cleaning_frequency:
        try:
            if cleaning_frequency == 'weekly':
                # 10% discount for weekly
                calculated_discount = float(Decimal(str(calculated_price)) * Decimal('0.10'))
            elif cleaning_frequency == 'bi_weekly':
                # 5% discount for bi-weekly
                calculated_discount = float(Decimal(str(calculated_price)) * Decimal('0.05'))
            else:
                # No discount for one_time or monthly
                calculated_discount = 0.0
        except (ValueError, TypeError, Exception) as e:
            print(f"Error calculating discount: {e}")
            calculated_discount = None
    
    # Get home type variable name for display (instead of using the old ForeignKey)
    home_type_display_name = None
    if home_type_id:
        try:
            home_type_var = PriceVariable.objects.filter(id=home_type_id, is_active=True).first()
            if home_type_var:
                home_type_display_name = home_type_var.variable_name
        except Exception:
            pass
    
    # Get bathroom variable name for display (instead of just the ID)
    bathroom_display_name = None
    if bath_count_id:
        try:
            bath_var = PriceVariable.objects.filter(id=bath_count_id, is_active=True).first()
            if bath_var:
                bathroom_display_name = bath_var.variable_name
        except Exception:
            pass
    
    # Fallback: if bath_count is stored as a string that's not a valid ID, try to use it as-is
    if not bathroom_display_name and home_cleaning_quote.bath_count:
        # If it's not a number (PriceVariable ID), use it as display name
        try:
            int(home_cleaning_quote.bath_count)
            # It's a number, so we already tried to look it up above
        except (ValueError, TypeError):
            # It's not a number, use as display name (for backward compatibility)
            bathroom_display_name = home_cleaning_quote.bath_count
    
    return render(request, "adminpanel/home_cleaning_quote_detail.html", {
        "home_cleaning_quote": home_cleaning_quote,
        "email_sent_at": email_sent_at,
        "email_sent_to": email_sent_to or home_cleaning_quote.email,
        "email_history": email_history,
        "calculated_estimated_time": calculated_estimated_time,
        "calculated_price": calculated_price,
        "calculated_parking_fee": calculated_parking_fee,
        "calculated_discount": calculated_discount,
        "home_type_display_name": home_type_display_name,
        "bathroom_display_name": bathroom_display_name,
    })


@login_required
@require_POST
def delete_home_cleaning_quote(request, quote_id):
    """Delete a home cleaning quote"""
    quote = get_object_or_404(HomeCleaningQuoteRequest, id=quote_id)
    quote.delete()
    messages.success(request, "Home cleaning quote deleted successfully.")
    return redirect("home_cleaning_quote_list")


def home_cleaning_quote_accept(request, quote_id, token):
    """Handle quote acceptance from email link"""
    from django.core.signing import Signer, BadSignature
    from django.http import HttpResponse, HttpResponseForbidden
    from urllib.parse import unquote
    
    home_cleaning_quote = get_object_or_404(HomeCleaningQuoteRequest, pk=quote_id)
    
    # Decode the token in case it was URL-encoded (handle double encoding)
    token = unquote(token)
    # Handle double encoding (if token contains %3A instead of :)
    if '%' in token:
        token = unquote(token)
    
    # Verify token
    signer = Signer()
    try:
        signed_value = signer.unsign(token)
        if str(home_cleaning_quote.id) != signed_value:
            return HttpResponseForbidden("Invalid token")
    except BadSignature:
        return HttpResponseForbidden("Invalid token")
    
    # Update status to accepted
    status_changed = False
    if home_cleaning_quote.status != "accepted":
        home_cleaning_quote.status = "accepted"
        home_cleaning_quote.save(update_fields=['status'])
        status_changed = True
    
    # Send admin notification email if status was changed
    if status_changed:
        try:
            from django.core.mail import EmailMultiAlternatives
            from django.template.loader import render_to_string
            from django.utils.html import strip_tags
            from django.conf import settings
            
            # Prepare email context
            admin_context = {
                "quote": home_cleaning_quote,
                "action": "accepted",
                "customer_name": home_cleaning_quote.name or "Customer",
                "quote_id": home_cleaning_quote.id,
            }
            
            # Render email template
            html_content = render_to_string("adminpanel/emails/home_cleaning_quote_status_notification.html", admin_context)
            text_content = strip_tags(html_content)
            
            # Send email to admin
            subject = f"✅ Quote #{home_cleaning_quote.id} Accepted by Customer"
            admin_email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=["support@thecleanhandy.com"],
            )
            admin_email.attach_alternative(html_content, "text/html")
            admin_email.send()
        except Exception as e:
            print(f"Warning: Could not send admin notification email: {e}")
    
    # Render success page
    return render(request, "adminpanel/home_cleaning_quote_response.html", {
        "quote": home_cleaning_quote,
        "action": "accepted",
        "message": "Thank you! Your quote has been accepted. We will contact you shortly to confirm the details."
    })


def home_cleaning_quote_decline(request, quote_id, token):
    """Handle quote decline from email link"""
    from django.core.signing import Signer, BadSignature
    from django.http import HttpResponseForbidden
    from urllib.parse import unquote
    
    home_cleaning_quote = get_object_or_404(HomeCleaningQuoteRequest, pk=quote_id)
    
    # Decode the token in case it was URL-encoded (handle double encoding)
    token = unquote(token)
    # Handle double encoding (if token contains %3A instead of :)
    if '%' in token:
        token = unquote(token)
    
    # Verify token
    signer = Signer()
    try:
        signed_value = signer.unsign(token)
        expected_value = f"decline_{home_cleaning_quote.id}"
        if expected_value != signed_value:
            return HttpResponseForbidden("Invalid token")
    except BadSignature:
        return HttpResponseForbidden("Invalid token")
    
    # Update status to declined
    status_changed = False
    if home_cleaning_quote.status != "declined":
        home_cleaning_quote.status = "declined"
        home_cleaning_quote.save(update_fields=['status'])
        status_changed = True
    
    # Send admin notification email if status was changed
    if status_changed:
        try:
            from django.core.mail import EmailMultiAlternatives
            from django.template.loader import render_to_string
            from django.utils.html import strip_tags
            from django.conf import settings
            
            # Prepare email context
            admin_context = {
                "quote": home_cleaning_quote,
                "action": "declined",
                "customer_name": home_cleaning_quote.name or "Customer",
                "quote_id": home_cleaning_quote.id,
            }
            
            # Render email template
            html_content = render_to_string("adminpanel/emails/home_cleaning_quote_status_notification.html", admin_context)
            text_content = strip_tags(html_content)
            
            # Send email to admin
            subject = f"❌ Quote #{home_cleaning_quote.id} Declined by Customer"
            admin_email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=["support@thecleanhandy.com"],
            )
            admin_email.attach_alternative(html_content, "text/html")
            admin_email.send()
        except Exception as e:
            print(f"Warning: Could not send admin notification email: {e}")
    
    # Render success page
    return render(request, "adminpanel/home_cleaning_quote_response.html", {
        "quote": home_cleaning_quote,
        "action": "declined",
        "message": "We're sorry to see you decline this offer. If you change your mind or have any questions, please don't hesitate to contact us."
    })


@login_required
@user_passes_test(admin_check)
def office_cleaning_quote_list(request):
    """List all office cleaning quotes with filtering and search"""
    office_cleaning_quotes = OfficeQuote.objects.all().order_by('-created_at')

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        office_cleaning_quotes = office_cleaning_quotes.filter(
            models.Q(name__icontains=search_query) |
            models.Q(email__icontains=search_query) |
            models.Q(phone_number__icontains=search_query) |
            models.Q(business_address__icontains=search_query) |
            models.Q(job_description__icontains=search_query)
        )

    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        office_cleaning_quotes = office_cleaning_quotes.filter(status=status_filter)

    # Date range filter
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')

    if from_date:
        try:
            from datetime import datetime
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
            office_cleaning_quotes = office_cleaning_quotes.filter(created_at__date__gte=from_date_obj)
        except (ValueError, TypeError):
            pass
    
    if to_date:
        try:
            from datetime import datetime
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
            office_cleaning_quotes = office_cleaning_quotes.filter(created_at__date__lte=to_date_obj)
        except (ValueError, TypeError):
            pass

    # Status choices for filter dropdown
    status_choices = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('quoted', 'Quoted'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]
    
    # Extract square footage from admin_notes (form_data) for each quote
    import json
    import re
    from quotes.models import PriceVariable
    
    for quote in office_cleaning_quotes:
        square_footage_display = None
        if quote.admin_notes:
            try:
                form_data = json.loads(quote.admin_notes)
                if isinstance(form_data, dict):
                    # First check if crew_size_hours_display already exists in form_data
                    crew_size_hours_display = form_data.get('crew_size_hours_display', '')
                    
                    # If not, try to get it from PriceVariable if crew_size_hours is an ID
                    if not crew_size_hours_display:
                        crew_size_hours_value = form_data.get('crew_size_hours', '')
                        if crew_size_hours_value:
                            try:
                                price_variable_id = int(crew_size_hours_value)
                                try:
                                    price_var = PriceVariable.objects.get(id=price_variable_id, is_active=True)
                                    crew_size_hours_display = price_var.variable_name
                                except PriceVariable.DoesNotExist:
                                    pass
                            except (ValueError, TypeError):
                                pass
                    
                    # Extract square footage from crew_size_hours_display
                    if crew_size_hours_display:
                        square_footage_match = re.search(r'\(([^)]*[Ss]q[.\s]*[Ff]t[^)]*)\)', crew_size_hours_display)
                        if square_footage_match:
                            square_footage_display = square_footage_match.group(1).strip()
                    
                    # If still not found, check if square_footage is directly in form_data
                    if not square_footage_display and form_data.get('square_footage'):
                        square_footage_display = form_data['square_footage']
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
        
        # Attach the extracted square footage to the quote object
        quote.display_square_footage = square_footage_display if square_footage_display else quote.square_footage
    
    context = {
        'office_cleaning_quotes': office_cleaning_quotes,
        'status_choices': status_choices,
        'selected_status': status_filter,
        'search_query': search_query,
        'from_date': from_date,
        'to_date': to_date,
    }

    return render(request, 'adminpanel/office_cleaning_quote_list.html', context)


@login_required
@user_passes_test(admin_check)
def office_cleaning_quote_detail(request, quote_id):
    """View office cleaning quote details"""
    import json
    from datetime import datetime
    
    office_cleaning_quote = get_object_or_404(OfficeQuote, pk=quote_id)

    if request.method == "POST":
        # Check if this is an email form submission
        if request.POST.get("email_action") == "send_quote_email":
            return send_office_cleaning_quote_email(request, quote_id)
        
        # Update status if provided
        new_status = request.POST.get("status")
        if new_status:
            office_cleaning_quote.status = new_status
        
        # Update admin notes if provided (preserve JSON form data if it exists)
        admin_notes = request.POST.get("admin_notes")
        if admin_notes is not None:
            # Check if current admin_notes is JSON (form data)
            current_notes = office_cleaning_quote.admin_notes or ""
            try:
                existing_form_data = json.loads(current_notes)
                if isinstance(existing_form_data, dict):
                    # Preserve form data and add admin notes separately
                    # Store admin notes in a separate field or append to JSON
                    existing_form_data['admin_notes_text'] = admin_notes
                    office_cleaning_quote.admin_notes = json.dumps(existing_form_data, indent=2)
                else:
                    office_cleaning_quote.admin_notes = admin_notes
            except (json.JSONDecodeError, ValueError):
                # Current notes are not JSON, replace with new notes
                office_cleaning_quote.admin_notes = admin_notes
        
        office_cleaning_quote.save()
        messages.success(request, "Quote updated successfully!")
        return redirect("office_cleaning_quote_list")

    # Parse additional form data from admin_notes if it's JSON
    form_data = {}
    if office_cleaning_quote.admin_notes:
        try:
            form_data = json.loads(office_cleaning_quote.admin_notes)
            # If it's not JSON, treat it as regular admin notes
            if not isinstance(form_data, dict):
                form_data = {}
        except (json.JSONDecodeError, ValueError):
            # admin_notes contains regular text, not JSON
            form_data = {}
    
    # Import ContactInfo from the correct location
    try:
        from quotes.models import ContactInfo
    except ImportError:
        ContactInfo = None
    
    # Format string values for display (replace underscores with spaces, title case)
    if isinstance(form_data, dict):
        # Format business_type
        if form_data.get('business_type'):
            form_data['business_type_display'] = form_data['business_type'].replace('_', ' ').title()
        
        # Format crew_size_hours - check if it's a PriceVariable ID (numeric) or old string format
        crew_size_hours_value = form_data.get('crew_size_hours', '')
        if crew_size_hours_value:
            # Check if it's a numeric ID (new format with PriceVariable)
            try:
                price_variable_id = int(crew_size_hours_value)
                # Try to get the PriceVariable
                try:
                    price_var = PriceVariable.objects.get(id=price_variable_id, is_active=True)
                    form_data['crew_size_hours_display'] = price_var.variable_name
                    form_data['price_variable'] = price_var
                    # Store price variable data for template
                    form_data['selected_price_variable'] = {
                        'id': price_var.id,
                        'name': price_var.variable_name,
                        'price': float(price_var.price) if price_var.price else None,
                        'duration_minutes': price_var.duration if price_var.duration else None,
                    }
                    # Extract square footage from PriceVariable name if it contains parentheses
                    # Example: "1 Cleaner Total 2 Hours (<500 Sq Ft)" -> "<500 Sq Ft"
                    import re
                    square_footage_match = re.search(r'\(([^)]*[Ss]q[.\s]*[Ff]t[^)]*)\)', price_var.variable_name)
                    if square_footage_match:
                        extracted_sqft = square_footage_match.group(1).strip()
                        form_data['square_footage_display'] = extracted_sqft
                except PriceVariable.DoesNotExist:
                    # Fall back to old string format display
                    crew_display = str(crew_size_hours_value).replace('_', ' ')
                    crew_display = crew_display.replace('cleaner', 'Cleaner').replace('cleaners', 'Cleaners')
                    crew_display = crew_display.replace('hours', 'Hours').replace('hour', 'Hour')
                    crew_display = crew_display.replace('sq ft', 'Sq Ft').replace('sqft', 'Sq Ft')
                    form_data['crew_size_hours_display'] = crew_display
            except (ValueError, TypeError):
                # Old string format
                crew_display = str(crew_size_hours_value).replace('_', ' ')
                crew_display = crew_display.replace('cleaner', 'Cleaner').replace('cleaners', 'Cleaners')
                crew_display = crew_display.replace('hours', 'Hours').replace('hour', 'Hour')
                crew_display = crew_display.replace('sq ft', 'Sq Ft').replace('sqft', 'Sq Ft')
                form_data['crew_size_hours_display'] = crew_display
        
        # Extract square footage from crew_size_hours_display if it contains parentheses
        # Example: "1 Cleaner Total 2 Hours (<500 Sq Ft)" -> "<500 Sq Ft"
        # Only extract if square_footage_display wasn't already set from PriceVariable above
        if 'square_footage_display' not in form_data and form_data.get('crew_size_hours_display'):
            import re
            crew_display_text = form_data['crew_size_hours_display']
            # Extract content within parentheses that contains "Sq Ft" or similar
            square_footage_match = re.search(r'\(([^)]*[Ss]q[.\s]*[Ff]t[^)]*)\)', crew_display_text)
            if square_footage_match:
                extracted_sqft = square_footage_match.group(1).strip()
                form_data['square_footage_display'] = extracted_sqft
        
        # Format hear_about_us
        if form_data.get('hear_about_us'):
            form_data['hear_about_us_display'] = form_data['hear_about_us'].replace('_', ' ').title()
        
        # Format cleaning_frequency
        if form_data.get('cleaning_frequency'):
            freq = form_data['cleaning_frequency']
            if freq == 'one_time':
                form_data['cleaning_frequency_display'] = 'One Time'
            elif freq == 'weekly':
                form_data['cleaning_frequency_display'] = 'Weekly - 10% Off'
            elif freq == 'bi_weekly':
                form_data['cleaning_frequency_display'] = 'Bi Weekly - 5% Off'
            elif freq == 'monthly':
                form_data['cleaning_frequency_display'] = 'Monthly'
            else:
                form_data['cleaning_frequency_display'] = freq.replace('_', ' ').title()
        
        # Format recurrence_pattern
        if form_data.get('recurrence_pattern'):
            form_data['recurrence_pattern_display'] = form_data['recurrence_pattern'].replace('_', ' ').title()
    
    # Parse dates and times if they exist
    if form_data.get('selected_date'):
        try:
            if isinstance(form_data['selected_date'], str):
                form_data['selected_date'] = datetime.strptime(form_data['selected_date'], '%Y-%m-%d').date()
        except (ValueError, TypeError):
            pass
    
    if form_data.get('selected_time'):
        try:
            if isinstance(form_data['selected_time'], str):
                if ':' in str(form_data['selected_time']):
                    hour, minute = map(int, str(form_data['selected_time']).split(':'))
                    from datetime import time
                    form_data['selected_time'] = time(hour, minute)
        except (ValueError, TypeError):
            pass

    # Parse email history from admin_notes if it exists
    email_sent_at = None
    email_sent_to = None
    email_history = []
    if office_cleaning_quote.admin_notes:
        try:
            notes_data = json.loads(office_cleaning_quote.admin_notes)
            if isinstance(notes_data, dict):
                # Get latest email sent time
                if 'quote_email_sent_at' in notes_data:
                    from django.utils.dateparse import parse_datetime
                    email_sent_at = parse_datetime(notes_data['quote_email_sent_at'])
                    email_sent_to = notes_data.get('customer_email')
                
                # Get email history log
                if 'email_history' in notes_data and isinstance(notes_data['email_history'], list):
                    from django.utils.dateparse import parse_datetime
                    for entry in notes_data['email_history']:
                        if isinstance(entry, dict) and 'sent_at' in entry:
                            parsed_time = parse_datetime(entry['sent_at'])
                            if parsed_time:
                                email_history.append({
                                    'sent_at': parsed_time,
                                    'customer_email': entry.get('customer_email', ''),
                                    'price': entry.get('price'),
                                    'discount': entry.get('discount'),
                                    'discount_type': entry.get('discount_type'),
                                })
                    # Sort by most recent first
                    email_history.sort(key=lambda x: x['sent_at'], reverse=True)
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
    
    # Calculate estimated time and price based on selected PriceVariable
    calculated_estimated_time = ""
    calculated_price = None
    price_source = None  # Track if price came from variable or hourly rate
    calculated_discount = None
    
    if form_data.get('selected_price_variable'):
        price_var_data = form_data['selected_price_variable']
        
        # Calculate estimated time from duration (convert minutes to hours)
        if price_var_data.get('duration_minutes'):
            duration_minutes = price_var_data['duration_minutes']
            if duration_minutes >= 60:
                hours = duration_minutes // 60
                minutes = duration_minutes % 60
                if minutes > 0:
                    # Convert to decimal hours (e.g., 120 min = 2.0 hours, 150 min = 2.5 hours)
                    decimal_hours = round(duration_minutes / 60.0, 1)
                    calculated_estimated_time = f"{decimal_hours} hours"
                else:
                    calculated_estimated_time = f"{hours} hour{'s' if hours != 1 else ''}"
            else:
                calculated_estimated_time = f"{duration_minutes} minute{'s' if duration_minutes != 1 else ''}"
        
        # Calculate price: use PriceVariable price if available, otherwise calculate from hourly rate
        if price_var_data.get('price'):
            calculated_price = price_var_data['price']
            price_source = 'variable'
        else:
            # Calculate from hourly rate and duration
            try:
                from quotes.utils import get_hourly_rate
                from decimal import Decimal
                hourly_rate = get_hourly_rate('office_cleaning')
                if hourly_rate and price_var_data.get('duration_minutes'):
                    duration_hours = Decimal(price_var_data['duration_minutes']) / Decimal('60')
                    calculated_price = float(hourly_rate * duration_hours)
                    price_source = 'hourly_rate'
            except Exception as e:
                print(f"Error calculating price from hourly rate: {e}")
    
    # Calculate discount based on cleaning frequency
    cleaning_frequency = form_data.get('cleaning_frequency', 'one_time')
    if calculated_price and cleaning_frequency:
        try:
            from decimal import Decimal
            if cleaning_frequency == 'weekly':
                # 10% discount for weekly
                calculated_discount = float(Decimal(str(calculated_price)) * Decimal('0.10'))
            elif cleaning_frequency == 'bi_weekly':
                # 5% discount for bi-weekly
                calculated_discount = float(Decimal(str(calculated_price)) * Decimal('0.05'))
            else:
                # No discount for one_time or monthly
                calculated_discount = 0.0
        except (ValueError, TypeError) as e:
            print(f"Error calculating discount: {e}")
            calculated_discount = None
    
    return render(request, "adminpanel/office_cleaning_quote_detail.html", {
        "office_cleaning_quote": office_cleaning_quote,
        "form_data": form_data,
        "email_sent_at": email_sent_at,
        "email_sent_to": email_sent_to or office_cleaning_quote.email,
        "email_history": email_history,
        "calculated_estimated_time": calculated_estimated_time,
        "calculated_price": calculated_price,
        "price_source": price_source,
        "calculated_discount": calculated_discount,
    })


@login_required
@user_passes_test(admin_check)
def send_home_cleaning_quote_email(request, quote_id):
    """Send email to customer with quote details and admin-provided information"""
    from django.core.mail import EmailMultiAlternatives
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags
    from django.contrib.sites.shortcuts import get_current_site
    
    home_cleaning_quote = get_object_or_404(HomeCleaningQuoteRequest, pk=quote_id)
    
    if request.method == "POST":
        try:
            # Get form data
            estimated_time = request.POST.get("estimated_time", "")
            price = request.POST.get("price", "")
            parking_fee = request.POST.get("parking_fee", "")
            discount = request.POST.get("discount", "")
            discount_type = request.POST.get("discount_type", "value")
            payment_link = request.POST.get("payment_link", "")
            note = request.POST.get("note", "")
            
            # Get editable customer details
            customer_name = request.POST.get("customer_name", home_cleaning_quote.name)
            customer_email = request.POST.get("customer_email", home_cleaning_quote.email)
            customer_phone = request.POST.get("customer_phone", home_cleaning_quote.phone)
            service_date = request.POST.get("service_date", home_cleaning_quote.date.strftime("%Y-%m-%d") if home_cleaning_quote.date else "")
            service_time = request.POST.get("service_time", home_cleaning_quote.hour.strftime("%H:%M") if home_cleaning_quote.hour else "")
            address = request.POST.get("address", home_cleaning_quote.address)
            apartment = request.POST.get("apartment", home_cleaning_quote.apartment or "")
            city = request.POST.get("city", home_cleaning_quote.city or "")
            state = request.POST.get("state", home_cleaning_quote.state or "")
            zip_code = request.POST.get("zip_code", home_cleaning_quote.zip_code or "")
            cleaning_type = request.POST.get("cleaning_type", home_cleaning_quote.cleaning_type or "")
            cleaning_frequency = request.POST.get("cleaning_frequency", home_cleaning_quote.cleaning_frequency or "")
            job_description = request.POST.get("job_description", home_cleaning_quote.job_description or "")
            
            # Calculate total price
            from decimal import Decimal
            subtotal = Decimal("0.00")
            discount_amount = Decimal("0.00")
            discount_display = ""
            sales_tax_rate = Decimal("8.875")  # 8.875%
            sales_tax = Decimal("0.00")
            total_price = Decimal("0.00")
            
            try:
                if price:
                    price_decimal = Decimal(str(price))
                    subtotal += price_decimal
                if parking_fee:
                    subtotal += Decimal(str(parking_fee))
                
                # Calculate discount
                if discount:
                    discount_value = Decimal(str(discount))
                    if discount_type == "percentage":
                        # Calculate discount from subtotal
                        if subtotal > 0:
                            discount_amount = (subtotal * discount_value) / Decimal("100")
                            discount_display = f"{discount}%"
                        else:
                            discount_amount = Decimal("0.00")
                            discount_display = f"{discount}%"
                    else:
                        # Direct dollar amount
                        discount_amount = discount_value
                        discount_display = f"${discount}"
                    subtotal -= discount_amount
                
                # Calculate sales tax (8.875% of subtotal after discount)
                if subtotal > 0:
                    sales_tax = (subtotal * sales_tax_rate) / Decimal("100")
                
                # Calculate total (subtotal + sales tax)
                total_price = subtotal + sales_tax
            except (ValueError, TypeError):
                pass
            
            # Generate secure tokens for accept/decline actions
            from django.core.signing import Signer
            signer = Signer()
            accept_token = signer.sign(str(home_cleaning_quote.id))
            decline_token = signer.sign(f"decline_{home_cleaning_quote.id}")
            
            # Build accept/decline URLs (Django's reverse will handle URL encoding automatically)
            current_site = get_current_site(request)
            accept_url = f"{request.scheme}://{current_site.domain}{reverse('home_cleaning_quote_accept', args=[home_cleaning_quote.id, accept_token])}"
            decline_url = f"{request.scheme}://{current_site.domain}{reverse('home_cleaning_quote_decline', args=[home_cleaning_quote.id, decline_token])}"
            
            # Prepare email context
            context = {
                "quote": home_cleaning_quote,
                "customer_name": customer_name,
                "customer_email": customer_email,
                "customer_phone": customer_phone,
                "service_date": service_date,
                "service_time": service_time,
                "address": address,
                "apartment": apartment,
                "city": city,
                "state": state,
                "zip_code": zip_code,
                "cleaning_type": cleaning_type,
                "cleaning_frequency": cleaning_frequency,
                "job_description": job_description,
                "estimated_time": estimated_time,
                "price": price,
                "parking_fee": parking_fee,
                "discount": discount,
                "discount_type": discount_type,
                "discount_amount": discount_amount,
                "discount_display": discount_display,
                "subtotal": subtotal,
                "sales_tax_rate": sales_tax_rate,
                "sales_tax": sales_tax,
                "total_price": total_price,
                "payment_link": payment_link,
                "note": note,
                "request_scheme": request.scheme,
                "domain": get_current_site(request).domain,
                "accept_url": accept_url,
                "decline_url": decline_url,
            }
            
            # Render email template
            html_content = render_to_string("adminpanel/emails/home_cleaning_quote_email.html", context)
            text_content = strip_tags(html_content)
            
            # Send email
            subject = f"Your Home Cleaning Quote - #{home_cleaning_quote.id}"
            from django.conf import settings
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[customer_email],
                bcc=["support@thecleanhandy.com"]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            # Save email sending time and add to email history log
            from django.utils import timezone
            import json
            email_sent_time = timezone.now()
            
            # Store email history in admin_notes as JSON
            try:
                email_entry = {
                    'sent_at': email_sent_time.isoformat(),
                    'customer_email': customer_email,
                    'price': str(price) if price else None,
                    'discount': str(discount) if discount else None,
                    'discount_type': discount_type,
                    'parking_fee': str(parking_fee) if parking_fee else None,
                }
                
                # Try to preserve existing admin_notes if it's JSON
                existing_notes = {}
                if hasattr(home_cleaning_quote, 'admin_notes') and home_cleaning_quote.admin_notes:
                    try:
                        existing_notes = json.loads(home_cleaning_quote.admin_notes)
                        if not isinstance(existing_notes, dict):
                            existing_notes = {}
                    except:
                        existing_notes = {}
                
                # Initialize email_history array if it doesn't exist
                if 'email_history' not in existing_notes:
                    existing_notes['email_history'] = []
                
                # Add new email entry to history
                existing_notes['email_history'].append(email_entry)
                
                # Also keep latest email info for backward compatibility
                existing_notes['quote_email_sent_at'] = email_sent_time.isoformat()
                existing_notes['customer_email'] = customer_email
                
                # Save updated notes
                home_cleaning_quote.admin_notes = json.dumps(existing_notes, indent=2)
                # Update status to "email_sent" after sending email
                home_cleaning_quote.status = "email_sent"
                home_cleaning_quote.save(update_fields=['admin_notes', 'status'])
            except Exception as save_error:
                print(f"Warning: Could not save email history: {save_error}")
            
            messages.success(request, f"📧 Email sent successfully to {customer_email} on {email_sent_time.strftime('%B %d, %Y at %I:%M %p')}")
        except Exception as e:
            messages.error(request, f"❌ Failed to send email: {str(e)}")
    
    return redirect("home_cleaning_quote_detail", quote_id=quote_id)


@login_required
@user_passes_test(admin_check)
def send_office_cleaning_quote_email(request, quote_id):
    """Send email to customer with quote details and admin-provided information"""
    from django.core.mail import EmailMultiAlternatives
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags
    from django.contrib.sites.shortcuts import get_current_site
    import json
    
    office_cleaning_quote = get_object_or_404(OfficeQuote, pk=quote_id)
    
    if request.method == "POST":
        try:
            # Get form data
            estimated_time = request.POST.get("estimated_time", "")
            price = request.POST.get("price", "")
            parking_fee = request.POST.get("parking_fee", "")
            discount = request.POST.get("discount", "")
            discount_type = request.POST.get("discount_type", "value")
            payment_link = request.POST.get("payment_link", "")
            note = request.POST.get("note", "")
            
            # Get editable customer details
            customer_name = request.POST.get("customer_name", office_cleaning_quote.name)
            customer_email = request.POST.get("customer_email", office_cleaning_quote.email)
            customer_phone = request.POST.get("customer_phone", office_cleaning_quote.phone_number)
            business_address = request.POST.get("business_address", office_cleaning_quote.business_address)
            square_footage = request.POST.get("square_footage", office_cleaning_quote.square_footage)
            job_description = request.POST.get("job_description", office_cleaning_quote.job_description)
            
            # Parse form data for schedule info
            form_data = {}
            if office_cleaning_quote.admin_notes:
                try:
                    form_data = json.loads(office_cleaning_quote.admin_notes)
                    if not isinstance(form_data, dict):
                        form_data = {}
                except (json.JSONDecodeError, ValueError):
                    form_data = {}
            
            service_date = request.POST.get("service_date", form_data.get("selected_date", ""))
            service_time = request.POST.get("service_time", form_data.get("selected_time", ""))
            cleaning_frequency = request.POST.get("cleaning_frequency", form_data.get("cleaning_frequency", ""))
            business_type = request.POST.get("business_type", form_data.get("business_type", ""))
            crew_size_hours = request.POST.get("crew_size_hours", form_data.get("crew_size_hours", ""))
            
            # Calculate total price
            from decimal import Decimal
            subtotal = Decimal("0.00")
            discount_amount = Decimal("0.00")
            discount_display = ""
            sales_tax_rate = Decimal("8.875")  # 8.875%
            sales_tax = Decimal("0.00")
            total_price = Decimal("0.00")
            
            try:
                if price:
                    price_decimal = Decimal(str(price))
                    subtotal += price_decimal
                if parking_fee:
                    subtotal += Decimal(str(parking_fee))
                
                # Calculate discount
                if discount:
                    discount_value = Decimal(str(discount))
                    if discount_type == "percentage":
                        # Calculate discount from subtotal
                        if subtotal > 0:
                            discount_amount = (subtotal * discount_value) / Decimal("100")
                            discount_display = f"{discount}%"
                        else:
                            discount_amount = Decimal("0.00")
                            discount_display = f"{discount}%"
                    else:
                        # Direct dollar amount
                        discount_amount = discount_value
                        discount_display = f"${discount}"
                    subtotal -= discount_amount
                
                # Calculate sales tax (8.875% of subtotal after discount)
                if subtotal > 0:
                    sales_tax = (subtotal * sales_tax_rate) / Decimal("100")
                
                # Calculate total (subtotal + sales tax)
                total_price = subtotal + sales_tax
            except (ValueError, TypeError):
                pass
            
            # Prepare email context
            context = {
                "quote": office_cleaning_quote,
                "customer_name": customer_name,
                "customer_email": customer_email,
                "customer_phone": customer_phone,
                "business_address": business_address,
                "square_footage": square_footage,
                "job_description": job_description,
                "service_date": service_date,
                "service_time": service_time,
                "cleaning_frequency": cleaning_frequency,
                "business_type": business_type,
                "crew_size_hours": crew_size_hours,
                "estimated_time": estimated_time,
                "price": price,
                "parking_fee": parking_fee,
                "discount": discount,
                "discount_type": discount_type,
                "discount_amount": discount_amount,
                "discount_display": discount_display,
                "subtotal": subtotal,
                "sales_tax_rate": sales_tax_rate,
                "sales_tax": sales_tax,
                "total_price": total_price,
                "payment_link": payment_link,
                "note": note,
                "request_scheme": request.scheme,
                "domain": get_current_site(request).domain,
            }
            
            # Render email template
            html_content = render_to_string("adminpanel/emails/office_cleaning_quote_email.html", context)
            text_content = strip_tags(html_content)
            
            # Send email
            subject = f"Your Office Cleaning Quote - #{office_cleaning_quote.id}"
            from django.conf import settings
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[customer_email],
                bcc=["support@thecleanhandy.com"]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            # Save email sending time and add to email history log
            from django.utils import timezone
            import json
            email_sent_time = timezone.now()
            
            # Store email history in admin_notes as JSON
            try:
                email_entry = {
                    'sent_at': email_sent_time.isoformat(),
                    'customer_email': customer_email,
                    'price': str(price) if price else None,
                    'discount': str(discount) if discount else None,
                    'discount_type': discount_type,
                    'parking_fee': str(parking_fee) if parking_fee else None,
                }
                
                # Get existing notes
                existing_notes = office_cleaning_quote.admin_notes or ""
                existing_data = {}
                
                # Try to parse existing JSON data
                try:
                    existing_data = json.loads(existing_notes)
                    if not isinstance(existing_data, dict):
                        existing_data = {}
                except (json.JSONDecodeError, ValueError):
                    # If admin_notes is not JSON, preserve it as admin_notes_text
                    existing_data = {'admin_notes_text': existing_notes}
                
                # Initialize email_history array if it doesn't exist
                if 'email_history' not in existing_data:
                    existing_data['email_history'] = []
                
                # Add new email entry to history
                existing_data['email_history'].append(email_entry)
                
                # Also keep latest email info for backward compatibility
                existing_data['quote_email_sent_at'] = email_sent_time.isoformat()
                existing_data['customer_email'] = customer_email
                
                # Save updated notes
                office_cleaning_quote.admin_notes = json.dumps(existing_data, indent=2)
                # Update status to "email_sent" after sending email
                office_cleaning_quote.status = "email_sent"
                office_cleaning_quote.save(update_fields=['admin_notes', 'status'])
            except Exception as save_error:
                print(f"Warning: Could not save email history: {save_error}")
            
            messages.success(request, f"📧 Email sent successfully to {customer_email} on {email_sent_time.strftime('%B %d, %Y at %I:%M %p')}")
        except Exception as e:
            messages.error(request, f"❌ Failed to send email: {str(e)}")
    
    return redirect("office_cleaning_quote_detail", quote_id=quote_id)


@login_required
@require_POST
def delete_office_cleaning_quote(request, quote_id):
    """Delete an office cleaning quote"""
    quote = get_object_or_404(OfficeQuote, id=quote_id)
    quote.delete()
    messages.success(request, "Office cleaning quote deleted successfully.")
    return redirect("office_cleaning_quote_list")


def export_office_cleaning_quotes_csv(request):
    """Export office cleaning quotes to CSV"""
    office_cleaning_quotes = OfficeQuote.objects.all().order_by('-created_at')
    
    # Apply filters if provided
    status_filter = request.GET.get('status')
    if status_filter:
        office_cleaning_quotes = office_cleaning_quotes.filter(status=status_filter)
    
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    
    if from_date:
        office_cleaning_quotes = office_cleaning_quotes.filter(created_at__date__gte=from_date)
    if to_date:
        office_cleaning_quotes = office_cleaning_quotes.filter(created_at__date__lte=to_date)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=office_cleaning_quotes.csv'
    
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Name', 'Email', 'Phone', 'Business Address', 'Square Footage',
        'Job Description', 'Status', 'Created At'
    ])
    
    for quote in office_cleaning_quotes:
        writer.writerow([
            quote.id,
            quote.name or '',
            quote.email or '',
            quote.phone_number or '',
            quote.business_address or '',
            quote.square_footage or '',
            quote.job_description or '',
            quote.status or '',
            quote.created_at.strftime('%Y-%m-%d %H:%M:%S') if quote.created_at else '',
        ])
    
    return response


def export_home_cleaning_quotes_csv(request):
    """Export home cleaning quotes to CSV"""
    home_cleaning_quotes = HomeCleaningQuoteRequest.objects.all().order_by('-created_at')
    
    # Apply filters if provided
    cleaning_type_filter = request.GET.get('cleaning_type')
    if cleaning_type_filter:
        home_cleaning_quotes = home_cleaning_quotes.filter(cleaning_type=cleaning_type_filter)
    
    frequency_filter = request.GET.get('frequency')
    if frequency_filter:
        home_cleaning_quotes = home_cleaning_quotes.filter(cleaning_frequency=frequency_filter)
    
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    
    if from_date:
        home_cleaning_quotes = home_cleaning_quotes.filter(created_at__date__gte=from_date)
    if to_date:
        home_cleaning_quotes = home_cleaning_quotes.filter(created_at__date__lte=to_date)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=home_cleaning_quotes.csv'
    
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Name', 'Email', 'Phone', 'Address', 'City', 'State', 'ZIP',
        'Service', 'Home Type', 'Cleaning Type', 'Bath Count',
        'Date', 'Hour', 'Frequency',
        'Get In', 'Parking', 'Pet', 'Job Description', 'Created At'
    ])
    
    for quote in home_cleaning_quotes:
        writer.writerow([
            quote.id,
            quote.name or '',
            quote.email or '',
            quote.phone or '',
            quote.address or '',
            quote.city or '',
            quote.state or '',
            quote.zip_code or '',
            quote.service.name if quote.service else '',
            quote.home_types.name if quote.home_types else '',
            quote.cleaning_type or '',
            quote.bath_count or '',
            quote.date.strftime('%Y-%m-%d') if quote.date else '',
            quote.hour.strftime('%H:%M') if quote.hour else '',
            quote.cleaning_frequency or '',
            quote.get_in or '',
            quote.parking or '',
            quote.pet or '',
            quote.job_description or '',
            quote.created_at.strftime('%Y-%m-%d %H:%M:%S') if quote.created_at else '',
        ])
    
    return response






