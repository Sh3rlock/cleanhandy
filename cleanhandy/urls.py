from django.contrib import admin
from django.urls import path, include
from quotes.views import home  # Import the home view

urlpatterns = [
    path("", home, name="home"),  # Homepage
    path("admin/", admin.site.urls),
    path("cleaning/", include("quotes.urls_cleaning")),  # Cleaning page
    path("handyman/", include("quotes.urls_handyman")),  # Handyman page
    path("quotes/", include("quotes.urls")),
]
