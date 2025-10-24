from django.urls import path
from .views import (
    admin_dashboard, update_quote_status, update_quote_detail_status, quote_list, quote_detail, booking_list, booking_detail_admin, customer_list, customer_detail, 
    service_list, add_service_category, edit_service_category, delete_service_category,
    add_service, edit_service, delete_service, booking_calendar, get_upcoming_quotes, quote_approval_view, quote_decline_view, block_time_slot,
    get_quote_details, add_quote, get_quotes_for_calendar, book_quote, get_event_details, decline_quote, ajax_filtered_quotes, export_quotes_csv, delete_quote, send_quote_email_view, get_booking_detail,
    giftcard_discount, subscriber_list, add_subscriber, export_subscribers_csv, office_quote_list, office_quote_detail, export_office_quotes_csv, send_office_quote_email, generate_office_quote_pdf,
    handyman_quote_list, handyman_quote_detail, update_handyman_quote_status, export_handyman_quotes_csv, send_handyman_quote_email, generate_handyman_quote_pdf, delete_handyman_quote,
    post_event_cleaning_quote_list, post_event_cleaning_quote_detail, update_post_event_cleaning_quote_status, export_post_event_cleaning_quotes_csv, send_post_event_cleaning_quote_email, generate_post_event_cleaning_quote_pdf, delete_post_event_cleaning_quote,
    send_payment_link
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
    path("customers/<str:username>/", customer_detail, name="customer_detail"),

    path("subscribers/", subscriber_list, name="subscriber_list"),

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

    path("subscribers/add/", add_subscriber, name="add_subscriber"),
    path('export-subscribers-csv/', export_subscribers_csv, name='export_subscribers_csv'),

    # Office Quotes Management
    path("office-quotes/", office_quote_list, name="office_quote_list"),
    path("office-quotes/<int:quote_id>/", office_quote_detail, name="office_quote_detail"),
    path("office-quotes/<int:quote_id>/delete/", delete_quote, name="delete_office_quote"),
    path("admin/office-quotes/update-status/<int:quote_id>/", update_quote_status, name="update_office_quote_status"),
    path("office-quotes/<int:quote_id>/update-status/", update_quote_detail_status, name="update_office_quote_detail_status"),

    path("office-bookings/api/get_quote_details/", get_quote_details, name="get_office_quote_details"),
    path("office-quotes/api/add/", add_quote, name="add_office_quote"),
    path("office-bookings/filter/", ajax_filtered_quotes, name="ajax_filtered_office_quotes"),

    path("office-bookings/export-csv/", export_quotes_csv, name="export_office_quotes_csv"),

    path("office-quotes/<int:quote_id>/send-email/", send_office_quote_email, name="send_office_quote_email"),
    path("office-quotes/<int:quote_id>/generate-pdf/", generate_office_quote_pdf, name="generate_office_quote_pdf"),
    path("office-quote/<int:quote_id>/approve/<str:token>/", quote_approval_view, name="office_quote_approve_link"),
    path("office-quote/<int:quote_id>/decline/<str:token>/", quote_decline_view, name="office_quote_decline_link"),

    path("admin/office-block-time-slot/", block_time_slot, name="block_office_time_slot"),

    # Handyman Quotes Management
    path("handyman-quotes/", handyman_quote_list, name="handyman_quote_list"),
    path("handyman-quotes/<int:quote_id>/", handyman_quote_detail, name="handyman_quote_detail"),
    path("handyman-quotes/<int:quote_id>/delete/", delete_handyman_quote, name="delete_handyman_quote"),
    path("admin/handyman-quotes/update-status/<int:quote_id>/", update_handyman_quote_status, name="update_handyman_quote_status"),
    path("handyman-quotes/<int:quote_id>/update-status/", update_handyman_quote_status, name="update_handyman_quote_detail_status"),
    path("handyman-quotes/export-csv/", export_handyman_quotes_csv, name="export_handyman_quotes_csv"),
    path("handyman-quotes/<int:quote_id>/send-email/", send_handyman_quote_email, name="send_handyman_quote_email"),
    path("handyman-quotes/<int:quote_id>/generate-pdf/", generate_handyman_quote_pdf, name="generate_handyman_quote_pdf"),

    # Post Event Cleaning Quotes Management
    path("post-event-cleaning-quotes/", post_event_cleaning_quote_list, name="post_event_cleaning_quote_list"),
    path("post-event-cleaning-quotes/<int:quote_id>/", post_event_cleaning_quote_detail, name="post_event_cleaning_quote_detail"),
    path("post-event-cleaning-quotes/<int:quote_id>/delete/", delete_post_event_cleaning_quote, name="delete_post_event_cleaning_quote"),
    path("admin/post-event-cleaning-quotes/update-status/<int:quote_id>/", update_post_event_cleaning_quote_status, name="update_post_event_cleaning_quote_status"),
    path("post-event-cleaning-quotes/<int:quote_id>/update-status/", update_post_event_cleaning_quote_status, name="update_post_event_cleaning_quote_detail_status"),
    path("post-event-cleaning-quotes/export-csv/", export_post_event_cleaning_quotes_csv, name="export_post_event_cleaning_quotes_csv"),
    path("post-event-cleaning-quotes/<int:quote_id>/send-email/", send_post_event_cleaning_quote_email, name="send_post_event_cleaning_quote_email"),
    path("post-event-cleaning-quotes/<int:quote_id>/generate-pdf/", generate_post_event_cleaning_quote_pdf, name="generate_post_event_cleaning_quote_pdf"),

    # Payment Link Management
    path("send-payment-link/", send_payment_link, name="send_payment_link"),

]   