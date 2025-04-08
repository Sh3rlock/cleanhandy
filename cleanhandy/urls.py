from django.contrib import admin
from django.urls import path, include
from quotes.views import home  # Import the home view
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static
from django.conf import settings

from django.http import HttpResponse
def healthcheck(request):
    return HttpResponse("OK")

urlpatterns = [
    path("", home, name="home"),
    path("admin/", include("adminpanel.urls")),  # Custom admin panel
    path("django-admin/", admin.site.urls),  # Default Django admin
    path("cleaning/", include("quotes.urls_cleaning")),
    path("handyman/", include("quotes.urls_handyman")),
    path("quotes/", include("quotes.urls")),
    path("blog/", include("blog.urls")),

    # Authentication URLs
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(template_name="registration/logout.html"), name="logout"),

]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    path("healthz/", healthcheck),  # add this
]
