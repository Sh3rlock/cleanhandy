from datetime import date, timedelta
from decimal import Decimal

from django import forms
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.accounts.models import User
from apps.booking.forms import QuotePropertyForm
from apps.booking.models import Job, PriceVariable, PriceVariableCategory, Property, QuoteEstimate, QuoteLineItem, QuoteRequest, TaxSettings
from apps.booking.pricing import calculate_quote, discount_for_selection, normalize_selection, service_needs_destination
from apps.booking.quote_prices import seed_quote_prices
from apps.content.models import ServicePage


class QuoteMathTests(TestCase):
    def test_discount_and_tax(self):
        totals = calculate_quote([Decimal("450"), Decimal("0")], Decimal("45.00"), Decimal("8.875"))
        self.assertEqual(totals["subtotal"], Decimal("450.00"))
        self.assertEqual(totals["discount_amount"], Decimal("45.00"))
        self.assertEqual(totals["tax_amount"], Decimal("35.94"))
        self.assertEqual(totals["total"], Decimal("440.94"))

    def test_discount_cannot_exceed_subtotal(self):
        totals = calculate_quote([Decimal("100")], Decimal("250"), Decimal("8.875"))
        self.assertEqual(totals["discount_amount"], Decimal("100.00"))
        self.assertEqual(totals["tax_amount"], Decimal("0.00"))
        self.assertEqual(totals["total"], Decimal("0.00"))

    def test_inactive_tax_rate_is_zero(self):
        TaxSettings.objects.create(tax_rate=Decimal("8.875"), is_active=False)
        self.assertEqual(TaxSettings.get_tax_rate(), Decimal("0"))


