"""
Populate Site page SEO rows with starter titles and descriptions (Django admin: Site page SEO).

Usage (from project directory with Django env):
  python manage.py seed_site_page_seo              # create missing rows only
  python manage.py seed_site_page_seo --update-empty  # fill blank fields on existing rows
  python manage.py seed_site_page_seo --overwrite     # replace all seeded text fields

Blog posts and Services: edit SEO on each Blog post / Service in admin — not covered here.
"""
from django.core.management.base import BaseCommand

from seo.models import SEOSchemaType, SitePageKey, SitePageSEO


# Starter copy for The CleanHandy — edit in admin to match your brand and locations.
SEED = {
    SitePageKey.HOME: {
        "seo_title": "Professional Cleaning & Handyman Services in New York",
        "meta_description": (
            "Book trusted home cleaning, office cleaning, and handyman help in NYC. "
            "Flexible scheduling, clear pricing, and reliable crews from The CleanHandy."
        ),
        "meta_keywords": (
            "house cleaning NYC, office cleaning New York, handyman services, "
            "deep cleaning, booking cleaning online"
        ),
        "schema_type": SEOSchemaType.WEB_PAGE,
        "notes": "Homepage — keep title under ~60 chars; description 150–160 chars ideal.",
    },
    SitePageKey.ABOUT: {
        "seo_title": "About The CleanHandy",
        "meta_description": (
            "Learn who we are, how we vet our teams, and why customers choose The CleanHandy "
            "for cleaning and handyman services across New York."
        ),
        "meta_keywords": "about The CleanHandy, cleaning company NYC, our team",
        "schema_type": SEOSchemaType.WEB_PAGE,
        "notes": "",
    },
    SitePageKey.CONTACT: {
        "seo_title": "Contact Us",
        "meta_description": (
            "Get in touch with The CleanHandy for quotes, scheduling, and support. "
            "We respond quickly to questions about home, office, and specialty cleaning."
        ),
        "meta_keywords": "contact The CleanHandy, cleaning quote NYC, customer support",
        "schema_type": SEOSchemaType.WEB_PAGE,
        "notes": "",
    },
    SitePageKey.BLOG_INDEX: {
        "seo_title": "Cleaning & Home Care Tips",
        "meta_description": (
            "Articles on booking cleaning, preparing your home, office maintenance, "
            "and getting the most from professional services in New York."
        ),
        "meta_keywords": "cleaning tips, home maintenance blog, NYC cleaning advice",
        "schema_type": SEOSchemaType.WEB_PAGE,
        "notes": "",
    },
    SitePageKey.FAQ: {
        "seo_title": "Frequently Asked Questions",
        "meta_description": (
            "Answers about pricing, scheduling, what to expect on visit day, "
            "and policies for The CleanHandy cleaning and handyman services."
        ),
        "meta_keywords": "cleaning FAQ, booking questions, cancellation policy",
        "schema_type": SEOSchemaType.FAQ_PAGE,
        "notes": "Uses FAQPage schema when set here.",
    },
    SitePageKey.TERMS: {
        "seo_title": "Terms of Service",
        "meta_description": (
            "Terms of service for using The CleanHandy website and booking cleaning "
            "or handyman services."
        ),
        "meta_keywords": "terms of service, legal, The CleanHandy",
        "schema_type": SEOSchemaType.WEB_PAGE,
        "notes": "Often noindex on legal-only sites — leave index on if you want them found.",
    },
    SitePageKey.PRIVACY: {
        "seo_title": "Privacy Policy",
        "meta_description": (
            "How The CleanHandy collects, uses, and protects your personal information "
            "when you use our site and services."
        ),
        "meta_keywords": "privacy policy, data protection, The CleanHandy",
        "schema_type": SEOSchemaType.WEB_PAGE,
        "notes": "",
    },
    SitePageKey.CLEANING_SERVICES: {
        "seo_title": "Home & Residential Cleaning Services",
        "meta_description": (
            "Browse residential cleaning options in NYC — regular, deep, move-in/out, "
            "and more. Request a quote tailored to your home."
        ),
        "meta_keywords": "residential cleaning NYC, house cleaning services, deep clean",
        "schema_type": SEOSchemaType.SERVICE,
        "notes": "",
    },
    SitePageKey.COMMERCIAL_SERVICES: {
        "seo_title": "Commercial & Office Cleaning",
        "meta_description": (
            "Professional office and commercial cleaning for New York businesses. "
            "Flexible schedules and services tailored to your workspace."
        ),
        "meta_keywords": "office cleaning NYC, commercial cleaning, janitorial services",
        "schema_type": SEOSchemaType.SERVICE,
        "notes": "",
    },
    SitePageKey.HANDYMAN_SERVICES: {
        "seo_title": "Handyman Services",
        "meta_description": (
            "Book skilled handyman help in New York — repairs, installs, and odd jobs. "
            "See services and request a quote from The CleanHandy."
        ),
        "meta_keywords": "handyman NYC, home repairs, odd jobs, handyman quote",
        "schema_type": SEOSchemaType.SERVICE,
        "notes": "",
    },
    SitePageKey.HOME_CLEANING_QUOTE: {
        "seo_title": "Book Home Cleaning",
        "meta_description": (
            "Get a home cleaning quote in minutes. Tell us about your space and schedule — "
            "The CleanHandy serves New York with vetted professionals."
        ),
        "meta_keywords": "book house cleaning, home cleaning quote NYC, schedule cleaner",
        "schema_type": SEOSchemaType.WEB_PAGE,
        "notes": "Same page may also match URL name cleaning_booking — tune one canonical if needed.",
    },
    SitePageKey.OFFICE_CLEANING_QUOTE: {
        "seo_title": "Office Cleaning Quote",
        "meta_description": (
            "Request a quote for office cleaning in NYC. Share your space size, frequency, "
            "and needs — we will follow up with options."
        ),
        "meta_keywords": "office cleaning quote, commercial cleaning estimate NYC",
        "schema_type": SEOSchemaType.WEB_PAGE,
        "notes": "",
    },
    SitePageKey.OFFICE_CLEANING_BOOKING: {
        "seo_title": "Book Office Cleaning",
        "meta_description": (
            "Schedule office cleaning with The CleanHandy. Reliable crews for New York "
            "businesses — book or inquire online."
        ),
        "meta_keywords": "book office cleaning, NYC office cleaner scheduling",
        "schema_type": SEOSchemaType.WEB_PAGE,
        "notes": "",
    },
    SitePageKey.CLEANING_BOOKING: {
        "seo_title": "Book a Cleaning",
        "meta_description": (
            "Book residential cleaning online. Choose options that fit your home in New York — "
            "fast booking with The CleanHandy."
        ),
        "meta_keywords": "book cleaning online, schedule house cleaning NYC",
        "schema_type": SEOSchemaType.WEB_PAGE,
        "notes": "Legacy/alternate URL for home cleaning booking — align messaging with home_cleaning_quote.",
    },
    SitePageKey.HANDYMAN_BOOKING: {
        "seo_title": "Book a Handyman",
        "meta_description": (
            "Book handyman services in New York. Describe your job and preferred time — "
            "The CleanHandy connects you with qualified help."
        ),
        "meta_keywords": "book handyman NYC, handyman appointment, repair booking",
        "schema_type": SEOSchemaType.WEB_PAGE,
        "notes": "",
    },
}


