from django.urls import path
from .views import cleaning_services

urlpatterns = [
    path("", cleaning_services, name="cleaning_services"),
]