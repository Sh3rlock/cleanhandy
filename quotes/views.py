from django.shortcuts import render, redirect
from .models import Quote, Service
from customers.models import Customer  # Import Customer from the correct app
from .forms import CleaningQuoteForm, HandymanQuoteForm
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from .utils import get_available_hours_for_date
from django.http import JsonResponse
from datetime import datetime, time, timedelta, date


def home(request):
    return render(request, "home.html")  # Make sure to create this template

def send_quote_email(quote):
    subject = f"Quote Request - {quote.customer.name}"
    text_content = (
        f"New quote request from {quote.customer.name}.\n"
        f"Service: {quote.service}\n"
        f"Date: {quote.date}\n"
        f"Status: {quote.status}\n\n"
        f"Customer Contact:\n"
        f"Name: {quote.customer.name}\n"
        f"Email: {quote.customer.email}\n"
        f"Phone: {quote.customer.phone}"
    )

    html_content = f"""
    <h2>New Quote Request</h2>
    <p><strong>Customer:</strong> {quote.customer.name}</p>
    <p><strong>Service:</strong> {quote.service}</p>
    <p><strong>Date:</strong> {quote.date}</p>
    <p><strong>Status:</strong> {quote.status}</p>
    <h3>Contact Information</h3>
    <p><strong>Email:</strong> {quote.customer.email}</p>
    <p><strong>Phone:</strong> {quote.customer.phone}</p>
    """

    msg = EmailMultiAlternatives(subject, text_content, "matyass91@gmail.com", [quote.customer.email, "matyass91@gmail.com"])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

def save_customer(name, email, phone):
    customer, created = Customer.objects.get_or_create(email=email, defaults={"name": name, "phone": phone})
    
    print(f"Customer {'Created' if created else 'Found'}: {customer.name} ({customer.email})")  # Debugging

    return customer


def request_cleaning_quote(request):
    if request.method == "POST":
        form = CleaningQuoteForm(request.POST)
        if form.is_valid():
            # Get customer details from request
            name = request.POST.get("name")
            email = request.POST.get("email")
            phone = request.POST.get("phone")

            # Save customer
            customer = save_customer(name, email, phone)

            # Create quote and link to customer
            quote = form.save(commit=False)
            quote.customer = customer
            quote.save()

            send_quote_email(quote)
            return redirect("quote_submitted")
    else:
        form = CleaningQuoteForm()
    return render(request, "quotes/request_cleaning_quote.html", {"form": form})

def request_handyman_quote(request):
    if request.method == "POST":
        form = HandymanQuoteForm(request.POST)
        if form.is_valid():
            # Get customer details from request
            name = request.POST.get("name")
            email = request.POST.get("email")
            phone = request.POST.get("phone")

            # Save customer
            customer = save_customer(name, email, phone)

            # Create quote and link to customer
            quote = form.save(commit=False)
            quote.customer = customer
            quote.save()

            send_quote_email(quote)
            return redirect("quote_submitted")
    else:
        form = HandymanQuoteForm()
    return render(request, "quotes/request_handyman_quote.html", {"form": form})

def quote_submitted(request):
    return render(request, "quotes/quote_submitted.html")

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

