from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [

    
    # Consolidated booking forms
    path('', views.booking_home, name='booking_home'),
    path('home-cleaning/', views.home_cleaning_booking, name='home_cleaning_booking'),
    path('office-cleaning/', views.office_cleaning_booking, name='office_cleaning_booking'),
    
    # Confirmation
    path('confirmation/<int:booking_id>/', views.booking_confirmation, name='booking_confirmation'),
]
