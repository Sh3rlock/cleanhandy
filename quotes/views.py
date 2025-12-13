from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import Quote, Service, CleaningExtra, ServiceCategory, NewsletterSubscriber, Booking, Review, OfficeQuote, HandymanQuote, PostEventCleaningQuote, HomeCleaningQuoteRequest
from customers.models import Customer  # Import Customer from the correct app
from .forms import CleaningQuoteForm, HandymanQuoteForm, NewsletterForm, CleaningBookingForm, HandymanBookingForm, ContactForm, OfficeQuoteForm, OfficeCleaningBookingForm, HandymanQuoteForm, PostEventCleaningQuoteForm, HomeCleaningQuoteRequestForm
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from .utils import get_available_hours_for_date, send_quote_email_cleaning, send_office_cleaning_booking_emails, send_email_with_timeout
from django.http import JsonResponse, HttpResponse
from datetime import datetime, time, timedelta, date
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from decimal import Decimal
from django.core.exceptions import ValidationError
import os
import json

from django.http import HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404

from .utils import process_handyman_quote, send_quote_email_handyman
from django.contrib import messages

from giftcards.models import GiftCard

from django.contrib.auth.forms import AuthenticationForm
from accounts.forms import CustomUserRegistrationForm, CustomLoginForm  # your custom register form
from django.contrib.auth import login

"""
HOURLY RATE USAGE EXAMPLES:

# Get hourly rate for a specific service
from .utils import get_hourly_rate
office_rate = get_hourly_rate('office_cleaning')  # Returns Decimal('75.00')
home_rate = get_hourly_rate('home_cleaning')      # Returns Decimal('55.00')

# Calculate labor cost
from .utils import calculate_labor_cost
total_cost = calculate_labor_cost('office_cleaning', 2, 3)  # 2 cleaners, 3 hours

# Get all active rates
from .utils import get_all_hourly_rates
all_rates = get_all_hourly_rates()  # Returns dict of all active rates
"""


def home(request):
    # Check if under construction mode is enabled
    if getattr(settings, 'UNDER_CONSTRUCTION', False):
        # Allow admin/staff users to access the site normally
        if not (hasattr(request, 'user') and request.user.is_authenticated and 
                (request.user.is_staff or request.user.is_superuser)):
            # Show under construction page for regular users and anonymous visitors
            return render(request, "under_construction.html", status=503)
    
    services = Service.objects.filter(category__name="Cleaning")
    home_services = Service.objects.filter(category__name="Home")
    commercial_services = Service.objects.filter(category__name="Commercial")
    handyman_services = Service.objects.filter(category__name="Handyman")
    top_services = Service.objects.order_by('-view_count')[:6]
    reviews = Review.objects.all()

    return render(request, "home.html", {
        "services": services,
        "home_services": home_services,
        "commercial_services": commercial_services,
        "handyman_services": handyman_services,
        "top_services": top_services,
        "login_form": CustomLoginForm(),
        "register_form": CustomUserRegistrationForm(),
        "reviews": reviews,
    })

def about(request):
    services = Service.objects.all()
    return render(request, "about.html", {
        "services": services,
    })

def contact(request):
    from .forms import ContactForm
    from .models import Contact
    from django.core.mail import send_mail
    success = False
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save()
            # Send email notification
            subject = f"New Contact Message: {contact.subject}"
            message = f"Name: {contact.name}\nEmail: {contact.email}\nSubject: {contact.subject}\n\nMessage:\n{contact.message}"
            send_mail(
                subject,
                message,
                "noreply@cleanhandy.com",
                ["support@thecleanhandy.com"],
                fail_silently=False,
            )
            success = True
            form = ContactForm()  # Reset form after success
    else:
        form = ContactForm()
    return render(request, "contact.html", {"form": form, "success": success})

def blog(request):
    return render(request, "blog.html")

def blog_detail(request):
    return render(request, "blog_detail.html")

