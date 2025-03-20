from django.urls import path
from .views import (
    admin_dashboard, update_quote_status, update_quote_detail_status, quote_list, quote_detail, booking_list, booking_detail, customer_list, customer_detail, 
    service_list, add_service_category, edit_service_category, delete_service_category,
    add_service, edit_service, delete_service
)

urlpatterns = [
    path("", admin_dashboard, name="admin_dashboard"),
    
    # Quotes Management
    path("quotes/", quote_list, name="quote_list"),
    path("quotes/<int:quote_id>/", quote_detail, name="quote_detail"),
    path("quotes/update-status/", update_quote_status, name="update_quote_status"),
    path("quotes/<int:quote_id>/update-status/", update_quote_detail_status, name="update_quote_detail_status"),

    # Booking Management
    path("bookings/", booking_list, name="booking_list"),
    path("bookings/<int:booking_id>/", booking_detail, name="booking_detail"),

    # Customer Management
    path("customers/", customer_list, name="customer_list"),
    path("customers/<int:customer_id>/", customer_detail, name="customer_detail"),

    path("services/", service_list, name="service_list"),
    path("services/category/add/", add_service_category, name="add_service_category"),
    path("services/category/edit/<int:category_id>/", edit_service_category, name="edit_service_category"),
    path("services/category/delete/<int:category_id>/", delete_service_category, name="delete_service_category"),
    path("services/add/", add_service, name="add_service"),
    path("services/edit/<int:service_id>/", edit_service, name="edit_service"),
    path("services/delete/<int:service_id>/", delete_service, name="delete_service"),
]