class QuoteFlowTests(TestCase):
    def setUp(self):
        self.service = ServicePage.objects.create(
            name="Apartment Moving",
            slug="apartment-moving-nyc",
            category=ServicePage.Category.MOVING,
            short_description="Apartment moves.",
        )
        self.other = ServicePage.objects.create(
            name="Assembly",
            slug="assembly",
            category=ServicePage.Category.ADDITIONAL,
            short_description="Assembly.",
        )
        seed_quote_prices()
        self.customer = User.objects.create_user(email="ada@example.com", password="password123")
        self.staff = User.objects.create_user(
            email="staff@example.com",
            password="password123",
            is_staff=True,
            role=User.Role.STAFF,
        )

    def test_other_service_options_are_ignored(self):
        foreign = PriceVariable.objects.filter(category__slug="assembly-size").first()
        chosen = normalize_selection(self.service, [foreign.pk])
        self.assertEqual(chosen, [])

    def test_moving_form_asks_for_dropoff_and_hides_price_until_confirm(self):
        self.assertTrue(service_needs_destination(self.service))
        self.assertFalse(service_needs_destination(self.other))
        form = QuotePropertyForm(service=self.service)
        data = {
            "borough": "manhattan",
            "kind": "apartment",
            "sqft_band": "under-1000",
            "street": "1 Main St",
            "dest_borough": "brooklyn",
            "dest_kind": "apartment",
            "dest_sqft_band": "1000-1500",
            "dest_street": "2 Main St",
            "parking_notes": "Garage on the left",
        }
        for field in form.option_fields():
            if isinstance(field.field, forms.MultipleChoiceField):
                continue
            data[field.name] = field.field.choices[0][0]
        start = self.client.post(reverse("quote_start"), {"service": self.service.pk})
        self.assertEqual(start.status_code, 302)
        details_page = self.client.get(reverse("quote_property"))
        self.assertContains(details_page, "Studio")
        self.assertContains(details_page, "Walk-up, 1 flight")
        self.assertContains(details_page, "Preferred day")
        self.assertContains(details_page, 'type="date"')
        self.assertNotContains(details_page, "$")
        self.assertNotContains(details_page, "% off")
        past = dict(data)
        past["preferred_date"] = (date.today() - timedelta(days=1)).isoformat()
        rejected = self.client.post(reverse("quote_property"), past)
        self.assertEqual(rejected.status_code, 200)
        self.assertContains(rejected, "Choose today or a later day.")
        chosen = date.today() + timedelta(days=3)
        data["preferred_date"] = chosen.isoformat()
        details = self.client.post(reverse("quote_property"), data)
        self.assertEqual(details.status_code, 302, details.content)
        contact = self.client.post(
            reverse("quote_contact"),
            {
                "contact_name": "Ada Lovelace",
                "contact_email": "ada@example.com",
                "contact_phone": "2125550100",
            },
        )
        self.assertRedirects(contact, reverse("quote_done"))
        quote = QuoteRequest.objects.get()
        self.assertEqual(quote.status, QuoteRequest.Status.REQUESTED)
        self.assertFalse(QuoteEstimate.objects.filter(quote=quote).exists())
        self.assertEqual(quote.destination.borough, "brooklyn")
        self.assertEqual(quote.subtotal, Decimal("450.00"))
        self.assertEqual(quote.total, Decimal("489.94"))
        self.assertEqual(quote.parking_notes, "Garage on the left")
        self.assertEqual(quote.preferred_date, chosen)
        parking = quote.line_items.get(label__startswith="Parking:")
        self.assertEqual(parking.amount, Decimal("0.00"))
        done = self.client.get(reverse("quote_done"))
        self.assertContains(done, "confirm the price")
        self.assertContains(done, "Preferred day")
        self.assertNotContains(done, "489.94")

        quote.user = self.customer
        quote.save(update_fields=["user"])
        self.client.login(username="ada@example.com", password="password123")
        account = self.client.get(reverse("account_home"))
        self.assertContains(account, "Waiting for staff to confirm the price")
        self.assertNotContains(account, "Accept quote")
        self.client.logout()

        self.assertEqual(self.client.get(reverse("staff_quotes")).status_code, 302)
        self.client.login(username="ada@example.com", password="password123")
        self.assertEqual(self.client.get(reverse("staff_quotes")).status_code, 403)
        self.client.logout()

        self.client.login(username="staff@example.com", password="password123")
        desk = self.client.get(reverse("staff_quotes"))
        self.assertContains(desk, "489.94")
        post = {"discount_kind": "amount", "discount_value": "0", "action": "confirm"}
        for line in quote.line_items.all():
            post[f"amount_{line.pk}"] = str(line.amount)
        saved = self.client.post(reverse("staff_quote_detail", args=[quote.pk]), post)
        self.assertRedirects(saved, reverse("staff_quote_detail", args=[quote.pk]))
        quote.refresh_from_db()
        self.assertEqual(quote.status, QuoteRequest.Status.QUOTED)
        self.assertEqual(quote.estimate.price, quote.total)
        self.client.logout()

        self.client.login(username="ada@example.com", password="password123")
        account = self.client.get(reverse("account_home"))
        self.assertContains(account, "Accept quote")
        self.assertContains(account, "489.94")

    def test_single_choice_categories_exist_for_each_family(self):
        self.assertTrue(PriceVariableCategory.objects.filter(slug="parking").exists())
        self.assertTrue(PriceVariableCategory.objects.filter(slug="cleaning-bathrooms").exists())
        self.assertTrue(PriceVariableCategory.objects.filter(slug="commercial-frequency").exists())
        weekly = PriceVariable.objects.get(category__slug="commercial-frequency", name="Weekly")
        self.assertEqual(weekly.discount_kind, "percent")
        self.assertEqual(weekly.discount_percent, Decimal("10.00"))
        dollars, kind, rate = discount_for_selection([weekly], Decimal("250"))
        self.assertEqual((dollars, kind, rate), (Decimal("25.00"), "percent", Decimal("10.00")))

    def test_staff_can_discount_by_amount_or_percent(self):
        prop = Property.objects.create(borough="manhattan", kind="apartment", sqft_band="under-1000", street="1 Main St")
        quote = QuoteRequest.objects.create(
            service=self.service,
            property=prop,
            contact_name="Ada Lovelace",
            contact_email="ada@example.com",
            contact_phone="2125550100",
            subtotal=Decimal("450.00"),
        )
        line = QuoteLineItem.objects.create(quote=quote, label="Studio", amount=Decimal("450.00"))
        self.client.login(username="staff@example.com", password="password123")
        saved = self.client.post(
            reverse("staff_quote_detail", args=[quote.pk]),
            {
                "discount_kind": "percent",
                "discount_value": "10",
                "action": "save",
                f"amount_{line.pk}": "450.00",
            },
        )
        self.assertRedirects(saved, reverse("staff_quote_detail", args=[quote.pk]))
        quote.refresh_from_db()
        self.assertEqual(quote.discount_kind, "percent")
        self.assertEqual(quote.discount_rate, Decimal("10.00"))
        self.assertEqual(quote.discount_amount, Decimal("45.00"))
        self.assertEqual(quote.tax_amount, Decimal("35.94"))
        self.assertEqual(quote.total, Decimal("440.94"))

        weekly = PriceVariable.objects.get(category__slug="commercial-frequency", name="Weekly")
        weekly.discount_kind = "amount"
        weekly.discount_amount = Decimal("40.00")
        weekly.discount_percent = Decimal("0")
        dollars, kind, rate = discount_for_selection([weekly], Decimal("250"))
        self.assertEqual((dollars, kind, rate), (Decimal("40.00"), "amount", Decimal("0.00")))

    def test_confirmed_quote_email_accepts_and_pdf_downloads(self):
        from django.core import mail

        from apps.booking.quote_actions import accept_token

        prop = Property.objects.create(borough="manhattan", kind="apartment", sqft_band="under-1000", street="1 Main St")
        quote = QuoteRequest.objects.create(
            service=self.service,
            property=prop,
            contact_name="Ada Lovelace",
            contact_email="ada@example.com",
            contact_phone="2125550100",
            subtotal=Decimal("450.00"),
            tax_rate=Decimal("8.875"),
            tax_amount=Decimal("39.94"),
            total=Decimal("489.94"),
            parking_notes="Garage on the left",
        )
        QuoteLineItem.objects.create(quote=quote, label="Studio", amount=Decimal("450.00"))
        self.client.login(username="staff@example.com", password="password123")
        too_early = self.client.post(reverse("staff_send_quote_email", args=[quote.pk]), {"email_note": "Soon"})
        self.assertRedirects(too_early, reverse("staff_quote_detail", args=[quote.pk]))
        self.assertEqual(len(mail.outbox), 0)

        QuoteEstimate.objects.create(quote=quote, price=quote.total, scope="Studio apartment move", created_by=self.staff)
        sent = self.client.post(
            reverse("staff_send_quote_email", args=[quote.pk]),
            {"email_note": "The elevator is reserved."},
        )
        self.assertRedirects(sent, reverse("staff_quote_detail", args=[quote.pk]))
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ["ada@example.com"])
        self.assertIn("489.94", message.body)
        self.assertIn("The elevator is reserved.", message.body)
        self.assertIn(reverse("quote_email_accept", args=[quote.pk, accept_token(quote)]), message.body)
        self.assertEqual(len(message.alternatives), 1)
        self.assertIn("Accept offer", message.alternatives[0][0])
        quote.refresh_from_db()
        self.assertIsNotNone(quote.quote_email_sent_at)
        detail = self.client.get(reverse("staff_quote_detail", args=[quote.pk]))
        self.assertContains(detail, "Send quote email")
        self.assertContains(detail, "Download PDF")

        pdf = self.client.get(reverse("staff_quote_pdf", args=[quote.pk]))
        self.assertEqual(pdf["Content-Type"], "application/pdf")
        self.assertTrue(pdf.content.startswith(b"%PDF"))
        self.assertGreater(len(pdf.content), 500)
        self.client.logout()

        self.client.login(username="ada@example.com", password="password123")
        self.assertEqual(self.client.get(reverse("staff_quote_pdf", args=[quote.pk])).status_code, 403)
        self.client.logout()

        bad = self.client.get(reverse("quote_email_accept", args=[quote.pk, "not-a-token"]))
        self.assertEqual(bad.status_code, 403)

        accepted = self.client.get(reverse("quote_email_accept", args=[quote.pk, accept_token(quote)]))
        self.assertContains(accepted, "Quote accepted")
        quote.refresh_from_db()
        self.assertEqual(quote.status, QuoteRequest.Status.SCHEDULED)
        self.assertEqual(quote.job.scheduled_date, quote.preferred_date)
        self.assertEqual(len(mail.outbox), 2)

    @override_settings(STRIPE_SECRET_KEY="sk_test_example", STRIPE_WEBHOOK_SECRET="whsec_example")
    def test_quote_email_includes_deposit_and_full_payment_links(self):
        from unittest.mock import patch

        from django.core import mail

        from apps.booking.models import QuotePayment
        from apps.booking.payments import record_checkout_session, split_amounts

        self.assertEqual(split_amounts(Decimal("489.94")), (Decimal("244.97"), Decimal("244.97")))
        prop = Property.objects.create(borough="queens", kind="apartment", sqft_band="under-1000", street="4 Oak St")
        quote = QuoteRequest.objects.create(
            service=self.service,
            property=prop,
            contact_name="Ada Lovelace",
            contact_email="ada@example.com",
            contact_phone="2125550100",
            status=QuoteRequest.Status.QUOTED,
            total=Decimal("489.94"),
        )
        QuoteEstimate.objects.create(quote=quote, price=quote.total, scope="Studio move")

        class FakeLink:
            def __init__(self, kind):
                self.id = f"plink_{kind}"
                self.url = f"https://buy.stripe.com/{kind}"

        def fake_create(**kwargs):
            return FakeLink(kwargs["metadata"]["payment_type"])

        self.client.login(username="staff@example.com", password="password123")
        with patch("apps.booking.payments.stripe.PaymentLink.create", side_effect=fake_create):
            sent = self.client.post(reverse("staff_send_quote_email", args=[quote.pk]), {"email_note": ""})
        self.assertRedirects(sent, reverse("staff_quote_detail", args=[quote.pk]))
        body = mail.outbox[0].body
        self.assertIn("https://buy.stripe.com/deposit", body)
        self.assertIn("https://buy.stripe.com/full", body)
        self.assertIn("244.97", body)
        self.assertIn("489.94", body)
        html = mail.outbox[0].alternatives[0][0]
        self.assertIn("Pay 50% deposit", html)
        self.assertIn("Pay full amount", html)
        deposit = quote.payments.get(kind=QuotePayment.Kind.DEPOSIT)
        self.assertEqual(deposit.amount, Decimal("244.97"))

        with patch("apps.booking.payments.stripe.PaymentLink.modify") as modify:
            record_checkout_session({"id": "cs_test", "payment_link": deposit.stripe_payment_link_id, "metadata": {}})
        deposit.refresh_from_db()
        self.assertEqual(deposit.status, QuotePayment.Status.PAID)
        modify.assert_called_once()
        self.assertEqual(self.client.get(reverse("quote_payment_received", args=[quote.pk])).status_code, 200)

    def test_email_decline_does_not_schedule_the_job(self):
        from apps.booking.quote_actions import decline_token

        prop = Property.objects.create(borough="brooklyn", kind="apartment", sqft_band="under-1000", street="9 Oak St")
        quote = QuoteRequest.objects.create(
            service=self.service,
            property=prop,
            contact_name="Ada Lovelace",
            contact_email="ada@example.com",
            contact_phone="2125550100",
            status=QuoteRequest.Status.QUOTED,
            total=Decimal("100.00"),
        )
        QuoteEstimate.objects.create(quote=quote, price=Decimal("100.00"), scope="Small move")
        declined = self.client.get(reverse("quote_email_decline", args=[quote.pk, decline_token(quote)]))
        self.assertContains(declined, "Quote declined")
        quote.refresh_from_db()
        self.assertEqual(quote.status, QuoteRequest.Status.DECLINED)
        self.assertFalse(hasattr(quote, "job"))