class Command(BaseCommand):
    help = "Seed Site page SEO rows (django-admin → Site page SEO)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite seeded text fields even if already set.",
        )
        parser.add_argument(
            "--update-empty",
            action="store_true",
            help="For existing rows, copy seed values only into blank text fields.",
        )

    def handle(self, *args, **options):
        overwrite = options["overwrite"]
        update_empty = options["update_empty"]

        created_n = 0
        updated_n = 0
        skipped_n = 0

        for page_key, seed in SEED.items():
            obj = SitePageSEO.objects.filter(page_key=page_key).first()

            if obj is None:
                SitePageSEO.objects.create(page_key=page_key, **seed)
                created_n += 1
                self.stdout.write(self.style.SUCCESS(f"Created: {page_key}"))
                continue

            if overwrite:
                for key, value in seed.items():
                    setattr(obj, key, value)
                obj.save()
                updated_n += 1
                self.stdout.write(self.style.WARNING(f"Overwritten: {page_key}"))
                continue

            if update_empty:
                changed = False
                for key, value in seed.items():
                    if key in ("robots_index", "robots_follow", "schema_type", "og_image", "canonical_url"):
                        continue
                    current = getattr(obj, key, None)
                    if current is None or (isinstance(current, str) and not str(current).strip()):
                        setattr(obj, key, value)
                        changed = True
                if not changed:
                    skipped_n += 1
                    self.stdout.write(f"Unchanged (already filled): {page_key}")
                else:
                    obj.save()
                    updated_n += 1
                    self.stdout.write(self.style.SUCCESS(f"Filled blanks: {page_key}"))
                continue

            skipped_n += 1
            self.stdout.write(f"Skipped (exists): {page_key}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Created: {created_n}, updated: {updated_n}, skipped: {skipped_n}."
            )
        )
        self.stdout.write(
            "Tip: OG title/description default from SEO title and meta description if left empty. "
            "Upload OG image per page or rely on SEO_DEFAULT_OG_IMAGE in settings."
        )