def request_cleaning_quote(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    all_services = Service.objects.all()

    # Get related services in the Home category (for suggestion sidebar)
    home_category = ServiceCategory.objects.filter(name__iexact='cleaning').first()
    related_services = (
        Service.objects.filter(category=home_category).exclude(id=service_id)
        if home_category else Service.objects.none()
    )

    # Track service view count
    service.view_count += 1
    service.save(update_fields=["view_count"])

    return render(request, "quotes/request_cleaning_quote.html", {
        "service": service,
        "all_services": all_services,
        "related_services": related_services,
    })


def request_handyman_quote(request, service_id):
    service = get_object_or_404(Service, id=service_id)

    cleaning_category = ServiceCategory.objects.filter(name__iexact='handyman').first()

    related_services = Service.objects.filter(
        category=cleaning_category
    ).exclude(id=service_id) if cleaning_category else Service.objects.none()

    # Increment the view count for the service
    service.view_count += 1
    service.save(update_fields=["view_count"])

    if request.method == "POST":
        form = HandymanQuoteForm(request.POST)
        if form.is_valid():
            quote = process_handyman_quote(form, request, service=service)
            return redirect("quote_submitted_handyman", quote_id=quote.id)
    else:
        form = HandymanQuoteForm(initial={'service': service.id})
    return render(request, "quotes/request_handyman_quote.html", {"form": form, "service": service, "related_services": related_services})

def quote_submitted_handyman(request, quote_id):
    quote = get_object_or_404(Booking, id=quote_id)
    return render(request, "quotes/quote_submitted_handyman.html", {"quote": quote})

def quote_submitted(request, quote_id):
    quote = get_object_or_404(Quote, id=quote_id)
    return render(request, "quotes/quote_submitted.html", {
        "quote": quote
    })

def home_cleaning_quote(request):
    """Display and handle home cleaning quote form"""
    # Get service category for home cleaning
    service_cat = ServiceCategory.objects.filter(name__iexact='home').first()
    if not service_cat:
        # Fallback: try to get first home service
        home_service = Service.objects.filter(category__name__iexact='home').first()
        if home_service:
            service_cat = home_service.category
    
    # Get related services for sidebar
    home_category = ServiceCategory.objects.filter(name__iexact='home').first()
    related_services = (
        Service.objects.filter(category=home_category)
        if home_category else Service.objects.none()
    )
    
    # Initialize saved_addresses for authenticated users
    saved_addresses = []
    if request.user.is_authenticated and hasattr(request.user, "profile"):
        saved_addresses = request.user.profile.addresses.all()
    
    if request.method == "POST":
        # Handle date and time from calendar selection
        selected_date = request.POST.get('selected_date')
        selected_time = request.POST.get('selected_time')
        
        # Create a mutable copy of POST data
        post_data = request.POST.copy()
        
        # Update form data with selected date and time if provided
        if selected_date:
            post_data['date'] = selected_date
        if selected_time:
            # Convert time string to time format
            try:
                if ':' in selected_time:
                    hour, minute = map(int, selected_time.split(':'))
                    time_str = f"{hour:02d}:{minute:02d}"
                    post_data['hour'] = time_str
            except:
                pass
        
        # Set service based on cleaning_type if provided, otherwise use default
        cleaning_type = post_data.get('cleaning_type', '')
        service_set = False
        
        if cleaning_type:
            # Try to find service based on cleaning type - match exact service names
            home_services = Service.objects.filter(category__name__iexact='home')
            if not home_services.exists() and service_cat:
                home_services = Service.objects.filter(category=service_cat)
            
            # Map cleaning types to exact service names from database
            service_name_mapping = {
                'Regular Cleaning': 'Deep Cleaning',  # Use Deep Cleaning as default for Regular (no Regular Cleaning service exists)
                'Deep Cleaning': 'Deep Cleaning',
                'Move In/Out Cleaning': 'Move In/Out Cleaning',
                'Post Renovation': 'Post Renovation Cleaning'
            }
            
            target_service_name = service_name_mapping.get(cleaning_type)
            
            if target_service_name:
                for service in home_services:
                    if service.name == target_service_name:
                        post_data['service'] = service.id  # Use integer, not string
                        service_set = True
                        print(f"✅ Set service to: {service.id} ({service.name}) for {cleaning_type}")
                        break
        
        # Fallback to default home service if not set based on cleaning type
        if not service_set and not post_data.get('service'):
            # Get first Home category service
            home_service = Service.objects.filter(category__name__iexact='home').first()
            if not home_service and service_cat:
                home_service = Service.objects.filter(category=service_cat).first()
            if home_service:
                post_data['service'] = home_service.id  # Use integer
                print(f"✅ Set default service to: {home_service.id} ({home_service.name})")
            else:
                # Last resort: get any service
                any_service = Service.objects.first()
                if any_service:
                    post_data['service'] = any_service.id  # Use integer
                    print(f"✅ Set fallback service to: {any_service.id} ({any_service.name})")
        
        print(f"🔍 POST data service value: {post_data.get('service')} (type: {type(post_data.get('service'))})")
        # Ensure service is an integer
        if post_data.get('service'):
            try:
                post_data['service'] = int(post_data['service'])
            except (ValueError, TypeError):
                print(f"⚠️ Could not convert service to integer: {post_data.get('service')}")
        
        form = HomeCleaningQuoteRequestForm(post_data)
        
        print(f"🔍 Form validation check - is_valid(): {form.is_valid()}")
        if not form.is_valid():
            print(f"❌ Form validation failed!")
            print(f"❌ Form errors: {form.errors}")
            print(f"❌ Form non-field errors: {form.non_field_errors()}")
        
        if form.is_valid():
            quote_request = form.save(commit=False)
            
            # Set service from post_data
            service_id = post_data.get('service')
            if service_id:
                try:
                    service = Service.objects.filter(id=int(service_id)).first()
                    if service:
                        quote_request.service = service
                        print(f"✅ Set service: {service.id} ({service.name})")
                except:
                    pass
            
            # Ensure service is set
            if not quote_request.service:
                home_service = Service.objects.filter(category__name__iexact='home').first()
                if not home_service and service_cat:
                    home_service = Service.objects.filter(category=service_cat).first()
                if home_service:
                    quote_request.service = home_service
                    print(f"✅ Set default service: {home_service.id} ({home_service.name})")
            
            # Handle date and time from calendar
            if selected_date:
                try:
                    quote_request.date = datetime.strptime(selected_date, '%Y-%m-%d').date()
                except:
                    pass
            if selected_time:
                try:
                    if ':' in selected_time:
                        hour, minute = map(int, selected_time.split(':'))
                        quote_request.hour = time(hour, minute)
                except:
                    pass
            
            # Set cleaning_frequency
            cleaning_frequency = post_data.get('cleaning_frequency', 'one_time')
            quote_request.cleaning_frequency = cleaning_frequency
            
            # Ensure required fields are set
            if not quote_request.date:
                quote_request.date = date.today() + timedelta(days=2)
            if not quote_request.hour:
                quote_request.hour = time(9, 0)
            if not quote_request.city:
                quote_request.city = 'New York'
            if not quote_request.state:
                quote_request.state = 'NY'
            
            # Save the quote request
            try:
                quote_request.save()
                print(f"✅ Successfully saved HomeCleaningQuoteRequest with ID: {quote_request.id}")
                print(f"✅ Saved data - Name: {quote_request.name}, Email: {quote_request.email}, Phone: {quote_request.phone}")
            except Exception as e:
                print(f"❌ ERROR saving HomeCleaningQuoteRequest: {str(e)}")
                import traceback
                traceback.print_exc()
                messages.error(request, f"An error occurred while saving your quote: {str(e)}")
                # Re-render form with error
                home_service = Service.objects.filter(category__name__iexact='home').first()
                if not home_service and service_cat:
                    home_service = Service.objects.filter(category=service_cat).first()
                if not home_service:
                    home_service = Service.objects.first()
                
                home_services = Service.objects.filter(category__name__iexact='home')
                if not home_services.exists() and service_cat:
                    home_services = Service.objects.filter(category=service_cat)
                
                cleaning_type_to_service = {}
                for service in home_services:
                    service_name_lower = service.name.lower()
                    if 'regular' in service_name_lower or 'standard' in service_name_lower or 'basic' in service_name_lower:
                        cleaning_type_to_service['Regular Cleaning'] = service.id
                    elif 'deep' in service_name_lower:
                        cleaning_type_to_service['Deep Cleaning'] = service.id
                    elif 'move' in service_name_lower or 'in/out' in service_name_lower or 'in-out' in service_name_lower:
                        cleaning_type_to_service['Move In/Out Cleaning'] = service.id
                    elif 'renovation' in service_name_lower or 'post' in service_name_lower:
                        cleaning_type_to_service['Post Renovation'] = service.id
                
                if home_service and not cleaning_type_to_service:
                    for cleaning_type in ['Regular Cleaning', 'Deep Cleaning', 'Move In/Out Cleaning', 'Post Renovation']:
                        cleaning_type_to_service[cleaning_type] = home_service.id
                elif home_service:
                    for cleaning_type in ['Regular Cleaning', 'Deep Cleaning', 'Move In/Out Cleaning', 'Post Renovation']:
                        if cleaning_type not in cleaning_type_to_service:
                            cleaning_type_to_service[cleaning_type] = home_service.id
                
                return render(request, "quotes/home_cleaning_quote.html", {
                    "form": form,
                    "service_cat": service_cat,
                    "home_service": home_service,
                    "related_services": related_services,
                    "saved_addresses": saved_addresses,
                    "cleaning_type_to_service": json.dumps(cleaning_type_to_service),
                })
            
            # Send email notification to admin
            try:
                subject = f"New Home Cleaning Quote Request from {quote_request.name or 'Customer'}"
                message = f"""
New Home Cleaning Quote Request:

Name: {quote_request.name or 'N/A'}
Email: {quote_request.email or 'N/A'}
Phone: {quote_request.phone or 'N/A'}

Service Details:
- Home Type: {quote_request.home_types.name if quote_request.home_types else 'N/A'}
- Cleaning Type: {quote_request.cleaning_type or 'N/A'}
- Number of Bathrooms: {quote_request.bath_count or 'N/A'}
- Cleaning Frequency: {quote_request.cleaning_frequency or 'N/A'}

Scheduling:
- Date: {quote_request.date.strftime('%Y-%m-%d') if quote_request.date else 'N/A'}
- Time: {quote_request.hour.strftime('%H:%M') if quote_request.hour else 'N/A'}

Address:
- Street: {quote_request.address or 'N/A'}
- Apartment: {quote_request.apartment or 'N/A'}
- City: {quote_request.city or 'N/A'}
- State: {quote_request.state or 'N/A'}
- ZIP Code: {quote_request.zip_code or 'N/A'}

Property Access:
- How to get in: {quote_request.get_in or 'N/A'}
- Parking Instructions: {quote_request.parking or 'N/A'}
- Pets: {quote_request.pet or 'N/A'}

Job Description:
{quote_request.job_description or 'N/A'}

Submitted at: {quote_request.created_at.strftime('%Y-%m-%d %H:%M:%S') if quote_request.created_at else 'N/A'}
Quote ID: {quote_request.id}
"""
                
                send_mail(
                    subject,
                    message,
                    "noreply@cleanhandy.com",
                    ["support@thecleanhandy.com"],  # Admin email
                    fail_silently=False,
                )
                print(f"✅ Email notification sent to admin for Home Cleaning Quote #{quote_request.id}")
            except Exception as e:
                print(f"❌ Email send failed for Home Cleaning Quote #{quote_request.id}: {e}")
                # Don't fail the request if email fails - just log the error
            
            # Redirect to a success page
            messages.success(request, "Your home cleaning quote request has been submitted successfully!")
            return redirect("home_cleaning_quote_submitted", quote_id=quote_request.id)
        else:
            print("❌ Form errors:", form.errors)
            # Re-render form with errors
            # Get home service for template
            home_service = Service.objects.filter(category__name__iexact='home').first()
            if not home_service and service_cat:
                home_service = Service.objects.filter(category=service_cat).first()
            if not home_service:
                home_service = Service.objects.first()
            
            # Create mapping of cleaning types to services for error rendering
            home_services = Service.objects.filter(category__name__iexact='home')
            if not home_services.exists() and service_cat:
                home_services = Service.objects.filter(category=service_cat)
            
            cleaning_type_to_service = {}
            # Map cleaning types to exact service names from database
            service_name_mapping = {
                'Regular Cleaning': 'Deep Cleaning',  # Use Deep Cleaning as default for Regular
                'Deep Cleaning': 'Deep Cleaning',
                'Move In/Out Cleaning': 'Move In/Out Cleaning',
                'Post Renovation': 'Post Renovation Cleaning'
            }
            
            for cleaning_type, target_service_name in service_name_mapping.items():
                for service in home_services:
                    if service.name == target_service_name:
                        cleaning_type_to_service[cleaning_type] = service.id
                        break
            
            if home_service and not cleaning_type_to_service:
                for cleaning_type in ['Regular Cleaning', 'Deep Cleaning', 'Move In/Out Cleaning', 'Post Renovation']:
                    cleaning_type_to_service[cleaning_type] = home_service.id
            elif home_service:
                for cleaning_type in ['Regular Cleaning', 'Deep Cleaning', 'Move In/Out Cleaning', 'Post Renovation']:
                    if cleaning_type not in cleaning_type_to_service:
                        cleaning_type_to_service[cleaning_type] = home_service.id

            return render(request, "quotes/home_cleaning_quote.html", {
                "form": form,
                "service_cat": service_cat,
                "home_service": home_service,
                "related_services": related_services,
                "saved_addresses": saved_addresses,
                "cleaning_type_to_service": json.dumps(cleaning_type_to_service),
            })
    else:
        # Initialize form with user data if logged in
        initial_data = {}
        
        # Set default service - always required, always Home category
        home_service = Service.objects.filter(category__name__iexact='home').first()
        if not home_service and service_cat:
            home_service = Service.objects.filter(category=service_cat).first()
        
        if home_service:
            initial_data['service'] = home_service.id
        
        if request.user.is_authenticated:
            # Pre-fill contact information
            initial_data['email'] = request.user.email
            
            if hasattr(request.user, "profile"):
                profile = request.user.profile
                if profile.full_name:
                    initial_data['name'] = profile.full_name
                if profile.phone:
                    initial_data['phone'] = profile.phone
                
                # Pre-fill with first saved address if available
                if saved_addresses.exists():
                    default_address = saved_addresses.first()
                    initial_data.update({
                        "address": default_address.street_address,
                        "apartment": default_address.apt_suite,
                        "zip_code": default_address.zip_code,
                    })
        
        form = HomeCleaningQuoteRequestForm(initial=initial_data)
    
    # Get default home service for template - always Home category
    home_service = Service.objects.filter(category__name__iexact='home').first()
    if not home_service and service_cat:
        home_service = Service.objects.filter(category=service_cat).first()
    
    # Create mapping of cleaning types to services
    # Get all home category services
    home_services = Service.objects.filter(category__name__iexact='home')
    if not home_services.exists() and service_cat:
        home_services = Service.objects.filter(category=service_cat)
    
    # Map cleaning types to services
    cleaning_type_to_service = {}
    for service in home_services:
        service_name_lower = service.name.lower()
        if 'regular' in service_name_lower or 'standard' in service_name_lower or 'basic' in service_name_lower:
            cleaning_type_to_service['Regular Cleaning'] = service.id
        elif 'deep' in service_name_lower:
            cleaning_type_to_service['Deep Cleaning'] = service.id
        elif 'move' in service_name_lower or 'in/out' in service_name_lower or 'in-out' in service_name_lower:
            cleaning_type_to_service['Move In/Out Cleaning'] = service.id
        elif 'renovation' in service_name_lower or 'post' in service_name_lower:
            cleaning_type_to_service['Post Renovation'] = service.id
    
    # If no specific matches, use the first home service as default for all
    if home_service and not cleaning_type_to_service:
        for cleaning_type in ['Regular Cleaning', 'Deep Cleaning', 'Move In/Out Cleaning', 'Post Renovation']:
            cleaning_type_to_service[cleaning_type] = home_service.id
    elif home_service:
        # Fill in any missing mappings with default home service
        for cleaning_type in ['Regular Cleaning', 'Deep Cleaning', 'Move In/Out Cleaning', 'Post Renovation']:
            if cleaning_type not in cleaning_type_to_service:
                cleaning_type_to_service[cleaning_type] = home_service.id
    
    return render(request, "quotes/home_cleaning_quote.html", {
        "form": form,
        "service_cat": service_cat,
        "home_service": home_service,
        "related_services": related_services,
        "saved_addresses": saved_addresses,
        "cleaning_type_to_service": json.dumps(cleaning_type_to_service),
    })

def cleaning_services(request):
    services = Service.objects.filter(category__name="Home")
    return render(request, "quotes/cleaning_services.html", {"services": services})

def commercial_services(request):
    services = Service.objects.filter(category__name="Commercial")
    return render(request, "quotes/commercial_services.html", {"services": services})

def handyman_services(request):
    services = Service.objects.filter(category__name="Handyman")
    return render(request, "quotes/handyman_services.html", {"services": services})

def available_hours_api(request):
    try:
        date_str = request.GET.get("date")
        hours = int(request.GET.get("hours", 2))  # get from query param or default 2
        
        print(f"🕐 Available hours API called: date={date_str}, hours={hours}")
        
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            print(f"❌ Invalid date format: {date_str}")
            return JsonResponse({"error": "Invalid date"}, status=400)

        print(f"📅 Parsed date: {date}")
        available = get_available_hours_for_date(date, hours_requested=hours)
        print(f"✅ Found {len(available)} available hours")
        
        formatted = [slot.strftime("%H:%M") for slot in available]
        return JsonResponse({"available_hours": formatted})
        
    except Exception as e:
        print(f"❌ Error in available_hours_api: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": "Internal server error"}, status=500)