class StaffCalendarTests(TestCase):
    def setUp(self):
        self.service = ServicePage.objects.create(
            name="Apartment Moving",
            slug="apartment-moving-nyc",
            category=ServicePage.Category.MOVING,
            short_description="Apartment moves.",
        )
        self.staff = User.objects.create_user(
            email="staff@example.com",
            password="password123",
            is_staff=True,
            role=User.Role.STAFF,
        )
        self.customer = User.objects.create_user(email="ada@example.com", password="password123")

    def quote(self, name, when, status=QuoteRequest.Status.QUOTED):
        prop = Property.objects.create(borough="queens", kind="apartment", sqft_band="under-1000", street="1 Main St")
        return QuoteRequest.objects.create(
            service=self.service,
            property=prop,
            contact_name=name,
            contact_email="ada@example.com",
            contact_phone="2125550100",
            status=status,
            preferred_date=when,
        )

    def test_month_shows_jobs_and_open_quotes_on_their_dates(self):
        booked = self.quote("Ada Lovelace", date(2026, 10, 15), QuoteRequest.Status.SCHEDULED)
        Job.objects.create(quote=booked, scheduled_date=date(2026, 10, 15), status=Job.Status.SCHEDULED)
        later = self.quote("November Only", date(2026, 11, 2))
        self.quote("Declined Person", date(2026, 10, 20), QuoteRequest.Status.DECLINED)
        undated = self.quote("Needs Date", None, QuoteRequest.Status.SCHEDULED)
        Job.objects.create(quote=undated, scheduled_date=None, status=Job.Status.SCHEDULED)

        self.assertEqual(self.client.get(reverse("staff_calendar")).status_code, 302)
        self.client.login(username="ada@example.com", password="password123")
        self.assertEqual(self.client.get(reverse("staff_calendar")).status_code, 403)
        self.client.logout()

        self.client.login(username="staff@example.com", password="password123")
        october = self.client.get(reverse("staff_calendar") + "?month=2026-10")
        self.assertContains(october, "October 2026")
        self.assertContains(october, 'class="calendar-event job scheduled"', count=1)
        self.assertContains(october, reverse("staff_quote_detail", args=[booked.pk]))
        self.assertContains(october, "November Only", count=1)
        self.assertNotContains(october, "Declined Person")
        self.assertContains(october, "Needs Date")
        self.assertContains(october, "?month=2026-09")
        self.assertContains(october, "?month=2026-11")

        november = self.client.get(reverse("staff_calendar") + "?month=2026-11")
        self.assertContains(november, 'class="calendar-event quote quoted"', count=1)
        self.assertContains(november, reverse("staff_quote_detail", args=[later.pk]))
        self.assertNotContains(november, "Ada Lovelace")


