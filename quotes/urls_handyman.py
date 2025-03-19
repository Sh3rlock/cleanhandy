from django.urls import path
from .views import handyman_services

urlpatterns = [
    path("", handyman_services, name="handyman_services"),
]