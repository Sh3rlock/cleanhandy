from decimal import Decimal

from apps.booking.models import PriceVariable, PriceVariableCategory, TaxSettings
from apps.content.models import ServicePage


def _option(name, price, discount="0"):
    return {"name": name, "price": Decimal(price), "discount_percent": Decimal(discount)}


MOVING_WITH_HOME = [
    "moving-services-nyc",
    "apartment-moving-nyc",
    "small-moves-nyc",
    "moving-and-cleaning-nyc",
]
MOVING_ALL = MOVING_WITH_HOME + ["moving-labor-nyc"]
CLEANING = [
    "move-in-out-cleaning-nyc",
    "move-out-cleaning-nyc",
    "move-in-cleaning-nyc",
    "apartment-move-out-cleaning-nyc",
    "rental-turnover-cleaning-nyc",
    "deep-cleaning-nyc",
    "post-renovation-cleaning-nyc",
]
COMMERCIAL = [
    "commercial-cleaning-nyc",
    "office-cleaning-nyc",
    "retail-cleaning-nyc",
    "property-management-cleaning",
    "recurring-commercial-cleaning",
]

CATALOG = [
    {
        "slug": "moving-home-size",
        "name": "Home size",
        "input_type": PriceVariableCategory.InputType.SINGLE,
        "sort_order": 10,
        "services": MOVING_WITH_HOME,
        "options": [
            _option("Studio", "450"),
            _option("1 bedroom", "650"),
            _option("2 bedrooms", "950"),
            _option("3 or more bedrooms", "1400"),
        ],
    },
    {
        "slug": "moving-pickup-access",
        "name": "Pickup access",
        "input_type": PriceVariableCategory.InputType.SINGLE,
        "sort_order": 20,
        "services": MOVING_ALL,
        "options": [
            _option("Elevator", "0"),
            _option("Walk-up, 1 flight", "75"),
            _option("Walk-up, 2 flights", "150"),
            _option("Walk-up, 3 or more flights", "250"),
        ],
    },
    {
        "slug": "moving-dropoff-access",
        "name": "Drop-off access",
        "input_type": PriceVariableCategory.InputType.SINGLE,
        "sort_order": 30,
        "services": MOVING_WITH_HOME,
        "options": [
            _option("Elevator", "0"),
            _option("Walk-up, 1 flight", "75"),
            _option("Walk-up, 2 flights", "150"),
            _option("Walk-up, 3 or more flights", "250"),
        ],
    },
    {
        "slug": "moving-packing",
        "name": "Packing",
        "input_type": PriceVariableCategory.InputType.ADDON,
        "sort_order": 40,
        "services": MOVING_WITH_HOME,
        "options": [_option("Pack the contents of the home", "350")],
    },
    {
        "slug": "moving-labor-crew",
        "name": "Crew and hours",
        "input_type": PriceVariableCategory.InputType.SINGLE,
        "sort_order": 15,
        "services": ["moving-labor-nyc"],
        "options": [
            _option("2 movers, 2 hours", "280"),
            _option("2 movers, 4 hours", "520"),
            _option("3 movers, 4 hours", "780"),
            _option("3 movers, 8 hours", "1440"),
        ],
    },
    {
        "slug": "cleaning-home-size",
        "name": "Home size",
        "input_type": PriceVariableCategory.InputType.SINGLE,
        "sort_order": 10,
        "services": CLEANING,
        "options": [
            _option("Studio", "180"),
            _option("1 bedroom", "240"),
            _option("2 bedrooms", "320"),
            _option("3 or more bedrooms", "420"),
        ],
    },
    {
        "slug": "cleaning-bathrooms",
        "name": "Bathrooms",
        "input_type": PriceVariableCategory.InputType.SINGLE,
        "sort_order": 20,
        "services": CLEANING,
        "options": [
            _option("1 bathroom", "0"),
            _option("2 bathrooms", "45"),
            _option("3 or more bathrooms", "90"),
        ],
    },
    {
        "slug": "commercial-space-size",
        "name": "Space size",
        "input_type": PriceVariableCategory.InputType.SINGLE,
        "sort_order": 10,
        "services": COMMERCIAL,
        "options": [
            _option("Under 1,000 sq ft", "250"),
            _option("1,000–2,500 sq ft", "450"),
            _option("2,500–5,000 sq ft", "750"),
            _option("Over 5,000 sq ft", "1100"),
        ],
    },
    {
        "slug": "commercial-frequency",
        "name": "Visit frequency",
        "input_type": PriceVariableCategory.InputType.SINGLE,
        "sort_order": 20,
        "services": COMMERCIAL,
        "options": [
            _option("One-time visit", "0", "0"),
            _option("Monthly", "0", "5"),
            _option("Every two weeks", "0", "5"),
            _option("Weekly", "0", "10"),
        ],
    },
    {
        "slug": "assembly-size",
        "name": "Assembly size",
        "input_type": PriceVariableCategory.InputType.SINGLE,
        "sort_order": 10,
        "services": ["assembly"],
        "options": [
            _option("A few small pieces", "120"),
            _option("A room of furniture", "280"),
            _option("A whole apartment", "520"),
        ],
    },
    {
        "slug": "mounting-size",
        "name": "Mounting size",
        "input_type": PriceVariableCategory.InputType.SINGLE,
        "sort_order": 10,
        "services": ["mounting"],
        "options": [
            _option("One item", "90"),
            _option("Two or three items", "180"),
            _option("Four or more items", "320"),
        ],
    },
    {
        "slug": "parking",
        "name": "Parking",
        "input_type": PriceVariableCategory.InputType.SINGLE,
        "sort_order": 50,
        "services": MOVING_ALL + CLEANING + COMMERCIAL + ["assembly", "mounting", "post-event-cleaning-nyc"],
        "options": [
            _option("Free parking at the building", "0"),
            _option("Street parking", "40"),
            _option("Paid garage or lot", "75"),
        ],
    },
    {
        "slug": "post-event-size",
        "name": "Event size",
        "input_type": PriceVariableCategory.InputType.SINGLE,
        "sort_order": 10,
        "services": ["post-event-cleaning-nyc"],
        "options": [
            _option("Small gathering", "220"),
            _option("Medium venue", "480"),
            _option("Large venue", "860"),
        ],
    },
]


def seed_quote_prices():
    """Create starter price options without overwriting amounts staff have edited."""
    TaxSettings.load()
    pages = {page.slug: page for page in ServicePage.objects.all()}
    for row in CATALOG:
        category, created = PriceVariableCategory.objects.get_or_create(
            slug=row["slug"],
            defaults={
                "name": row["name"],
                "input_type": row["input_type"],
                "sort_order": row["sort_order"],
                "is_active": True,
            },
        )
        if created:
            category.services.set([pages[slug] for slug in row["services"] if slug in pages])
        for index, option in enumerate(row["options"]):
            PriceVariable.objects.get_or_create(
                category=category,
                name=option["name"],
                defaults={
                    "price": option["price"],
                    "discount_percent": option["discount_percent"],
                    "sort_order": index,
                    "is_active": True,
                },
            )
