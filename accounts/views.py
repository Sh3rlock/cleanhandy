# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import CustomUserRegistrationForm
from django.contrib.auth.decorators import login_required
from .forms import UserForm, CustomerProfileForm
from quotes.forms import CleaningBookingForm, HandymanBookingForm, ReviewForm
from .models import CustomerProfile, CustomerAddress
from quotes.models import ServiceCategory, CleaningExtra, Service, Booking, Review
from django.contrib import messages
import json
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from quotes.models import Quote
from customers.models import Customer
from django.shortcuts import get_object_or_404
from quotes.utils import send_quote_email_cleaning, send_quote_email_handyman
from django.views.decorators.http import require_POST

from .forms import RescheduleBookingForm  # We'll create this next

from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import CustomUserRegistrationForm, CustomLoginForm
from django.contrib.auth.forms import AuthenticationForm

from django.http import JsonResponse
from django.contrib.auth.forms import AuthenticationForm


from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib import messages
from django.urls import reverse

from django.db import IntegrityError, transaction

from django.contrib.auth import authenticate, login

def register(request):
    if request.method == "POST":
        form = CustomUserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Save user but don't commit to DB until password is set
                    user = form.save(commit=False)
                    user.set_password(form.cleaned_data["password1"])
                    user.is_active = False
                    user.save()

                    # Prevent profile duplication
                    CustomerProfile.objects.get_or_create(
                        user=user,
                        defaults={"full_name": user.username}
                    )

                    # Send email confirmation
                    current_site = get_current_site(request)
                    subject = 'Activate your account'
                    message = render_to_string('accounts/activation_email.html', {
                        'user': user,
                        'domain': current_site.domain,
                        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                        'token': default_token_generator.make_token(user),
                    })
                    user.email_user(subject, message)

                    return redirect("activation_pending")
            except IntegrityError:
                messages.error(request, "Something went wrong. Please try again.")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserRegistrationForm()

    return render(request, "accounts/register.html", {"form": form})



def activation_pending(request):
    """Display activation pending page after registration"""
    return render(request, "accounts/activation_pending.html")

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Your account is now active. You can log in.")
        return redirect("login")
    else:
        messages.error(request, "The activation link is invalid or has expired.")
        return redirect("register")
    

