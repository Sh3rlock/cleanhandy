# accounts/urls.py
from django.urls import path
from .views import profile_view
from . import views
from django.contrib.auth import views as auth_views
from accounts import views as account_views

urlpatterns = [
    
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('accounts/register/', account_views.register, name='register'),
    path('accounts/profile/', account_views.profile_view, name='profile'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('booking/<int:booking_id>/', views.booking_detail, name='booking_detail'),

    path("cleaning/request/", views.request_cleaning_booking, name="request_cleaning_booking"),
    path("handyman/request/", views.request_handyman_booking, name="request_handyman_booking"),
    path("submitted/<int:booking_id>/", views.booking_submitted_cleaning, name="booking_submitted_cleaning"),
    path("submitted_handyman/<int:booking_id>/", views.booking_submitted_handyman, name="booking_submitted_handyman"),
    path("profile/add-address/", views.add_customer_address, name="add_customer_address"),

    path("booking/<int:booking_id>/reschedule/", views.reschedule_booking, name="reschedule_booking"),
    path("booking/<int:booking_id>/cancel/", views.cancel_booking, name="cancel_booking"),

    path('accounts/help/', views.help, name='help'),
    path('refresh-csrf/', views.refresh_csrf_token, name='refresh_csrf_token'),
    path('test-email/', views.test_email, name='test_email'),

    path("activate/<uidb64>/<token>/", account_views.activate, name="activate"),
    path("login/", views.login_view, name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("password-reset/", auth_views.PasswordResetView.as_view(
        template_name="accounts/password_reset.html"), name="password_reset"),
    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(
        template_name="accounts/password_reset_done.html"), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="accounts/password_reset_confirm.html"), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(
        template_name="accounts/password_reset_complete.html"), name="password_reset_complete"),

]


