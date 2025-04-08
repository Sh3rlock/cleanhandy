from django.shortcuts import render, redirect
from .models import Quote, Service, CleaningExtra, ServiceCategory, NewsletterSubscriber
from customers.models import Customer  # Import Customer from the correct app
from .forms import CleaningQuoteForm, HandymanQuoteForm, NewsletterForm
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from .utils import get_available_hours_for_date
from django.http import JsonResponse
from datetime import datetime, time, timedelta, date
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

from django.http import HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404

from .utils import process_handyman_quote, process_cleaning_quote
from django.contrib import messages


def home(request):
    cleaning_services =  Service.objects.filter(category__name="Cleaning")
    handyman_services = Service.objects.filter(category__name="Handyman")
    top_services = Service.objects.order_by('-view_count')[:3]

    return render(request, "home.html", {
        "cleaning_services": cleaning_services,
        "handyman_services": handyman_services,
        "top_services": top_services,
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
    extras = CleaningExtra.objects.all()

    # ✅ Get the category object for 'cleaning'
    cleaning_category = ServiceCategory.objects.filter(name__iexact='cleaning').first()

    # ✅ Filter services in the 'cleaning' category, excluding the current one
    related_services = Service.objects.filter(
        category=cleaning_category
    ).exclude(id=service_id) if cleaning_category else Service.objects.none()

    # Increment the view count for the service
    service.view_count += 1
    service.save(update_fields=["view_count"])

    if request.method == "POST":
        form = CleaningQuoteForm(request.POST)

        if form.is_valid():
            quote = process_cleaning_quote(form, request, service=service)
            return redirect("quote_submitted", quote_id=quote.id)
        else:
            print("❌ Form errors:", form.errors)
            return HttpResponseBadRequest("Invalid form submission")
    else:
        form = CleaningQuoteForm(initial={'service': service.id})

    return render(request, "quotes/request_cleaning_quote.html", {
        "form": form,
        "cleaning_extras": extras,
        "service": service,
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
    quote = get_object_or_404(Quote, id=quote_id)
    return render(request, "quotes/quote_submitted_handyman.html", {"quote": quote})

def quote_submitted(request, quote_id):
    quote = get_object_or_404(Quote, id=quote_id)
    return render(request, "quotes/quote_submitted.html", {
        "quote": quote
    })

def cleaning_services(request):
    services = Service.objects.filter(category__name="Cleaning")
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




