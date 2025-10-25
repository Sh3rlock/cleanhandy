# giftcards/utils.py
from io import BytesIO
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from weasyprint import HTML
from django.conf import settings

def generate_giftcard_pdf(giftcard):
    html_string = render_to_string("giftcards/giftcard_pdf.html", {"giftcard": giftcard})
    pdf_file = BytesIO()
    HTML(string=html_string).write_pdf(pdf_file)
    pdf_file.seek(0)
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
    email.attach(f"giftcard-{giftcard.code}.pdf", pdf_file.read(), "application/pdf")
    email.send()

