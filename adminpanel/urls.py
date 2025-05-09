from django.urls import path
from .views import (
    admin_dashboard, update_quote_status, update_quote_detail_status, quote_list, quote_detail, booking_list, booking_detail_admin, customer_list, customer_detail, 
    service_list, add_service_category, edit_service_category, delete_service_category,
    add_service, edit_service, delete_service, booking_calendar, get_upcoming_quotes, quote_approval_view, quote_decline_view, block_time_slot,
    get_quote_details, add_quote, get_quotes_for_calendar, book_quote, get_event_details, decline_quote, ajax_filtered_quotes, export_quotes_csv, delete_quote, send_quote_email_view, get_booking_detail,
    giftcard_discount
)

urlpatterns = [
    path("", admin_dashboard, name="admin_dashboard"),
    
    # Quotes Management
    path("quotes/", quote_list, name="quote_list"),
    path("quotes/<int:quote_id>/", quote_detail, name="quote_detail"),
    path("quotes/<int:quote_id>/delete/", delete_quote, name="delete_quote"),
    path("admin/quotes/update-status/<int:quote_id>/", update_quote_status, name="update_quote_status"),
    path("quotes/<int:quote_id>/update-status/", update_quote_detail_status, name="update_quote_detail_status"),

    path("bookings/api/get_quote_details/", get_quote_details, name="get_quote_details"),
    path("quotes/api/add/", add_quote, name="add_quote"),
    path("bookings/filter/", ajax_filtered_quotes, name="ajax_filtered_quotes"),

    # Booking Management
    path("bookings/", booking_list, name="booking_list"),
    path('bookings/<int:booking_id>/json/', get_booking_detail, name='booking_detail_json'),
    path("bookings/<int:booking_id>/", booking_detail_admin, name="booking_detail_admin"),

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

    path("bookings/calendar/", booking_calendar, name="booking_calendar"),

    path("quotes/api/get/", get_quotes_for_calendar, name="get_quotes_for_calendar"),
    path("quotes/api/book/", book_quote, name="book_quote"),
    path("api/get_event_details/", get_event_details, name="get_event_details"),
    path("quotes/api/get/", get_quotes_for_calendar, name="get_quotes_for_calendar"),
    path("quotes/api/decline/", decline_quote, name="decline_quote"),
    path("quotes/api/upcoming/", get_upcoming_quotes, name="get_upcoming_quotes"),

    path("bookings/export-csv/", export_quotes_csv, name="export_quotes_csv"),

    path("quotes/<int:quote_id>/send-email/", send_quote_email_view, name="send_quote_email"),
    path("quote/<int:quote_id>/approve/<str:token>/", quote_approval_view, name="quote_approve_link"),
    path("quote/<int:quote_id>/decline/<str:token>/", quote_decline_view, name="quote_decline_link"),

    path("admin/block-time-slot/", block_time_slot, name="block_time_slot"),

    path("giftcard-discount/", giftcard_discount, name="giftcard_discount"),







]   