from unittest.mock import patch

from django.core import mail
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.content.models import NewsletterSubscriber


class NewsletterTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            email="staff@example.com",
            password="password123",
            is_staff=True,
            role=User.Role.STAFF,
        )
        self.customer = User.objects.create_user(email="ada@example.com", password="password123")

    def subscribe(self, email="reader@example.com", next_path="/privacy/", follow=False):
        return self.client.post(
            reverse("newsletter_subscribe"),
            {"email": email, "next": next_path},
            follow=follow,
        )

    def test_footer_form_subscribes_and_sends_welcome(self):
        home = self.client.get(reverse("home"))
        self.assertContains(home, reverse("newsletter_subscribe"))
        response = self.subscribe("Reader@Example.com", follow=True)
        self.assertRedirects(response, "/privacy/")
        self.assertContains(response, "occasional notes about moving and cleaning")
        subscriber = NewsletterSubscriber.objects.get()
        self.assertEqual(subscriber.email, "reader@example.com")
        self.assertTrue(subscriber.is_active)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("You're on the", mail.outbox[0].subject)
        self.assertIn(str(subscriber.token), mail.outbox[0].alternatives[0][0])

    def test_duplicate_active_email_is_not_added_again(self):
        self.subscribe()
        response = self.subscribe(follow=True)
        self.assertRedirects(response, "/privacy/")
        self.assertContains(response, "already on the list")
        self.assertEqual(NewsletterSubscriber.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_invalid_email_is_rejected(self):
        response = self.subscribe("not-an-email", follow=True)
        self.assertRedirects(response, "/privacy/")
        self.assertContains(response, "Enter a valid email address.")
        self.assertEqual(NewsletterSubscriber.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_unsafe_next_returns_home(self):
        response = self.subscribe(next_path="https://example.com")
        self.assertRedirects(response, "/")

    def test_signup_succeeds_when_welcome_mail_fails(self):
        with patch("apps.content.newsletter._send", side_effect=OSError("smtp")):
            response = self.subscribe(follow=True)
        self.assertRedirects(response, "/privacy/")
        self.assertContains(response, "occasional notes about moving and cleaning")
        self.assertTrue(NewsletterSubscriber.objects.get().is_active)

    def test_unsubscribe_requires_post_and_resubscribe_works(self):
        self.subscribe()
        subscriber = NewsletterSubscriber.objects.get()
        url = reverse("newsletter_unsubscribe", args=[subscriber.token])
        preview = self.client.get(url)
        self.assertContains(preview, "Unsubscribe")
        subscriber.refresh_from_db()
        self.assertTrue(subscriber.is_active)
        done = self.client.post(url)
        self.assertContains(done, "off the list")
        subscriber.refresh_from_db()
        self.assertFalse(subscriber.is_active)
        self.assertIsNotNone(subscriber.unsubscribed_at)
        again = self.subscribe()
        self.assertRedirects(again, "/privacy/")
        subscriber.refresh_from_db()
        self.assertTrue(subscriber.is_active)
        self.assertIsNone(subscriber.unsubscribed_at)
        self.assertEqual(NewsletterSubscriber.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 2)

    def test_staff_send_reaches_only_active_subscribers(self):
        self.subscribe("active@example.com")
        self.subscribe("gone@example.com")
        gone = NewsletterSubscriber.objects.get(email="gone@example.com")
        self.client.post(reverse("newsletter_unsubscribe", args=[gone.token]))
        mail.outbox.clear()

        denied = self.client.get(reverse("staff_newsletter"))
        self.assertEqual(denied.status_code, 302)
        self.client.login(username="ada@example.com", password="password123")
        self.assertEqual(self.client.get(reverse("staff_newsletter")).status_code, 403)
        self.client.logout()

        self.client.login(username="staff@example.com", password="password123")
        page = self.client.get(reverse("staff_newsletter"))
        self.assertContains(page, "1 active subscriber")
        self.assertContains(page, "gone@example.com")
        sent = self.client.post(
            reverse("staff_newsletter"),
            {"subject": "Spring cleaning notes", "body": "First line.\n\nSecond line."},
        )
        self.assertRedirects(sent, reverse("staff_newsletter"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["active@example.com"])
        self.assertEqual(mail.outbox[0].subject, "Spring cleaning notes")
        html = mail.outbox[0].alternatives[0][0]
        self.assertIn("First line.", html)
        self.assertIn("Second line.", html)
        active = NewsletterSubscriber.objects.get(email="active@example.com")
        self.assertIn(str(active.token), html)
        self.assertNotIn(str(gone.token), html)
