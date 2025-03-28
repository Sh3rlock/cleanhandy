from django.shortcuts import render, redirect
from .models import Quote, Service, CleaningExtra
from customers.models import Customer  # Import Customer from the correct app
from .forms import CleaningQuoteForm, HandymanQuoteForm
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

from django.core.files.base import ContentFile
from weasyprint import HTML
from io import BytesIO
from django.core.mail import EmailMessage


def home(request):
    return render(request, "home.html")  # Make sure to create this template

def send_quote_email_handyman(quote):
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

def send_quote_email_cleaning(quote):
    # Render HTML for PDF
    pdf_html = render_to_string("quotes/quote_pdf.html", {"quote": quote})
    pdf_buffer = BytesIO()
    HTML(string=pdf_html).write_pdf(target=pdf_buffer)
    pdf_buffer.seek(0)

    # Save PDF to model
    filename = f"quote-{quote.id}.pdf"
    quote.pdf_file.save(filename, ContentFile(pdf_buffer.read()), save=True)
    pdf_buffer.seek(0)  # Reset if also attaching to email

    # Send email
    html_message = render_to_string("quotes/email_quote_summary.html", {"quote": quote})
    email = EmailMessage(
        subject="Your Cleaning Quote",
        body=html_message,
        from_email="matyass91@gmail.com",
        to=[quote.customer.email],
    )
    email.content_subtype = "html"
    email.attach(filename, pdf_buffer.read(), "application/pdf")
    email.send()


def request_cleaning_quote(request):
    extras = CleaningExtra.objects.all()

    if request.method == "POST":
        form = CleaningQuoteForm(request.POST)

        if form.is_valid():
            # Get or create customer
            name = request.POST.get("name")
            email = request.POST.get("email")
            phone = request.POST.get("phone")

            customer, created = Customer.objects.get_or_create(email=email, defaults={
                "name": name,
                "phone": phone,
            })

            if not created:
                updated = False
                if customer.name != name:
                    customer.name = name
                    updated = True
                if customer.phone != phone:
                    customer.phone = phone
                    updated = True
                if updated:
                    customer.save()

            # Create quote and link customer
            quote = form.save(commit=False)
            quote.customer = customer
            quote.save()

            # Set M2M fields properly
            quote.home_types_id = request.POST.get("home_types")
            quote.square_feet_options_id = request.POST.get("square_feet_options")  # Set M2M field to selected option
            quote.extras.set(request.POST.getlist("extras"))

            # Now calculate price with all M2M data available
            quote.price = quote.calculate_total_price()
            quote.save()

            # Send email and redirect
            send_quote_email_cleaning(quote)
            return redirect("quote_submitted", quote_id=quote.id)

        else:
            print("❌ Form errors:", form.errors)
            return HttpResponseBadRequest("Invalid form submission")

    else:
        form = CleaningQuoteForm()

    return render(request, "quotes/request_cleaning_quote.html", {
        "form": form,
        "cleaning_extras": extras,
    })



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

            send_quote_email_handyman(quote)
            return redirect("quote_submitted")
    else:
        form = HandymanQuoteForm()
    return render(request, "quotes/request_handyman_quote.html", {"form": form})

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




