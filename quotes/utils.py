from datetime import time, timedelta, datetime
from quotes.models import Quote, Booking
from adminpanel.models import BlockedTimeSlot
from datetime import datetime, timedelta, time
from django.http import JsonResponse
from .models import Customer
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from weasyprint import HTML
from io import BytesIO
from django.core.mail import EmailMessage
from django.http import HttpRequest
from django.conf import settings

def get_available_hours_for_date(date, hours_requested=2):
    start_hour = 9
    end_hour = 20
    interval = 30  # minutes
    duration_minutes = max(hours_requested * 60, 120)  # Minimum 2 hours

    # Generate all potential 30-min slots
    all_slots = []
    current = datetime.combine(date, time(hour=start_hour))
    end = datetime.combine(date, time(hour=end_hour))
    while current + timedelta(minutes=duration_minutes) <= end:
        all_slots.append(current.time())
        current += timedelta(minutes=interval)

    # Collect unavailable time ranges
    unavailable_ranges = []
    for quote in Booking.objects.filter(date=date):
        duration = max(quote.hours_requested or 2, 2)
        start = datetime.combine(date, quote.hour)
        end = start + timedelta(hours=duration)
        unavailable_ranges.append((start.time(), end.time()))
    
      # 3. ❌ Exclude admin-blocked slots
    blocked_slots = BlockedTimeSlot.objects.filter(date=date)
    for block in blocked_slots:
        unavailable_ranges.append((block.start_time, block.end_time))

    # Check if each slot fits entirely in available range
    valid_slots = []
    for slot in all_slots:
        start = datetime.combine(date, slot)
        end = start + timedelta(minutes=duration_minutes)

        overlaps = any(
            (start.time() < u_end and end.time() > u_start)
            for u_start, u_end in unavailable_ranges
        )
        if not overlaps:
            valid_slots.append(slot)

    return valid_slots

def send_quote_email_handyman(quote):
    subject = f"Quote Request - {quote.name}"
    text_content = (
        f"New quote request from {quote.name}.\n"
        f"Service: {quote.service_cat}\n"
        f"Date: {quote.date}\n"
        f"Status: {quote.status}\n\n"
        f"Customer Contact:\n"
        f"Name: {quote.name}\n"
        f"Email: {quote.email}\n"
        f"Phone: {quote.phone}\n"
        f"Job Description:{quote.job_description}\n"
    )

    html_content = f"""
    <h2>New Booking Request</h2>
    <p><strong>Customer:</strong> {quote.name}</p>
    <p><strong>Service:</strong> {quote.service_cat}</p>
    <p><strong>Date:</strong> {quote.date}</p>
    <p><strong>Status:</strong> {quote.status}</p>
    <h3>Contact Information</h3>
    <p><strong>Email:</strong> {quote.email}</p>
    <p><strong>Phone:</strong> {quote.phone}</p>
    <h3>Job Description</h3>
    <p>{quote.job_description}</p>
    """

    msg = EmailMultiAlternatives(subject, text_content, "matyass91@gmail.com", [quote.email, "matyass91@gmail.com"])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

from django.conf import settings

def send_quote_email_cleaning(booking):
    # Render PDF HTML and generate PDF
    pdf_html = render_to_string("quotes/quote_pdf.html", {"booking": booking})
    pdf_buffer = BytesIO()
    HTML(string=pdf_html).write_pdf(target=pdf_buffer)
    pdf_buffer.seek(0)

    # Save PDF to model
    filename = f"quote-{booking.id}.pdf"
    booking.pdf_file.save(filename, ContentFile(pdf_buffer.read()), save=True)
    pdf_buffer.seek(0)

    # Email to customer
    html_message = render_to_string("quotes/email_quote_summary.html", {"booking": booking})
    customer_email = EmailMessage(
        subject="Your Cleaning Quote",
        body=html_message,
        from_email="matyass91@gmail.com",
        to=[booking.email],
    )
    customer_email.content_subtype = "html"
    customer_email.attach(filename, pdf_buffer.read(), "application/pdf")
    customer_email.send()

    # Reset PDF buffer for second email
    pdf_buffer.seek(0)

    # Email to admin/staff
    admin_message = render_to_string("quotes/email_quote_admin.html", {"booking": booking})
    admin_email = EmailMessage(
        subject=f"New Cleaning Booking from {booking.name}",
        body=admin_message,
        from_email="matyass91@gmail.com",
        to=[settings.DEFAULT_FROM_EMAIL],  # or use a hardcoded staff email here
    )
    admin_email.content_subtype = "html"
    admin_email.attach(filename, pdf_buffer.read(), "application/pdf")
    admin_email.send()



def process_handyman_quote(form, request, service=None):
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

    quote = form.save(commit=False)
    quote.customer = customer
    if service:
        quote.service = service  # override with selected service
    quote.save()

    send_quote_email_handyman(quote)  # make this customizable if needed
    return quote

def process_cleaning_quote(form, request: HttpRequest, service=None):
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

    quote = form.save(commit=False)
    quote.customer = customer
    quote.save()

    # Set foreign key fields manually (if not handled by form)
    quote.home_types_id = request.POST.get("home_types")
    quote.square_feet_options_id = request.POST.get("square_feet_options")
    if service:
        quote.service = service  # override with selected service
    quote.save()

    # Handle ManyToMany fields
    quote.extras.set(request.POST.getlist("extras"))

    # Calculate and save final price
    quote.price = quote.calculate_total_price()
    quote.save()

    # Send notification
    send_quote_email_cleaning(quote)

    return quote



