from .models import Service
from .forms import NewsletterForm
from .models import ServiceCategory

def all_services(request):
    return {
        'all_services': Service.objects.all()
    }

def newsletter_form(request):
    return {
        'newsletter_form': NewsletterForm()
    }

def cleaning_service_category(request):
    return {
        'cleaning_service_cat': ServiceCategory.objects.filter(name__iexact='cleaning').first()
    }


