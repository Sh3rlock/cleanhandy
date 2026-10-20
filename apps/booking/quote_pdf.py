from fpdf import FPDF

from apps.company.models import get_company


def _text(value):
    cleaned = str(value or "").replace("\u2013", "-").replace("\u2014", "-").replace("\u2022", "-")
    return cleaned.encode("latin-1", "replace").decode("latin-1")


def _money(amount):
    return f"${amount:.2f}"


class _QuotePDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", size=9)
        self.set_text_color(80, 80, 80)
        self.cell(0, 8, f"Page {self.page_no()}", align="C", new_x="LMARGIN", new_y="NEXT")


def _section(pdf, title):
    pdf.ln(2)
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(241, 90, 41)
    pdf.cell(0, 8, _text(title), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(40, 40, 40)
    pdf.set_font("Helvetica", size=11)


def _paragraph(pdf, text):
    if not text:
        return
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(pdf.epw, 6, _text(text), new_x="LMARGIN", new_y="NEXT")


def _money_row(pdf, label, amount):
    pdf.set_x(pdf.l_margin)
    pdf.cell(140, 8, _text(label))
    pdf.cell(0, 8, amount, align="R", new_x="LMARGIN", new_y="NEXT")


def _place(pdf, place):
    street = place.street
    if place.unit:
        street = f"{street}, {place.unit}"
    _paragraph(pdf, f"{place.get_kind_display()}, {place.get_borough_display()}")
    if street.strip():
        _paragraph(pdf, street)
    _paragraph(pdf, place.get_sqft_band_display())


def build_quote_pdf(quote):
    company = get_company()
    pdf = _QuotePDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_text_color(241, 90, 41)
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 10, _text(company.legal_name or "TheCleanHandy"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(40, 40, 40)
    pdf.set_font("Helvetica", size=11)
    phone = company.phone or "(347) 652-6165"
    email = company.public_email or "support@thecleanhandy.com"
    pdf.cell(0, 6, _text(f"{phone}  |  {email}"), new_x="LMARGIN", new_y="NEXT")
    if company.service_area:
        pdf.cell(0, 6, _text(company.service_area), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_draw_color(241, 90, 41)
    pdf.set_line_width(0.6)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 8, _text(f"Quote #{quote.pk}"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=11)
    pdf.cell(0, 6, _text(f"{quote.service.name}  |  {quote.get_status_display()}"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, _text(f"Requested {quote.created_at:%B %d, %Y}"), new_x="LMARGIN", new_y="NEXT")

    _section(pdf, "Customer")
    _paragraph(pdf, quote.contact_name)
    _paragraph(pdf, quote.contact_email)
    _paragraph(pdf, quote.contact_phone)
    if quote.preferred_date:
        _paragraph(pdf, f"Preferred date: {quote.preferred_date:%B %d, %Y}")

    _section(pdf, "Pickup" if quote.destination_id else "Address")
    _place(pdf, quote.property)
    if quote.destination_id:
        _section(pdf, "Drop-off")
        _place(pdf, quote.destination)
    if quote.parking_notes:
        _section(pdf, "Parking instructions")
        _paragraph(pdf, quote.parking_notes)
    if quote.notes:
        _section(pdf, "Customer notes")
        _paragraph(pdf, quote.notes)

    _section(pdf, "Price")
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_x(pdf.l_margin)
    pdf.cell(140, 7, "Option", border="B")
    pdf.cell(0, 7, "Amount", border="B", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=11)
    lines = list(quote.line_items.all())
    if not lines:
        pdf.cell(0, 7, "No priced options were selected.", new_x="LMARGIN", new_y="NEXT")
    for line in lines:
        pdf.set_x(pdf.l_margin)
        pdf.cell(140, 7, _text(line.label))
        pdf.cell(0, 7, _money(line.amount), align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    _money_row(pdf, "Subtotal", _money(quote.subtotal))
    if quote.discount_amount:
        if quote.discount_kind == "percent":
            label = f"Discount ({quote.discount_rate}%)"
        else:
            label = "Discount"
        _money_row(pdf, label, f"-{_money(quote.discount_amount)}")
    _money_row(pdf, f"Tax ({quote.tax_rate}%)", _money(quote.tax_amount))
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(241, 90, 41)
    _money_row(pdf, "Total", _money(quote.total))
    pdf.set_text_color(40, 40, 40)
    pdf.set_font("Helvetica", size=11)

    estimate = getattr(quote, "estimate", None)
    if estimate and estimate.scope:
        _section(pdf, "Scope")
        _paragraph(pdf, estimate.scope)
    if quote.email_note:
        _section(pdf, "Note")
        _paragraph(pdf, quote.email_note)

    pdf.ln(6)
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", size=10)
    pdf.multi_cell(
        pdf.epw,
        5,
        _text(
            "This quote is valid for the details above. Accepting it holds the request for TheCleanHandy to confirm the schedule."
        ),
        new_x="LMARGIN",
        new_y="NEXT",
    )
    return bytes(pdf.output())
