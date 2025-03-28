from django.urls import path
from .views import quote_submitted, request_cleaning_quote, request_handyman_quote, available_hours_api

urlpatterns = [
    path("request-cleaning/", request_cleaning_quote, name="request_cleaning_quote"),
    path("request-handyman/", request_handyman_quote, name="request_handyman_quote"),
    path("submitted/<int:quote_id>/", quote_submitted, name="quote_submitted"),
    path("api/available-hours/", available_hours_api, name="available_hours_api"),
    
]