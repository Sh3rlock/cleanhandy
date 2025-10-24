from .models import Service
from .forms import NewsletterForm
from .models import ServiceCategory
from .models import ContactInfo, AboutContent

def all_services(request):
    try:
        return {
            'all_services': Service.objects.all()
        }
    except Exception as e:
        return {
            'all_services': []
        }

def newsletter_form(request):
    return {
        'newsletter_form': NewsletterForm()
    }

def cleaning_service_category(request):
    try:
        return {
            'home_service_cat': ServiceCategory.objects.filter(name__iexact='home').first(),
            'commercial_service_cat': ServiceCategory.objects.filter(name__iexact='commercial').first()
        }
    except Exception as e:
        return {
            'home_service_cat': None,
            'commercial_service_cat': None
        }

def handyman_service_category(request):
    try:
        return {
            'handyman_service_cat': ServiceCategory.objects.filter(name__iexact='handyman').first()
        }
    except Exception as e:
        return {
            'handyman_service_cat': None
        }

def contact_info(request):
    """Add contact information to all templates"""
    try:
        contact_info = ContactInfo.get_active()
    except Exception as e:
        # Handle case where table doesn't exist yet (during migrations)
        contact_info = None
    return {
        'contact_info': contact_info
    }

def about_content(request):
    """Add about content to all templates"""
    try:
        about_content = AboutContent.get_active()
    except Exception as e:
        # Handle case where table doesn't exist yet (during migrations)
        about_content = None
    return {
        'about_content': about_content
    }