def login_view(request):
    if request.method == "POST":
        form = CustomLoginForm(data=request.POST)
        if form.is_valid():
            login_input = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            # First try by username
            user = authenticate(request, username=login_input, password=password)

            # If not found, try by email
            if user is None:
                try:
                    user_obj = User.objects.get(email__iexact=login_input)
                    if not user_obj.is_active:
                        messages.error(request, "Your account is inactive. Please check your email to activate.")
                        return render(request, "accounts/login.html", {"form": form})
                    user = authenticate(request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    user = None

            if user is not None:
                login(request, user)
                messages.success(request, "You are now logged in.")
                return redirect("profile")
            else:
                messages.error(request, "Invalid login credentials.")
    else:
        form = CustomLoginForm()

    return render(request, "accounts/login.html", {"form": form})



@login_required
def profile_view(request):
    user = request.user
    profile, created = CustomerProfile.objects.get_or_create(user=user)
    service_cat = ServiceCategory.objects.filter(name__iexact='home').first()

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
    service_cat = ServiceCategory.objects.filter(name__iexact='home').first()

    # Match bookings by email (since Booking has no FK to User/Profile)
    bookings = Booking.objects.filter(email=user_email).order_by("-created_at")

    return render(request, 'accounts/my_bookings.html', {
        'bookings': bookings,
        'service_cat': service_cat,
    })


@login_required
def booking_detail(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    # Check if the logged-in user's email matches the booking's email
    if booking.email != request.user.email:
        return HttpResponseForbidden("You are not allowed to view this booking.")

    # Handle review form submission
    review_form = ReviewForm()
    review_submitted = False
    if request.method == "POST":
        review_form = ReviewForm(request.POST)
        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.booking = booking
            review.save()
            review_submitted = True
            review_form = ReviewForm()  # Reset form after submission

    # Determine template based on service category
    service_cat_name = booking.service_cat.name.lower() if booking.service_cat else ''

    if service_cat_name == 'home':
        template_name = 'accounts/booking_detail_user.html'
    elif service_cat_name == 'commercial':
        template_name = 'accounts/booking_detail_user.html'  # Same template but with conditional logic
    else:
        template_name = 'accounts/handyman_detail_user.html'

    reviews = booking.reviews.all().order_by('-created_at')

    return render(request, template_name, {
        'booking': booking,
        'service_cat': booking.service_cat,
        'review_form': review_form,
        'review_submitted': review_submitted,
        'reviews': reviews,
    })



# Booking a service
def booking_submitted_cleaning(request, booking_id):
    print(f"🎯 booking_submitted_cleaning view called with booking_id={booking_id}")
    booking = get_object_or_404(Booking, id=booking_id)
    print(f"✅ Booking found: {booking.id} - {booking.name} ({booking.email})")
    return render(request, "accounts/booking_submitted_cleaning.html", {
        "booking": booking
    })

def booking_submitted_handyman(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    return render(request, "accounts/booking_submitted_handyman.html", {
        "booking": booking
    })

def request_cleaning_booking(request):
    service_cat = ServiceCategory.objects.filter(name__iexact='home').first()
    extras = CleaningExtra.objects.all()

    # Related services for sidebar
    home_category = ServiceCategory.objects.filter(name__iexact='home').first()
    related_services = (
        Service.objects.filter(category=home_category)
        if home_category else Service.objects.none()
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

            # Server-side price calculation
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
            return render(request, "accounts/account_cleaning_booking_form.html", {
                "form": form,
                "cleaning_extras": extras,
                "service_cat": service_cat,
                "related_services": related_services,
            })

    else:
        form = CleaningBookingForm(initial=initial_data)

    return render(request, "accounts/account_cleaning_booking_form.html", {
        "form": form,
        "cleaning_extras": extras,
        "service_cat": service_cat,
        "related_services": related_services,
        "saved_addresses": saved_addresses,
    })

def request_handyman_booking(request):
    service_cat = ServiceCategory.objects.filter(name__iexact='handyman').first()

    cleaning_category = ServiceCategory.objects.filter(name__iexact='handyman').first()

    saved_addresses = []

    related_services = Service.objects.filter(
        category=cleaning_category
    ) if cleaning_category else Service.objects.none()

    # Increment the view count for the service
    # service_cat.view_count += 1
    # service_cat.save(update_fields=["view_count"])
    if request.method == "GET":
        initial_data = {}

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

        form = HandymanBookingForm(initial=initial_data)

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
            return redirect("booking_submitted_handyman", booking_id=booking.id)
    else:
        # Merge 'service' into the original initial_data dictionary
        initial_data['service'] = service_cat.id
        form = HandymanBookingForm(initial=initial_data)
    return render(request, "accounts/request_handyman_booking.html", {"form": form, "service_cat": service_cat, "related_services": related_services, "saved_addresses": saved_addresses})



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
        next_url = request.POST.get("next")

        if next_url == reverse("request_cleaning_booking"):
            return redirect("request_cleaning_booking")
        else:
            return redirect("profile")
        
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

def help(request):
    service_cat = ServiceCategory.objects.filter(name__iexact='home').first()
    return render(request, "accounts/help.html", {
        "service_cat": service_cat,
    })


from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse

@ensure_csrf_cookie
def refresh_csrf_token(request):
    """Refresh CSRF token for AJAX requests"""
    return JsonResponse({'status': 'success'})


from django.core.mail import send_mail
from django.conf import settings

def test_email(request):
    """Test email functionality"""
    if not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': 'Access denied'})
    
    try:
        send_mail(
            'Test Email from CleanHandy',
            'This is a test email to verify email functionality is working correctly.',
            settings.DEFAULT_FROM_EMAIL,
            [request.user.email],
            fail_silently=False,
        )
        return JsonResponse({
            'status': 'success', 
            'message': f'Test email sent successfully to {request.user.email}'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error', 
            'message': f'Failed to send test email: {str(e)}'
        })


def csrf_debug(request):
    """Debug CSRF token issues"""
    from django.middleware.csrf import get_token
    
    if request.method == 'GET':
        # Get fresh CSRF token
        csrf_token = get_token(request)
        return JsonResponse({
            'csrf_token': csrf_token,
            'cookies': dict(request.COOKIES),
            'session_key': request.session.session_key,
            'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            'status': 'success'
        })
    elif request.method == 'POST':
        # Test CSRF validation
        return JsonResponse({
            'status': 'success',
            'message': 'CSRF token is valid',
            'csrf_token': request.POST.get('csrfmiddlewaretoken', 'Not provided')
        })


def debug_booking_calculation(request):
    """Debug booking price calculation"""
    if not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': 'Access denied'})
    
    try:
        from quotes.models import Booking, ServiceCategory, SquareFeetOption, HomeType, CleaningExtra
        
        # Create a test booking
        service_cat = ServiceCategory.objects.filter(name__iexact='home').first()
        if not service_cat:
            return JsonResponse({'status': 'error', 'message': 'No home service category found'})
        
        # Get sample data
        square_feet_option = SquareFeetOption.objects.first()
        home_type = HomeType.objects.first()
        
        booking = Booking(
            service_cat=service_cat,
            square_feet_options=square_feet_option,
            home_types=home_type,
            hours_requested=3,
            num_cleaners=2
        )
        
        # Test calculations
        is_large = booking.is_large_home()
        subtotal = booking.calculate_subtotal()
        tax = booking.calculate_tax()
        total = booking.calculate_total_price()
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'service_cat': str(service_cat),
                'square_feet_option': str(square_feet_option) if square_feet_option else 'None',
                'home_type': str(home_type) if home_type else 'None',
                'is_large_home': is_large,
                'subtotal': float(subtotal),
                'tax': float(tax),
                'total': float(total),
                'hours_requested': float(booking.hours_requested) if booking.hours_requested else None,
                'num_cleaners': booking.num_cleaners
            }
        })
        
    except Exception as e:
        import traceback
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        })


