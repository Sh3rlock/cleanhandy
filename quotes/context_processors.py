from .models import Service
from .forms import NewsletterForm
from .models import ServiceCategory
from .models import ContactInfo, AboutContent

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

def handyman_service_category(request):
    return {
        'handyman_service_cat': ServiceCategory.objects.filter(name__iexact='handyman').first()
    }

def contact_info(request):
    """Add contact information to all templates"""
    contact_info = ContactInfo.get_active()
    return {
        'contact_info': contact_info
    }

def about_content(request):
    """Add about content to all templates"""
    about_content = AboutContent.get_active()
    return {
        'about_content': about_content
    }


