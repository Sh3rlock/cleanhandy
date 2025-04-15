# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import CustomUserRegistrationForm
from django.contrib.auth.decorators import login_required
from .forms import UserForm, CustomerProfileForm
from quotes.forms import CleaningBookingForm, HandymanBookingForm
from .models import CustomerProfile, CustomerAddress
from quotes.models import ServiceCategory, CleaningExtra, Service, Booking
from django.contrib import messages
import json
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from quotes.models import Quote
from customers.models import Customer
from django.shortcuts import get_object_or_404
from quotes.utils import send_quote_email_cleaning
from django.views.decorators.http import require_POST

from .forms import RescheduleBookingForm  # We'll create this next

from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import CustomUserRegistrationForm
from django.contrib.auth.forms import AuthenticationForm

from django.http import JsonResponse
from django.contrib.auth.forms import AuthenticationForm

def register(request):
    if request.method == "POST":
        form = CustomUserRegistrationForm(request.POST)

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            if form.is_valid():
                user = form.save()
                login(request, user)
                return JsonResponse({"success": True})
            else:
                errors = []
                for field_errors in form.errors.values():
                    errors.extend(field_errors)
                return JsonResponse({"success": False, "errors": errors})

        # fallback if not AJAX
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
        else:
            return render(request, "home.html", {
                "register_form": form,
                "login_form": AuthenticationForm()
            })

    return redirect("home")



@login_required
def profile_view(request):
    user = request.user
    profile, created = CustomerProfile.objects.get_or_create(user=user)
    service_cat = ServiceCategory.objects.filter(name__iexact='cleaning').first()

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        profile_form = CustomerProfileForm(request.POST, instance=profile)

        # Extract address inputs from POST
        street_list = request.POST.getlist('addresses[][street_address]')
        apt_list = request.POST.getlist('addresses[][apt_suite]')
        zip_list = request.POST.getlist('addresses[][zip_code]')

        # Prepare errors
        address_errors = []
        for i, (street, zip_code) in enumerate(zip(street_list, zip_list)):
            if not street.strip():
                address_errors.append(f"Address {i + 1}: Street address is required.")
            if not zip_code.strip():
                address_errors.append(f"Address {i + 1}: ZIP code is required.")

        if user_form.is_valid() and profile_form.is_valid() and not address_errors:
            user_form.save()
            profile_form.save()

            # Clear and recreate addresses
            profile.addresses.all().delete()
            for i in range(len(street_list)):
                CustomerAddress.objects.create(
                    profile=profile,
                    street_address=street_list[i],
                    apt_suite=apt_list[i] if apt_list else '',
                    zip_code=zip_list[i]
                )

            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
        else:
            if address_errors:
                for error in address_errors:
                    messages.error(request, error)
            else:
                messages.error(request, 'Please correct the form errors below.')

    user_form = UserForm(instance=user)
    profile_form = CustomerProfileForm(instance=profile)

    return render(request, 'accounts/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile,
        'service_cat': service_cat,

    })

@login_required
def my_bookings(request):
    user_email = request.user.email
    service_cat = ServiceCategory.objects.filter(name__iexact='cleaning').first()

    # Match bookings by email (since Booking has no FK to User/Profile)
    bookings = Booking.objects.filter(email=user_email).order_by("-created_at")

    return render(request, 'accounts/my_bookings.html', {
        'bookings': bookings,
        'service_cat': service_cat,
    })

@login_required
def booking_detail(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    service_cat = ServiceCategory.objects.filter(name__iexact='cleaning').first()

    # Check if the logged-in user's email matches the booking's email
    if booking.email != request.user.email:
        return HttpResponseForbidden("You are not allowed to view this booking.")

    return render(request, 'accounts/booking_detail_user.html', {
        'booking': booking,
        'service_cat': service_cat,
    })


# Booking a service
def booking_submitted_cleaning(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    return render(request, "accounts/booking_submitted_cleaning.html", {
        "booking": booking
    })

def request_cleaning_booking(request, service_cat_id):
    service_cat = get_object_or_404(ServiceCategory, id=service_cat_id)
    extras = CleaningExtra.objects.all()

    # Related services for sidebar
    cleaning_category = ServiceCategory.objects.filter(name__iexact='cleaning').first()
    related_services = (
        Service.objects.filter(category=cleaning_category).exclude(id=service_cat_id)
        if cleaning_category else Service.objects.none()
    )

    if request.method == "GET":
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

        form = CleaningBookingForm(initial=initial_data)


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

            # Server-side price calculation
            booking.price = booking.calculate_total_price()
            booking.save()

            try:
                send_quote_email_cleaning(booking)
            except Exception as e:
                print("❌ Email send failed:", e)

            return redirect("booking_submitted_cleaning", booking_id=booking.id)
        else:
            print("❌ Form errors:", form.errors)
            return HttpResponseBadRequest("Invalid form submission")

    else:
        form = CleaningBookingForm(initial=initial_data)

    return render(request, "accounts/account_cleaning_booking_form.html", {
        "form": form,
        "cleaning_extras": extras,
        "service_cat": service_cat,
        "related_services": related_services,
        "saved_addresses": saved_addresses,
    })


@login_required
def add_customer_address(request):
    if request.method == "POST":
        profile = request.user.profile
        CustomerAddress.objects.create(
            profile=profile,
            street_address=request.POST.get("street_address"),
            apt_suite=request.POST.get("apt_suite"),
            zip_code=request.POST.get("zip_code"),
            city=request.POST.get("city"),
            state=request.POST.get("state")
        )
        return redirect("request_cleaning_booking", service_cat_id=ServiceCategory.objects.get(name__iexact="cleaning").id)
    return HttpResponseBadRequest("Invalid method")

@login_required
def reschedule_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, email=request.user.email)

    if booking.status == 'cancelled':
        messages.warning(request, "You cannot reschedule a cancelled booking.")
        return redirect("my_bookings")

    if request.method == "POST":
        form = RescheduleBookingForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            booking.status = "confirmed"  # Optional: ensure it's still active
            booking.save()
            messages.success(request, "Booking successfully rescheduled.")
            return redirect("booking_detail", booking_id=booking.id)
    else:
        form = RescheduleBookingForm(instance=booking)

    return render(request, "accounts/reschedule_booking.html", {"form": form, "booking": booking})

@require_POST
@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, email=request.user.email)

    if booking.status == 'cancelled':
        messages.info(request, "This booking was already cancelled.")
    else:
        booking.status = 'cancelled'
        booking.save()
        messages.success(request, "Your booking has been cancelled.")

    return redirect("booking_detail", booking_id=booking.id)



