from django.contrib import admin
from django.urls import path, include
from quotes.views import home  # Import the home view
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("", home, name="home"),
    path("admin/", include("adminpanel.urls")),  # Custom admin panel
    path("django-admin/", admin.site.urls),  # Default Django admin
    path("cleaning/", include("quotes.urls_cleaning")),
    path("handyman/", include("quotes.urls_handyman")),
    path("quotes/", include("quotes.urls")),

    # Authentication URLs
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
]