def subscribe_newsletter(request):
    if request.method == 'POST':
        if not request.POST.get('agree_terms'):
            return JsonResponse({'status': 'error', 'message': 'You must agree to the terms.'})

        form = NewsletterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            subscriber, created = NewsletterSubscriber.objects.get_or_create(email=email)

            if not created:
                return JsonResponse({'status': 'info', 'message': 'You are already subscribed.'})

            return JsonResponse({'status': 'success', 'message': 'Thanks for subscribing!'})

        # Extract the first form error to display in the UI
        error_message = form.errors.get('email')
        if error_message:
            return JsonResponse({'status': 'error', 'message': error_message[0]})
        
        return JsonResponse({'status': 'error', 'message': 'Invalid input.'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request.'})



# Booking a service
def request_cleaning_booking(request, service_cat_id):
    try:
        print("🏠 Home cleaning booking view started")
        service_cat = get_object_or_404(ServiceCategory, id=service_cat_id)
        extras = CleaningExtra.objects.all()
        print(f"✅ Service category found: {service_cat}")
        print(f"✅ Cleaning extras count: {extras.count()}")
    except Exception as e:
        print(f"❌ Error in home cleaning view setup: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

    # Get related services in the Home category (for suggestion sidebar)
    home_category = ServiceCategory.objects.filter(name__iexact='home').first()
    related_services = (
        Service.objects.filter(category=home_category).exclude(id=service_cat_id)
        if home_category else Service.objects.none()
    )

    # Track service view count
    service_cat.view_count += 1
    service_cat.save(update_fields=["view_count"])

    if request.method == "POST":
        form = CleaningBookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.service_cat = service_cat

            # Save initially to set many-to-many
            booking.save()

            # Set extras (many-to-many)
            selected_extra_ids = request.POST.getlist("extras")
            if selected_extra_ids:
                selected_extras = CleaningExtra.objects.filter(id__in=selected_extra_ids)
                booking.extras.set(selected_extras)

            # Server-side price calculation
            booking.price = booking.calculate_total_price()

            # Apply Gift Card
            code = form.cleaned_data.get('giftcard_code')
            if code:
                try:
                    gift = GiftCard.objects.get(code=code.upper(), is_active=True)
                    if gift.balance >= booking.price:
                        gift.balance -= booking.price
                        booking.price = 0
                        gift.is_active = gift.balance > 0
                    else:
                        booking.price -= gift.balance
                        gift.balance = 0
                        gift.is_active = False
                    gift.save()
                    booking.giftcard_code_used = gift.code  # optional field in Booking
                except GiftCard.DoesNotExist:
                    form.add_error("giftcard_code", "Invalid or insufficient gift card.")
                    return render(request, "booking/request_cleaning_booking.html", {
                        "form": form,
                        "cleaning_extras": extras,
                        "service_cat": service_cat,
                        "related_services": related_services,
                    })

            booking.save()

            try:
                send_quote_email_cleaning(booking)
                print(f"✅ Email sending completed for booking {booking.id}")
            except Exception as e:
                print(f"❌ Email send failed: {str(e)}")
            
            print(f"🔄 About to redirect to booking_submitted_cleaning with booking_id={booking.id}")
            print(f"🔄 Redirect URL should be: /accounts/submitted/{booking.id}/")
            return redirect("booking_submitted_cleaning", booking_id=booking.id)
        else:
            print("❌ Form errors:", form.errors)
            return render(request, "booking/request_cleaning_booking.html", {
                "form": form,
                "cleaning_extras": extras,
                "service_cat": service_cat,
                "related_services": related_services,
            })
    else:
        form = CleaningBookingForm(initial={'service_cat': service_cat.id})

    return render(request, "booking/request_cleaning_booking.html", {
        "form": form,
        "cleaning_extras": extras,
        "service_cat": service_cat,
        "related_services": related_services,
    })


def request_handyman_booking(request, service_cat_id):
    service_cat = get_object_or_404(ServiceCategory, id=service_cat_id)

    cleaning_category = ServiceCategory.objects.filter(name__iexact='handyman').first()

    related_services = Service.objects.filter(
        category=cleaning_category
    ).exclude(id=service_cat_id) if cleaning_category else Service.objects.none()

    # Increment the view count for the service
    service_cat.view_count += 1
    service_cat.save(update_fields=["view_count"])

    if request.method == "POST":
        form = HandymanBookingForm(request.POST)
        if form.is_valid():
            booking = process_handyman_quote(form, request, service=service_cat)
            return redirect("quote_submitted_handyman", quote_id=booking.id)
    else:
        form = HandymanBookingForm(initial={'service': service_cat.id})
    return render(request, "request/request_handyman_booking.html", {"form": form, "service_cat": service_cat, "related_services": related_services})

def cleaning_booking(request):
    service_cat = ServiceCategory.objects.filter(name__iexact='home').first()
    extras = CleaningExtra.objects.all()

    # Related services for sidebar
    home_category = ServiceCategory.objects.filter(name__iexact='home').first()
    related_services = (
        Service.objects.filter(category=home_category)
        if home_category else Service.objects.none()
    )

    # Initialize saved_addresses for authenticated users
    saved_addresses = []
    if request.user.is_authenticated and hasattr(request.user, "profile"):
        saved_addresses = request.user.profile.addresses.all()


    if request.method == "POST":
        try:
            print("📋 POST data received:")
            for key, value in request.POST.items():
                print(f"  {key}: {value}")
            
            # Check if required database objects exist
            try:
                from quotes.models import SquareFeetOption, HomeType
                square_feet_options = SquareFeetOption.objects.all()
                home_types = HomeType.objects.all()
                print(f"✅ SquareFeetOption count: {square_feet_options.count()}")
                print(f"✅ HomeType count: {home_types.count()}")
            except Exception as e:
                print(f"❌ Error checking database objects: {str(e)}")
            
            form = CleaningBookingForm(request.POST)
            print(f"🔍 Form validation: {form.is_valid()}")
            
            if form.is_valid():
                print("✅ Form is valid, processing booking...")
                booking = form.save(commit=False)
                booking.service_cat = service_cat
                
                # Set cleaning frequency from form data
                booking.cleaning_frequency = request.POST.get('cleaning_frequency', 'one_time')
                print(f"✅ Set cleaning frequency: {booking.cleaning_frequency}")

                # Additional time slot conflict check at view level
                from .utils import check_time_slot_conflict
                if check_time_slot_conflict(booking.date, booking.hour, booking.hours_requested):
                    form.add_error('hour', 'This time slot is already booked. Please select a different time.')
                    print("❌ Time slot conflict detected at view level")
                    return render(request, "booking/cleaning_booking.html", {
                        "form": form,
                        "cleaning_extras": extras,
                        "service_cat": service_cat,
                        "related_services": related_services,
                        "saved_addresses": saved_addresses,
                        "STRIPE_PUBLISHABLE_KEY": settings.STRIPE_PUBLISHABLE_KEY,
                    })

                # Save first to set M2M
                booking.save()
                print(f"✅ Booking created with ID: {booking.id}")

                selected_extra_ids = request.POST.getlist("extras")
                if selected_extra_ids:
                    selected_extras = CleaningExtra.objects.filter(id__in=selected_extra_ids)
                    booking.extras.set(selected_extras)
                    print(f"✅ Set extras: {[extra.name for extra in selected_extras]}")

                # --- Handle Gift Card or Discount Code ---
                code_data = form.cleaned_data.get("gift_card_code")
                
                # Check if gift card discount is applied via frontend JavaScript
                gift_card_discount_from_frontend = request.POST.get('applied_gift_card_amount')
                if gift_card_discount_from_frontend:
                    try:
                        booking.gift_card_discount = Decimal(gift_card_discount_from_frontend)
                        print(f"✅ Applied gift card discount from frontend: {booking.gift_card_discount}")
                    except:
                        print(f"❌ Invalid gift card discount from frontend: {gift_card_discount_from_frontend}")

                try:
                    # Calculate initial price
                    booking.price = booking.calculate_total_price()
                    print(f"✅ Calculated booking price: {booking.price}")
                    
                    if code_data:
                        code_type, code_obj = code_data

                        if code_type == "giftcard":
                            booking.gift_card = code_obj
                            booking.gift_card_discount = min(code_obj.balance, booking.price)

                        elif code_type == "discount":
                            if code_obj.discount_type == "fixed":
                                booking.gift_card_discount = min(code_obj.value, booking.price)
                            elif code_obj.discount_type == "percent":
                                booking.gift_card_discount = booking.price * (code_obj.value / 100)
                            code_obj.times_used += 1
                            code_obj.save()

                    # Recalculate final price after discount
                    booking.price = booking.calculate_total_price()
                    print(f"✅ Final booking price: {booking.price}")
                    
                except Exception as e:
                    print(f"❌ Error calculating booking price: {str(e)}")
                    # Set a default price to prevent booking failure
                    booking.price = Decimal("100.00")  # Default price
                    booking.gift_card_discount = None
                
                booking.save()

                # --- Deduct Gift Card balance if used ---
                if code_data:
                    code_type, code_obj = code_data
                    if code_type == "giftcard" and booking.gift_card_discount:
                        code_obj.balance -= booking.gift_card_discount
                        if code_obj.balance <= 0:
                            code_obj.is_active = False
                        code_obj.save()

                try:
                    send_quote_email_cleaning(booking)
                    print(f"✅ Email sending completed for booking {booking.id}")
                except Exception as e:
                    print(f"❌ Email send failed: {str(e)}")

                # Check if this is an AJAX request (for Stripe payment)
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'booking_id': booking.id,
                        'total_amount': float(booking.price),
                        'calculated_total': float(booking.calculate_total_price()),
                        'redirect_url': f'/accounts/submitted/{booking.id}/'
                    })
                else:
                    print(f"🔄 Redirecting to booking_submitted_cleaning with booking_id={booking.id}")
                    return redirect("booking_submitted_cleaning", booking_id=booking.id)

            else:
                print("❌ Form errors:", form.errors)
                print("❌ Form non-field errors:", form.non_field_errors())
                for field, errors in form.errors.items():
                    print(f"❌ Field '{field}' errors: {errors}")
                
                # Check if this is an AJAX request
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': 'Form validation failed',
                        'errors': form.errors,
                        'non_field_errors': form.non_field_errors()
                    })
                else:
                    return render(request, "booking/cleaning_booking.html", {
                    "form": form,
                    "cleaning_extras": extras,
                    "service_cat": service_cat,
                    "related_services": related_services,
                    "saved_addresses": saved_addresses,
                    "STRIPE_PUBLISHABLE_KEY": settings.STRIPE_PUBLISHABLE_KEY,
                })
                
        except Exception as e:
            print(f"❌ Error processing booking form: {str(e)}")
            print(f"❌ Environment: {settings.DEBUG}")
            print(f"❌ Database: {settings.DATABASES['default']['ENGINE']}")
            import traceback
            traceback.print_exc()
            
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': f'An error occurred while processing your booking: {str(e)}'
                })
            else:
                # Return form with error message
                form = CleaningBookingForm(request.POST)
                return render(request, "booking/cleaning_booking.html", {
                    "form": form,
                    "cleaning_extras": extras,
                    "service_cat": service_cat,
                    "related_services": related_services,
                    "saved_addresses": saved_addresses,
                    "error_message": f"An error occurred while processing your booking: {str(e)}",
                    "STRIPE_PUBLISHABLE_KEY": settings.STRIPE_PUBLISHABLE_KEY,
                })
    else:
        # Initialize form with user data if logged in
        initial_data = {}
        
        if request.user.is_authenticated:
            initial_data["email"] = request.user.email
            
            if hasattr(request.user, "profile"):
                profile = request.user.profile
                initial_data["name"] = profile.full_name
                initial_data["phone"] = profile.phone
                
                # Pre-fill with first saved address if available
                if saved_addresses.exists():
                    default_address = saved_addresses.first()
                    initial_data.update({
                        "address": default_address.street_address,
                        "apartment": default_address.apt_suite,
                        "zip_code": default_address.zip_code,
                        "city": default_address.city or "New York",
                        "state": default_address.state or "NY",
                    })
        
        form = CleaningBookingForm(initial=initial_data)

    return render(request, "booking/cleaning_booking.html", {
        "form": form,
        "cleaning_extras": extras,
        "service_cat": service_cat,
        "related_services": related_services,
        "saved_addresses": saved_addresses,
        "STRIPE_PUBLISHABLE_KEY": settings.STRIPE_PUBLISHABLE_KEY,
    })

