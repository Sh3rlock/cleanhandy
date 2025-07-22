from django.shortcuts import render, redirect
from .models import Quote, Service, CleaningExtra, ServiceCategory, NewsletterSubscriber, Booking
from customers.models import Customer  # Import Customer from the correct app
from .forms import CleaningQuoteForm, HandymanQuoteForm, NewsletterForm, CleaningBookingForm, HandymanBookingForm
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from .utils import get_available_hours_for_date, send_quote_email_cleaning
from django.http import JsonResponse
from datetime import datetime, time, timedelta, date
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

from django.http import HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404

from .utils import process_handyman_quote, send_quote_email_handyman
from django.contrib import messages

from giftcards.models import GiftCard

from django.contrib.auth.forms import AuthenticationForm
from accounts.forms import CustomUserRegistrationForm, CustomLoginForm  # your custom register form
from django.contrib.auth import login


def home(request):
    cleaning_services =  Service.objects.filter(category__name="Cleaning")
    handyman_services = Service.objects.filter(category__name="Handyman")
    top_services = Service.objects.order_by('-view_count')[:3]

    return render(request, "home.html", {
        "cleaning_services": cleaning_services,
        "handyman_services": handyman_services,
        "top_services": top_services,
        "login_form": CustomLoginForm(),
        "register_form": CustomUserRegistrationForm(),
    })

def about(request):
    services = Service.objects.all()
    return render(request, "about.html", {
        "services": services,
    })

def contact(request): 
    return render(request, "contact.html")

def blog(request):
    return render(request, "blog.html")

def blog_detail(request):
    return render(request, "blog_detail.html")

def request_cleaning_quote(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    all_services = Service.objects.all()

    # Get related services in the Cleaning category (for suggestion sidebar)
    cleaning_category = ServiceCategory.objects.filter(name__iexact='cleaning').first()
    related_services = (
        Service.objects.filter(category=cleaning_category).exclude(id=service_id)
        if cleaning_category else Service.objects.none()
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

def cleaning_services(request):
    services = Booking.objects.filter(category__name="Cleaning")
    return render(request, "quotes/cleaning_services.html", {"services": services})

def handyman_services(request):
    services = Service.objects.filter(category__name="Handyman")
    return render(request, "quotes/handyman_services.html", {"services": services})

def available_hours_api(request):
    date_str = request.GET.get("date")
    hours = int(request.GET.get("hours", 2))  # get from query param or default 2
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid date"}, status=400)

    available = get_available_hours_for_date(date, hours_requested=hours)
    formatted = [slot.strftime("%H:%M") for slot in available]
    return JsonResponse({"available_hours": formatted})


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
    service_cat = get_object_or_404(ServiceCategory, id=service_cat_id)
    extras = CleaningExtra.objects.all()

    # Get related services in the Cleaning category (for suggestion sidebar)
    cleaning_category = ServiceCategory.objects.filter(name__iexact='cleaning').first()
    related_services = (
        Service.objects.filter(category=cleaning_category).exclude(id=service_cat_id)
        if cleaning_category else Service.objects.none()
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
            except Exception as e:
                print("❌ Email send failed:", e)
                return redirect("quote_submitted", booking_id=booking.id)
            else:
                print("❌ Form errors:", form.errors)
                return HttpResponseBadRequest("Invalid form submission")
    else:
        form = CleaningBookingForm(initial={'service': booking.id})

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
    service_cat = ServiceCategory.objects.filter(name__iexact='cleaning').first()
    extras = CleaningExtra.objects.all()

    # Related services for sidebar
    cleaning_category = ServiceCategory.objects.filter(name__iexact='cleaning').first()
    related_services = (
        Service.objects.filter(category=cleaning_category)
        if cleaning_category else Service.objects.none()
    )


    if request.method == "POST":
        form = CleaningBookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.service_cat = service_cat

            # Save first to set M2M
            booking.save()

            selected_extra_ids = request.POST.getlist("extras")
            if selected_extra_ids:
                selected_extras = CleaningExtra.objects.filter(id__in=selected_extra_ids)
                booking.extras.set(selected_extras)

            # --- Handle Gift Card or Discount Code ---
            code_data = form.cleaned_data.get("gift_card_code")

            if code_data:
                code_type, code_obj = code_data

                if code_type == "giftcard":
                    booking.gift_card = code_obj
                    booking.gift_card_discount = min(code_obj.balance, booking.calculate_total_price())

                elif code_type == "discount":
                    if code_obj.discount_type == "fixed":
                        booking.gift_card_discount = min(code_obj.value, booking.calculate_total_price())
                    elif code_obj.discount_type == "percent":
                        booking.gift_card_discount = booking.calculate_total_price() * (code_obj.value / 100)
                    code_obj.times_used += 1
                    code_obj.save()

            # Final price after discount
            booking.price = booking.calculate_total_price()
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
            except Exception as e:
                print("❌ Email send failed:", e)

            return redirect("booking_submitted_cleaning", booking_id=booking.id)

        else:
            print("❌ Form errors:", form.errors)
            return render(request, "booking/cleaning_booking.html", {
                "form": form,
                "cleaning_extras": extras,
                "service_cat": service_cat,
                "related_services": related_services,
            })
    else:
        form = CleaningBookingForm()


    return render(request, "booking/cleaning_booking.html", {
        "form": form,
        "cleaning_extras": extras,
        "service_cat": service_cat,
        "related_services": related_services,
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


def terms(request):
    return render(request, "terms.html")

def privacy(request):
    return render(request, "privacy.html")

def faq(request):
    return render(request, "faq.html")



