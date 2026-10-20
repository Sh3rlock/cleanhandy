from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.company.models import get_company

User = get_user_model()


class SocialLinkTests(TestCase):
    def test_social_icons_follow_the_company_profile(self):
        company = get_company()
        company.facebook_url = "https://www.facebook.com/thecleanhandy"
        company.instagram_url = "https://www.instagram.com/thecleanhandy"
        company.youtube_url = ""
        company.linkedin_url = ""
        company.save()

        home = self.client.get(reverse("home"))
        self.assertContains(home, "https://www.facebook.com/thecleanhandy")
        self.assertContains(home, "https://www.instagram.com/thecleanhandy")
        self.assertContains(home, "TheCleanHandy on Facebook")
        self.assertNotContains(home, "on YouTube")
        self.assertContains(home, '"sameAs": ["https://www.facebook.com/thecleanhandy", "https://www.instagram.com/thecleanhandy"]')

        contact = self.client.get(reverse("contact"))
        self.assertContains(contact, "https://www.instagram.com/thecleanhandy")

        company.facebook_url = ""
        company.instagram_url = ""
        company.save()
        hidden = self.client.get(reverse("home"))
        self.assertNotContains(hidden, "Social media")
        self.assertNotContains(hidden, "sameAs")

    def test_staff_can_save_social_links(self):
        User.objects.create_user(email="staff@example.com", password="password123", is_staff=True)
        self.client.login(username="staff@example.com", password="password123")
        page = self.client.get(reverse("staff_social"))
        self.assertContains(page, "Facebook")
        self.assertContains(page, "LinkedIn")

        saved = self.client.post(
            reverse("staff_social"),
            {
                "facebook_url": "https://www.facebook.com/thecleanhandy",
                "instagram_url": "",
                "youtube_url": "not-a-url",
                "linkedin_url": "",
            },
        )
        self.assertEqual(saved.status_code, 200)
        self.assertContains(saved, "Enter a valid URL")
        company = get_company()
        self.assertEqual(company.facebook_url, "")

        saved = self.client.post(
            reverse("staff_social"),
            {
                "facebook_url": "https://www.facebook.com/thecleanhandy",
                "instagram_url": "",
                "youtube_url": "",
                "linkedin_url": "https://www.linkedin.com/company/thecleanhandy",
            },
        )
        self.assertRedirects(saved, reverse("staff_social"))
        company.refresh_from_db()
        self.assertEqual(company.facebook_url, "https://www.facebook.com/thecleanhandy")
        self.assertEqual(company.linkedin_url, "https://www.linkedin.com/company/thecleanhandy")
        self.assertEqual(company.instagram_url, "")