def handyman_booking(request):
    service_cat = ServiceCategory.objects.filter(name__iexact='handyman').first()

    cleaning_category = ServiceCategory.objects.filter(name__iexact='handyman').first()

    related_services = Service.objects.filter(
        category=cleaning_category
    ) if cleaning_category else Service.objects.none()

    # Increment the view count for the service
    # service_cat.view_count += 1
    # service_cat.save(update_fields=["view_count"])

    if request.method == "POST":
        form = HandymanBookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.service_cat = service_cat

            # Save first to set M2M
            booking.save()

            try:
                send_quote_email_handyman(booking)
            except Exception as e:
                print("❌ Email send failed:", e)
            return redirect("quote_submitted_handyman", quote_id=booking.id)
    else:
        form = HandymanBookingForm()
    return render(request, "booking/handyman_booking.html", {"form": form, "service_cat": service_cat, "related_services": related_services})

def office_cleaning_booking(request):
    try:
        print("🏢 Office cleaning booking view started")
        service_cat = ServiceCategory.objects.filter(name__iexact='commercial').first()
        extras = CleaningExtra.objects.all()
        print(f"✅ Service category: {service_cat}")
        print(f"✅ Extras count: {extras.count()}")

        # Get the hourly rate for office cleaning
        from .utils import get_hourly_rate
        hourly_rate = get_hourly_rate('office_cleaning')
        print(f"✅ Hourly rate: {hourly_rate}")
    except Exception as e:
        print(f"❌ Error in office cleaning booking view setup: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

    # Related services for sidebar
    commercial_category = ServiceCategory.objects.filter(name__iexact='commercial').first()
    related_services = (
        Service.objects.filter(category=commercial_category)
        if commercial_category else Service.objects.none()
    )

    if request.method == "POST":
        form = OfficeCleaningBookingForm(request.POST)
        
        # Debug: Print all POST data
        print("🔍 POST data received:")
        for key, value in request.POST.items():
            print(f"   {key}: {value}")
        
        # Check if we have the essential custom form data even if Django form validation fails
        has_essential_data = (
            request.POST.get('business_type') and 
            request.POST.get('crew_size_hours') and 
            request.POST.get('selected_date') and 
            request.POST.get('selected_time')
        )
        
        print(f"🔍 Has essential data: {has_essential_data}")
        print(f"🔍 Form is valid: {form.is_valid()}")
        
        if not form.is_valid():
            print("❌ Django form errors:")
            for field, errors in form.errors.items():
                print(f"   {field}: {errors}")
        
        if not has_essential_data:
            print("❌ Missing essential custom form data:")
            print("   Required: business_type, crew_size_hours, selected_date, selected_time")
            print("   Received:", {
                'business_type': request.POST.get('business_type'),
                'crew_size_hours': request.POST.get('crew_size_hours'),
                'selected_date': request.POST.get('selected_date'),
                'selected_time': request.POST.get('selected_time')
            })
        
        if form.is_valid() or has_essential_data:
            # Create booking object - either from form or manually
            if form.is_valid():
                booking = form.save(commit=False)
            else:
                # Create booking manually when form validation fails
                from .models import Booking
                booking = Booking()
                # Set basic required fields
                booking.name = request.POST.get('name', '')
                booking.email = request.POST.get('email', '')
                booking.phone = request.POST.get('phone', '')
                booking.address = request.POST.get('address', '')
                booking.city = request.POST.get('city', 'New York')
                booking.state = request.POST.get('state', 'NY')
                booking.zip_code = request.POST.get('zip_code', '')
                booking.job_description = request.POST.get('job_description', '')
            
            booking.service_cat = service_cat

            # Handle the new office cleaning specific fields from form and request.POST
            # Priority: Django form data first, then custom HTML form data
            booking.business_type = form.cleaned_data.get('business_type') or request.POST.get('business_type', 'office')
            booking.crew_size_hours = form.cleaned_data.get('crew_size_hours') or request.POST.get('crew_size_hours', '')
            booking.hear_about_us = form.cleaned_data.get('hear_about_us') or request.POST.get('hear_about_us', '')
            cleaning_frequency_from_form = form.cleaned_data.get('cleaning_frequency')
            cleaning_frequency_from_post = request.POST.get('cleaning_frequency', 'one_time')
            print(f"🔍 Cleaning frequency from form: {cleaning_frequency_from_form}")
            print(f"🔍 Cleaning frequency from POST: {cleaning_frequency_from_post}")
            booking.cleaning_frequency = cleaning_frequency_from_form or cleaning_frequency_from_post
            print(f"🔍 Initial cleaning frequency set to: {booking.cleaning_frequency}")
            
            # Extract hours and cleaners from crew_size_hours if available
            if booking.crew_size_hours:
                try:
                    parts = booking.crew_size_hours.split('_')
                    if len(parts) >= 3:
                        # Extract number of cleaners (first part)
                        cleaners_str = parts[0]
                        booking.num_cleaners = int(cleaners_str)
                        
                        # Extract hours from the format like "2_hours" or "2.5_hours"
                        # The format is: {cleaners}_cleaner_{hours}_hours_{sqft}
                        hours_str = parts[2]
                        if 'hours' in hours_str:
                            hours_str = hours_str.replace('hours', '').replace('hour', '')
                        # Handle decimal hours like 2.5
                        if '.' in hours_str:
                            booking.hours_requested = float(hours_str)
                        else:
                            booking.hours_requested = int(hours_str)
                            
                        print(f"✅ Parsed crew_size_hours: {booking.crew_size_hours}")
                        print(f"   - Number of cleaners: {booking.num_cleaners}")
                        print(f"   - Hours requested: {booking.hours_requested}")
                        
                except (ValueError, IndexError) as e:
                    print(f"❌ Error parsing crew_size_hours: {e}")
                    # Try to get values from hidden fields as fallback
                    hidden_cleaners = request.POST.get('num_cleaners')
                    hidden_hours = request.POST.get('hours_requested')
                    
                    if hidden_cleaners:
                        try:
                            booking.num_cleaners = int(hidden_cleaners)
                        except ValueError:
                            booking.num_cleaners = 1
                    else:
                        booking.num_cleaners = 1
                        
                    if hidden_hours:
                        try:
                            booking.hours_requested = float(hidden_hours)
                        except ValueError:
                            booking.hours_requested = 2
                    else:
                        booking.hours_requested = 2
                        
                    print(f"✅ Using hidden field values: cleaners={booking.num_cleaners}, hours={booking.hours_requested}")
            else:
                # Try to get values from hidden fields first
                hidden_cleaners = request.POST.get('num_cleaners')
                hidden_hours = request.POST.get('hours_requested')
                
                if hidden_cleaners:
                    try:
                        booking.num_cleaners = int(hidden_cleaners)
                    except ValueError:
                        booking.num_cleaners = 1
                else:
                    booking.num_cleaners = 1
                    
                if hidden_hours:
                    try:
                        booking.hours_requested = float(hidden_hours)
                    except ValueError:
                        booking.hours_requested = 2
                else:
                    booking.hours_requested = 2
                    
                print(f"✅ Using hidden field values: cleaners={booking.num_cleaners}, hours={booking.hours_requested}")

            # Set date and time
            selected_date = request.POST.get('selected_date')
            selected_time = request.POST.get('selected_time')
            
            if selected_date:
                try:
                    booking.date = datetime.strptime(selected_date, '%Y-%m-%d').date()
                except ValueError:
                    print(f"❌ Invalid date format: {selected_date}")
                    booking.date = date.today() + timedelta(days=2)
            else:
                booking.date = date.today() + timedelta(days=2)
            
            if selected_time:
                try:
                    # Handle time format like "9:00" or "14:00"
                    if ':' in selected_time:
                        hour, minute = map(int, selected_time.split(':'))
                        booking.hour = time(hour, minute)
                    else:
                        # Handle 24-hour format like "900" or "1400"
                        hour = int(selected_time) // 100
                        minute = int(selected_time) % 100
                        booking.hour = time(hour, minute)
                except ValueError:
                    print(f"❌ Invalid time format: {selected_time}")
                    booking.hour = time(9, 0)  # Default to 9:00 AM
            else:
                booking.hour = time(9, 0)  # Default to 9:00 AM

            # Set the cleaning frequency from the form
            cleaning_frequency_from_post = request.POST.get('cleaning_frequency', 'one_time')
            print(f"🔍 Cleaning frequency from POST: {cleaning_frequency_from_post}")
            booking.cleaning_frequency = cleaning_frequency_from_post
            print(f"🔍 Final cleaning frequency set to: {booking.cleaning_frequency}")
            
            # Additional time slot conflict check at view level (same as home cleaning)
            from .utils import check_time_slot_conflict
            if check_time_slot_conflict(booking.date, booking.hour, booking.hours_requested):
                print("❌ Time slot conflict detected at view level")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': 'This time slot is already booked. Please select a different time.'
                    })
                else:
                    # Return form with error message
                    form = OfficeCleaningBookingForm(request.POST)
                    form.add_error('hour', 'This time slot is already booked. Please select a different time.')
                    return render(request, "booking/office_cleaning_booking.html", {
                        "form": form,
                        "extras": extras,
                        "related_services": related_services,
                        "hourly_rate": hourly_rate,
                        "saved_addresses": saved_addresses,
                        "STRIPE_PUBLISHABLE_KEY": settings.STRIPE_PUBLISHABLE_KEY,
                    })

            try:
                # Save the booking first to get an ID
                booking.save()
                print(f"✅ Booking saved with ID: {booking.id}")
                
                # Add extras after booking is saved
                if request.POST.get('extras'):
                    extra_ids = request.POST.getlist('extras')
                    for extra_id in extra_ids:
                        try:
                            extra = CleaningExtra.objects.get(id=extra_id)
                            booking.extras.add(extra)
                            print(f"✅ Added extra: {extra.name}")
                        except (CleaningExtra.DoesNotExist, ValueError):
                            pass
                
                # Calculate price after booking is saved and extras are added
                booking.price = booking.calculate_total_price()
                print(f"✅ Calculated final price: {booking.price}")
                
                # Save again to store the calculated price
                booking.save()
            except ValidationError as e:
                print(f"❌ Validation error saving booking: {str(e)}")
                # Check if this is a time slot conflict (race condition)
                if "This time slot is already booked" in str(e):
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'error': 'This time slot is already booked. Please select a different time.'
                        })
                    else:
                        # Return form with error message
                        form = OfficeCleaningBookingForm(request.POST)
                        form.add_error('hour', 'This time slot is already booked. Please select a different time.')
                        return render(request, "booking/office_cleaning_booking.html", {
                            "form": form,
                            "extras": extras,
                            "related_services": related_services,
                            "hourly_rate": hourly_rate,
                            "saved_addresses": saved_addresses,
                            "STRIPE_PUBLISHABLE_KEY": settings.STRIPE_PUBLISHABLE_KEY,
                        })
                else:
                    # Re-raise other validation errors
                    raise
            except Exception as e:
                print(f"❌ Error saving booking: {str(e)}")
                # Re-raise other errors
                raise
            
            # Calculate individual components for email reporting
            labor_cost = float(hourly_rate) * booking.num_cleaners * booking.hours_requested
            extra_cost = sum(float(extra.price) for extra in booking.extras.all())
            subtotal = labor_cost + extra_cost
            frequency_discount_amount = booking.calculate_frequency_discount_amount()
            tax_rate = 0.08875  # 8.875%
            tax = subtotal * tax_rate
            total = booking.price
            
            print(f"✅ Booking created successfully:")
            print(f"   - ID: {booking.id}")
            print(f"   - Labor cost: ${labor_cost:.2f}")
            print(f"   - Extra cost: ${extra_cost:.2f}")
            print(f"   - Subtotal: ${subtotal:.2f}")
            print(f"   - Tax: ${tax:.2f}")
            print(f"   - Total: ${total:.2f}")
            
            # Send confirmation emails (non-blocking)
            try:
                # Use timeout settings from Django settings
                email_timeout = getattr(settings, 'EMAIL_TIMEOUT', 10)
                print(f"📧 Attempting to send emails with {email_timeout}s timeout...")
                
                email_success = send_office_cleaning_booking_emails(booking, hourly_rate, labor_cost, frequency_discount_amount, subtotal, tax)
                if email_success:
                    print(f"✅ Office cleaning booking emails sent successfully for booking {booking.id}")
                else:
                    print(f"⚠️ Office cleaning booking emails failed for booking {booking.id} (non-critical)")
            except Exception as e:
                print(f"❌ Failed to send office cleaning booking emails for booking {booking.id}: {e}")
                # Continue to redirect even if email fails - emails are non-critical for booking completion
            
            # Check if this is an AJAX request (for Stripe payment)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'booking_id': booking.id,
                    'total_amount': float(booking.price),
                    'calculated_total': float(booking.calculate_total_price()),
                    'redirect_url': f'/quotes/booking/confirmation/{booking.id}/'
                })
            else:
                # Redirect to confirmation page
                return redirect('booking_confirmation', booking_id=booking.id)
        else:
            print("❌ Form validation failed and missing essential data")
            
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Form validation failed and missing essential data',
                    'errors': form.errors if form else {},
                    'non_field_errors': form.non_field_errors() if form else []
                })
            else:
                # Continue to render form with errors
                pass
    else:
        # Initialize form with user data if logged in
        initial_data = {}
        saved_addresses = []

        if request.user.is_authenticated:
            initial_data["email"] = request.user.email

            if hasattr(request.user, "profile"):
                profile = request.user.profile
                initial_data["name"] = profile.full_name
                initial_data["phone"] = profile.phone

                addresses = profile.addresses.all()
                saved_addresses = addresses

                if addresses.exists():
                    default_address = addresses.first()
                    initial_data.update({
                        "address": default_address.street_address,
                        "apartment": default_address.apt_suite,
                        "zip_code": default_address.zip_code,
                        "city": default_address.city or "New York",
                        "state": default_address.state or "NY",
                    })

        form = OfficeCleaningBookingForm(initial=initial_data)

    return render(request, "booking/office_cleaning_booking.html", {
        "form": form,
        "extras": extras,
        "related_services": related_services,
        "hourly_rate": hourly_rate,
        "saved_addresses": saved_addresses,
        "STRIPE_PUBLISHABLE_KEY": settings.STRIPE_PUBLISHABLE_KEY,
    })