def debug_form_validation(request):
    """Debug form validation with test data"""
    if not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': 'Access denied'})
    
    try:
        from quotes.forms import CleaningBookingForm
        from quotes.models import ServiceCategory
        
        # Get service category
        service_cat = ServiceCategory.objects.filter(name__iexact='home').first()
        if not service_cat:
            return JsonResponse({'status': 'error', 'message': 'No home service category found'})
        
        # Test data similar to the actual form submission
        test_data = {
            'service_cat': service_cat.id,
            'hours_requested': 5,
            'num_cleaners': 2,
            'cleaning_type': '1000-1500 (Regular)',
            'date': '2025-09-24',
            'hour': '09:00',
            'square_feet_options': 1,
            'home_types': 2,
            'bath_count': 2,
            'extras': [1, 2, 6],
            'name': 'Test User',
            'email': 'test@example.com',
            'phone': '1234567890',
            'address': 'Test Address',
            'apartment': '7',
            'zip_code': '53560',
            'city': 'New York',
            'state': 'NY',
            'get_in': 'call_organize',
            'parking': 'Garage',
            'pet': 'cat',
            'cleaning_frequency': 'bi_weekly',
            'frequency_discount': '10',
            'selected_date': '2025-09-24',
            'selected_time': '09:00',
            'recurrence_pattern': 'one_time',
            'job_description': 'Test cleaning job',
            'gift_card_code': ''
        }
        
        # Test form validation
        form = CleaningBookingForm(test_data)
        is_valid = form.is_valid()
        
        result = {
            'status': 'success' if is_valid else 'error',
            'is_valid': is_valid,
            'errors': dict(form.errors),
            'non_field_errors': form.non_field_errors(),
            'cleaned_data': form.cleaned_data if is_valid else None,
            'test_data': test_data
        }
        
        return JsonResponse(result)
        
    except Exception as e:
        import traceback
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        })

