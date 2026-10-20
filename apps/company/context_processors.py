from apps.company.models import get_company
from apps.content.models import ServicePage


def site_context(request):
    menu_services = ServicePage.objects.filter(is_active=True).exclude(menu="").order_by("menu_order", "name")
    grouped = {"moving": [], "cleaning": [], "commercial": []}
    for service in menu_services:
        if service.menu in grouped:
            grouped[service.menu].append(service)
    return {
        "company": get_company(),
        "nav_moving": grouped["moving"],
        "nav_cleaning": grouped["cleaning"],
        "nav_commercial": grouped["commercial"],
    }
