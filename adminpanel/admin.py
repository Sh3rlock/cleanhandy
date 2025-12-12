from django.contrib import admin
from django.utils.html import format_html
from .models import BlockedTimeSlot

@admin.register(BlockedTimeSlot)
class BlockedTimeSlotAdmin(admin.ModelAdmin):
    list_display = ("date", "start_time", "end_time", "reason", "created_at")
    list_filter = ("date",)

# HandymanQuote is already registered in quotes/admin.py
# This prevents duplicate registration errors