def office_cleaning_quote(request):
    """Display and handle office cleaning quote form"""
    # Initialize saved_addresses for authenticated users
    saved_addresses = []
    if request.user.is_authenticated and hasattr(request.user, "profile"):
        saved_addresses = request.user.profile.addresses.all()
    
    if request.method == "POST":
        form = OfficeQuoteForm(request.POST)
        if form.is_valid():
            office_quote = form.save()
            
            # Store additional form data in admin_notes as JSON for later retrieval
            additional_data = {
                'business_type': request.POST.get('business_type', ''),
                'crew_size_hours': request.POST.get('crew_size_hours', ''),
                'hear_about_us': request.POST.get('hear_about_us', ''),
                'cleaning_frequency': request.POST.get('cleaning_frequency', 'one_time'),
                'frequency_discount': request.POST.get('frequency_discount', '0'),
                'selected_date': request.POST.get('selected_date', ''),
                'selected_time': request.POST.get('selected_time', ''),
                'recurrence_pattern': request.POST.get('recurrence_pattern', 'one_time'),
            }
            
            # Store in admin_notes as JSON (will be overwritten if admin adds notes later, but that's acceptable)
            import json
            if not office_quote.admin_notes:
                office_quote.admin_notes = json.dumps(additional_data, indent=2)
                office_quote.save()

            # Send email notification to admin
            try:
                # Parse additional data from admin_notes for email
                date_time_info = ""
                if office_quote.admin_notes:
                    try:
                        additional_data = json.loads(office_quote.admin_notes)
                        selected_date = additional_data.get('selected_date', '')
                        selected_time = additional_data.get('selected_time', '')
                        business_type = additional_data.get('business_type', '')
                        crew_size_hours = additional_data.get('crew_size_hours', '')
                        cleaning_frequency = additional_data.get('cleaning_frequency', '')
                        
                        if selected_date and selected_time:
                            date_time_info = f"""
Scheduling:
- Date: {selected_date}
- Time: {selected_time}
- Cleaning Frequency: {cleaning_frequency or 'N/A'}
"""
                        if business_type:
                            date_time_info += f"- Business Type: {business_type}\n"
                        if crew_size_hours:
                            date_time_info += f"- Crew/Size/Hours: {crew_size_hours}\n"
                    except (json.JSONDecodeError, KeyError):
                        pass
                
                subject = f"New Office Cleaning Quote Request from {office_quote.name}"
                message = f"""
New Office Cleaning Quote Request:

Contact Information:
- Name: {office_quote.name}
- Email: {office_quote.email}
- Phone: {office_quote.phone_number}

Business Details:
- Business Address: {office_quote.business_address}
- Square Footage: {office_quote.square_footage}
{date_time_info}
Job Description:
{office_quote.job_description}

Submitted at: {office_quote.created_at.strftime('%Y-%m-%d %H:%M:%S') if office_quote.created_at else 'N/A'}
Quote ID: {office_quote.id}
"""

                send_mail(
                    subject,
                    message,
                    "noreply@cleanhandy.com",
                    ["support@thecleanhandy.com"],  # Admin email
                    fail_silently=False,
                )
                print(f"✅ Email notification sent to admin for Office Cleaning Quote #{office_quote.id}")
            except Exception as e:
                print(f"❌ Email send failed for Office Cleaning Quote #{office_quote.id}: {e}")

            # Redirect to success page or return JSON for AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Your quote request has been submitted successfully! We will contact you soon.',
                    'quote_id': office_quote.id,
                    'redirect_url': reverse('office_cleaning_quote_submitted', args=[office_quote.id])
                })
            else:
                # For non-AJAX requests, redirect to a success page
                return redirect('office_cleaning_quote_submitted', quote_id=office_quote.id)
    else:
        # Initialize form with user data if logged in
        initial_data = {}
        
        if request.user.is_authenticated:
            # Pre-fill contact information
            initial_data['email'] = request.user.email
            
            if hasattr(request.user, "profile"):
                profile = request.user.profile
                if profile.full_name:
                    initial_data['name'] = profile.full_name
                if profile.phone:
                    initial_data['phone_number'] = profile.phone
                
                # Pre-fill with first saved address if available
                if saved_addresses.exists():
                    default_address = saved_addresses.first()
                    # Store address data in initial_data for JavaScript to use
                    initial_data['_address_street'] = default_address.street_address
                    initial_data['_address_apt'] = default_address.apt_suite or ''
                    initial_data['_address_zip'] = default_address.zip_code
                    initial_data['_address_city'] = default_address.city or 'New York'
                    initial_data['_address_state'] = default_address.state or 'NY'
        
        form = OfficeQuoteForm(initial=initial_data)

    return render(request, "quotes/office_cleaning_quote.html", {
        "form": form,
        "saved_addresses": saved_addresses,
        "user": request.user,
    })

