# accounts/urls.py
from django.urls import path
from .views import profile_view
from . import views
from django.contrib.auth import views as auth_views
from accounts import views as account_views

urlpatterns = [
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('accounts/register/', account_views.register, name='register'),
    path('accounts/profile/', account_views.profile_view, name='profile'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('booking/<int:booking_id>/', views.booking_detail, name='booking_detail'),

    path("cleaning/request/<int:service_cat_id>/", views.request_cleaning_booking, name="request_cleaning_booking"),
    path("submitted/<int:booking_id>/", views.booking_submitted_cleaning, name="booking_submitted_cleaning"),
    path("profile/add-address/", views.add_customer_address, name="add_customer_address"),

    path("booking/<int:booking_id>/reschedule/", views.reschedule_booking, name="reschedule_booking"),
    path("booking/<int:booking_id>/cancel/", views.cancel_booking, name="cancel_booking"),

    path('accounts/help/', views.help, name='help'),

]