class StaffDashboardTests(TestCase):
    def setUp(self):
        self.service = ServicePage.objects.create(
            name="Apartment Moving",
            slug="apartment-moving-nyc",
            category=ServicePage.Category.MOVING,
            short_description="Apartment moves.",
        )
        self.staff = User.objects.create_user(
            email="staff@example.com",
            password="password123",
            is_staff=True,
            role=User.Role.STAFF,
        )
        self.customer = User.objects.create_user(email="ada@example.com", password="password123")

    def quote(self, name, status, when=None):
        prop = Property.objects.create(borough="queens", kind="apartment", sqft_band="under-1000", street="1 Main St")
        return QuoteRequest.objects.create(
            service=self.service,
            property=prop,
            contact_name=name,
            contact_email="ada@example.com",
            contact_phone="2125550100",
            status=status,
            preferred_date=when,
            total=Decimal("120.00"),
        )

    def test_dashboard_summarizes_open_work(self):
        from django.utils import timezone

        from apps.booking.models import QuotePayment

        today = timezone.localdate()
        waiting = self.quote("Needs Price", QuoteRequest.Status.REQUESTED)
        booked = self.quote("Jordan Lee", QuoteRequest.Status.SCHEDULED, today)
        Job.objects.create(quote=booked, scheduled_date=today, status=Job.Status.SCHEDULED)
        later = self.quote("Far Ahead", QuoteRequest.Status.QUOTED, today + date.resolution * 20)
        QuotePayment.objects.create(
            quote=booked,
            kind=QuotePayment.Kind.DEPOSIT,
            amount=Decimal("60.00"),
            status=QuotePayment.Status.PAID,
            paid_at=timezone.now(),
        )

        self.assertEqual(self.client.get(reverse("staff_dashboard")).status_code, 302)
        self.client.login(username="ada@example.com", password="password123")
        self.assertEqual(self.client.get(reverse("staff_dashboard")).status_code, 403)
        self.client.logout()

        self.client.login(username="staff@example.com", password="password123")
        page = self.client.get(reverse("staff_dashboard"))
        self.assertContains(page, "Need a price")
        self.assertContains(page, reverse("staff_quotes") + "?status=requested")
        self.assertContains(page, reverse("staff_quote_detail", args=[waiting.pk]))
        self.assertContains(page, "Jordan Lee")
        self.assertContains(page, "Next 7 days")
        self.assertContains(page, "60.00")
        self.assertContains(page, "Far Ahead")