def office_quote_submit(request):
    if request.method == "POST":
        form = OfficeQuoteForm(request.POST)
        if form.is_valid():
            office_quote = form.save()
            
            # Send email notification to admin
            try:
                subject = f"New Office Cleaning Quote Request from {office_quote.name}"
                message = f"""
                New Office Cleaning Quote Request:
                
                Name: {office_quote.name}
                Email: {office_quote.email}
                Phone: {office_quote.phone_number}
                Business Address: {office_quote.business_address}
                Square Footage: {office_quote.square_footage}
                Job Description: {office_quote.job_description}
                
                Submitted at: {office_quote.created_at}
                """
                
                send_mail(
                    subject,
                    message,
                    "noreply@cleanhandy.com",
                    ["support@thecleanhandy.com"],  # Admin email
                    fail_silently=False,
                )
            except Exception as e:
                print(f"❌ Email send failed: {e}")
            
            return JsonResponse({
                'success': True,
                'message': 'Your quote request has been submitted successfully! We will contact you soon.'
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

def terms(request):
    return render(request, "terms.html")

def privacy(request):
    return render(request, "privacy.html")

def faq(request):
    return render(request, "faq.html")


def download_office_cleaning_pdf(request, booking_id):
    """
    Generate and download a PDF for office cleaning quotes
    """
    try:
        # Get the booking
        booking = get_object_or_404(Booking, id=booking_id)
        
        # Get contact info for PDF template
        from .models import ContactInfo
        contact_info = ContactInfo.get_active()
        
        # Render the PDF template
        html_content = render_to_string('quotes/office_cleaning_pdf.html', {
            'booking': booking,
            'contact_info': contact_info
        })
        
        # Generate PDF using weasyprint
        try:
            from weasyprint import HTML, CSS
            from django.conf import settings
            
            # Create PDF from HTML
            pdf = HTML(string=html_content).write_pdf()
            
            # Create HTTP response with PDF
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="office_cleaning_quote_{booking.id}_{booking.name.replace(" ", "_")}.pdf"'
            
            return response
            
        except ImportError:
            # Fallback if weasyprint is not available
            return HttpResponse(
                "PDF generation requires weasyprint. Please install it with: pip install weasyprint",
                content_type='text/plain'
            )
        except Exception as e:
            print(f"❌ PDF generation failed: {e}")
            return HttpResponse(
                f"PDF generation failed: {str(e)}",
                content_type='text/plain'
            )
            
    except Exception as e:
        print(f"❌ Error in download_office_cleaning_pdf: {e}")
        return HttpResponse(
            f"Error generating PDF: {str(e)}",
            content_type='text/plain'
        )


def office_cleaning_quote_submitted(request, quote_id):
    """
    Display the office cleaning quote submitted page
    """
    try:
        from quotes.models import OfficeQuote, ContactInfo
        
        office_quote = get_object_or_404(OfficeQuote, id=quote_id)
        
        # Get contact info for display
        try:
            contact_info = ContactInfo.objects.filter(is_active=True).first()
        except:
            contact_info = None
        
        return render(request, "quotes/office_cleaning_quote_submitted.html", {
            "office_quote": office_quote,
            "contact_info": contact_info,
        })
    except Exception as e:
        print(f"❌ Error in office_cleaning_quote_submitted: {e}")
        return HttpResponse(
            f"Error loading quote: {str(e)}",
            content_type='text/plain'
        )


def booking_confirmation(request, booking_id):
    """
    Display the booking confirmation page for both home and office cleaning bookings
    """
    try:
        booking = get_object_or_404(Booking, id=booking_id)
        
        # Determine which template to use based on service type
        if booking.service_cat.name.lower() == 'commercial' or booking.business_type:
            # Office cleaning confirmation
            template = "quotes/office_cleaning_booking_confirmation.html"
        else:
            # Home cleaning confirmation
            template = "quotes/home_cleaning_booking_confirmation.html"
        
        return render(request, template, {
            "booking": booking
        })
    except Exception as e:
        print(f"❌ Error in booking_confirmation: {e}")
        return HttpResponse(
            f"Error loading booking confirmation: {str(e)}",
            content_type='text/plain'
        )


def handyman_quote_submit(request):
    """Handle handyman quote form submission"""
    if request.method == 'POST':
        form = HandymanQuoteForm(request.POST)
        
        if form.is_valid():
            try:
                # Save the handyman quote
                handyman_quote = form.save()
                
                # Send email notification (optional)
                try:
                    send_mail(
                        'New Handyman Quote Request',
                        f'A new handyman quote request has been submitted by {handyman_quote.name}.\n\n'
                        f'Email: {handyman_quote.email}\n'
                        f'Phone: {handyman_quote.phone_number}\n'
                        f'Address: {handyman_quote.address}\n'
                        f'Job Description: {handyman_quote.job_description}',
                        settings.DEFAULT_FROM_EMAIL,
                        [settings.DEFAULT_FROM_EMAIL],  # Send to admin
                        fail_silently=False,
                    )
                except Exception as e:
                    print(f"❌ Error sending handyman quote email: {e}")
                
                return JsonResponse({
                    'success': True,
                    'message': 'Thank you! Your handyman quote request has been submitted successfully. We will contact you soon with a detailed quote.'
                })
                
            except Exception as e:
                print(f"❌ Error saving handyman quote: {e}")
                return JsonResponse({
                    'success': False,
                    'message': 'An error occurred while submitting your request. Please try again.'
                })
        else:
            # Return form errors
            errors = {}
            for field, field_errors in form.errors.items():
                errors[field] = field_errors[0] if field_errors else 'This field is required.'
            
            return JsonResponse({
                'success': False,
                'message': 'Please correct the errors in the form.',
                'errors': errors
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method.'
    })


def request_post_event_cleaning_quote(request, service_id):
    """Display Post Event Cleaning service detail page with quote form"""
    service = get_object_or_404(Service, id=service_id)

    # Get the 3 most used cleaning services as related services for post event cleaning
    cleaning_category = ServiceCategory.objects.filter(name__iexact='cleaning').first()

    related_services = Service.objects.filter(
        category=cleaning_category
    ).order_by('-view_count')[:3] if cleaning_category else Service.objects.none()

    # Increment the view count for the service
    service.view_count += 1
    service.save()

    return render(request, "quotes/request_post_event_cleaning_quote.html", {
        "service": service,
        "related_services": related_services,
    })


def post_event_cleaning_quote_submit(request):
    """Handle Post Event Cleaning quote form submission"""
    if request.method == 'POST':
        form = PostEventCleaningQuoteForm(request.POST)
        
        if form.is_valid():
            try:
                # Save the post event cleaning quote
                post_event_quote = form.save()
                
                # Send email notification to admin
                try:
                    from django.template.loader import render_to_string
                    from django.core.mail import EmailMessage
                    from django.conf import settings
                    from django.urls import reverse
                    
                    # Generate admin URL
                    admin_url = request.build_absolute_uri(
                        reverse('admin:quotes_posteventcleaningquote_change', args=[post_event_quote.id])
                    )
                    
                    # Render email template
                    admin_html = render_to_string("quotes/email_post_event_cleaning_admin.html", {
                        "quote": post_event_quote,
                        "admin_url": admin_url
                    })
                    
                    # Send email to admin
                    admin_email = EmailMessage(
                        subject=f"🎉 New Post Event Cleaning Quote Request from {post_event_quote.name} - #{post_event_quote.id}",
                        body=admin_html,
                        from_email="support@thecleanhandy.com",
                        to=["support@thecleanhandy.com"],  # Admin email
                    )
                    admin_email.content_subtype = "html"
                    
                    # Send admin email with timeout
                    email_timeout = getattr(settings, 'EMAIL_TIMEOUT', 10)
                    if send_email_with_timeout(admin_email, email_timeout):
                        print(f"✅ Post event cleaning quote email sent to admin for quote #{post_event_quote.id}")
                    else:
                        print(f"❌ Failed to send post event cleaning quote admin email (timeout or connection error)")
                    
                except Exception as email_error:
                    print(f"❌ Failed to send post event cleaning quote email: {email_error}")
                    # Continue execution even if email fails
                
                return JsonResponse({
                    'success': True,
                    'message': 'Your Post Event Cleaning quote request has been submitted successfully!',
                    'quote_id': post_event_quote.id
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'An error occurred: {str(e)}'
                })
        else:
            # Return form errors
            errors = {}
            for field, field_errors in form.errors.items():
                errors[field] = [str(error) for error in field_errors]
            
            # Debug logging
            print(f"❌ Post Event Cleaning form validation failed:")
            print(f"Form data: {request.POST}")
            print(f"Form errors: {form.errors}")
            
            return JsonResponse({
                'success': False,
                'message': 'Please correct the errors in the form.',
                'errors': errors
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method.'
    })


def quote_submitted_post_event_cleaning(request, quote_id):
    """Display confirmation page after Post Event Cleaning quote submission"""
    quote = get_object_or_404(PostEventCleaningQuote, id=quote_id)
    return render(request, "quotes/quote_submitted_post_event_cleaning.html", {"quote": quote})


def home_cleaning_quote_submitted(request, quote_id):
    """Display confirmation page after Home Cleaning quote submission"""
    quote_request = get_object_or_404(HomeCleaningQuoteRequest, id=quote_id)
    return render(request, "quotes/quote_submitted.html", {
        "quote": quote_request  # Pass as quote for template compatibility
    })



