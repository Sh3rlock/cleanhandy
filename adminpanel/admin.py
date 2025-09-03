from django.contrib import admin
from django.utils.html import format_html
from .models import BlockedTimeSlot
from quotes.models import OfficeQuote, HandymanQuote

@admin.register(BlockedTimeSlot)
class BlockedTimeSlotAdmin(admin.ModelAdmin):
    list_display = ("date", "start_time", "end_time", "reason", "created_at")
    list_filter = ("date",)

@admin.register(OfficeQuote)
class OfficeQuoteAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "phone_number", "square_footage", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("name", "email", "phone_number", "business_address")
    readonly_fields = ("created_at",)
    list_editable = ("status",)
    
    fieldsets = (
        ("Customer Information", {
            "fields": ("name", "email", "phone_number")
        }),
        ("Project Details", {
            "fields": ("business_address", "square_footage", "job_description")
        }),
        ("Status & Notes", {
            "fields": ("status", "admin_notes")
        }),
        ("Timestamps", {
            "fields": ("created_at",),
            "classes": ("collapse",)
        }),
    )

# HandymanQuote is already registered in quotes/admin.py
# This prevents duplicate registration errors
