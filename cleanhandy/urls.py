from django.contrib import admin
from django.urls import path, include
from quotes.views import home  # Import the home view
from django.contrib.auth import views as auth_views
from accounts import views as account_views
from django.conf.urls.static import static
from django.conf import settings
from accounts.forms import StyledPasswordResetForm, StyledSetPasswordForm

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
    path('accounts/', include('accounts.urls')),
    path("giftcards/", include("giftcards.urls")),
    path("bookings/", include("bookings.urls")),

    path("activate/<uidb64>/<token>/", account_views.activate, name="activate"),
    path("login/", account_views.login_view, name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("password-reset/", auth_views.PasswordResetView.as_view(form_class=StyledPasswordResetForm, template_name="accounts/password_reset.html"), name="password_reset"),
    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(
        template_name="accounts/password_reset_done.html"), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="accounts/password_reset_confirm.html",
        form_class=StyledSetPasswordForm
    ), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(
        template_name="accounts/password_reset_complete.html"), name="password_reset_complete"),

]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    path("healthz/", healthcheck),  # add this
]
