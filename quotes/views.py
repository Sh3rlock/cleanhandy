from django.shortcuts import render, redirect
from .models import Quote, Service
from .forms import QuoteForm
from django.core.mail import send_mail

def home(request):
    return render(request, "home.html")  # Make sure to create this template

def send_quote_email(quote):
    subject = f"Quote Request - {quote.name}"
    message = f"New quote request from {quote.name}.\nService: {quote.service}\nDate: {quote.date}\nStatus: {quote.status}"
    
    send_mail(subject, message, "matyass91@gmail.com", [quote.email, "matyass91@gmail.com"])

def request_quote(request):
    if request.method == "POST":
        form = QuoteForm(request.POST)
        if form.is_valid():
            quote = form.save()
            send_quote_email(quote)  # Send email
            return redirect("quote_submitted")  # Redirect after submission
    else:
        form = QuoteForm()
    
    return render(request, "quotes/request_quote.html", {"form": form})

def quote_submitted(request):
    return render(request, "quotes/quote_submitted.html")

def cleaning_services(request):
    services = Service.objects.filter(category__name="Cleaning")
    return render(request, "quotes/cleaning_services.html", {"services": services})

def handyman_services(request):
    services = Service.objects.filter(category__name="Handyman")
    return render(request, "quotes/handyman_services.html", {"services": services})