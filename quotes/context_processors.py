from .models import Service

def all_services(request):
    return {
        'all_services': Service.objects.all()
    }
