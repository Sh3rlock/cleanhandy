# giftcards/utils.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from io import BytesIO
from django.core.mail import EmailMessage
from django.http import HttpRequest
from django.conf import settings
from .models import GiftCard
from decimal import Decimal

def generate_giftcard_pdf(giftcard):
    html_string = render_to_string("giftcards/giftcard_pdf.html", {"giftcard": giftcard})
    pdf_file = BytesIO()
    # WeasyPrint is removed, so this function will now return an empty BytesIO
    # or raise an error if PDF generation is required.
    # For now, we'll return an empty BytesIO as a placeholder.
    return pdf_file

def send_giftcard_email(to_email, giftcard, pdf_file):
    subject = "🎁 You've received a CleanHandy Gift Card!"
    body = (
        f"Hi,\n\n"
        f"You've received a {giftcard.amount}€ gift card for cleaning services.\n"
        f"Gift Card Code: {giftcard.code}\n\n"
        f"The gift card is attached as a PDF.\n\n"
        f"Enjoy!"
    )
    email = EmailMessage(
        subject,
        body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email]
    )
    # pdf_file is expected to be a BytesIO object containing the PDF data.
    # If pdf_file is empty or None, this will raise an error.
    # For now, we'll attach an empty file as a placeholder.
    email.attach(f"giftcard-{giftcard.code}.pdf", pdf_file.read(), "application/pdf")
    email.send()

