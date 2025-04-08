from django.urls import path
from .views import about, contact, blog, blog_detail, quote_submitted, request_cleaning_quote, request_handyman_quote, available_hours_api, quote_submitted_handyman, subscribe_newsletter

urlpatterns = [
    path("about", about, name="about"),
    path("contact", contact, name="contact"),
    path("blog", blog, name="blog"),
    path("blog-detail", blog_detail, name="blog_detail"),

    path("cleaning/request/<int:service_id>/", request_cleaning_quote, name="request_cleaning_quote"),
    path('handyman/request/<int:service_id>/', request_handyman_quote, name='request_handyman_quote'),
    path("submitted/<int:quote_id>/", quote_submitted, name="quote_submitted"),
    path("submitted-handyman/<int:quote_id>/", quote_submitted_handyman, name="quote_submitted_handyman"),
    path("api/available-hours/", available_hours_api, name="available_hours_api"),

    path('subscribe/', subscribe_newsletter, name='subscribe_newsletter'),
    
]