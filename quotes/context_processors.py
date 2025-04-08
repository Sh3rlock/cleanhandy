from .models import Service
from .forms import NewsletterForm

def all_services(request):
    return {
        'all_services': Service.objects.all()
    }

def newsletter_form(request):
    return {
        'newsletter_form': NewsletterForm()
    }
