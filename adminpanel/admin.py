from django.contrib import admin
from .models import BlockedTimeSlot

@admin.register(BlockedTimeSlot)
class BlockedTimeSlotAdmin(admin.ModelAdmin):
    list_display = ("date", "start_time", "end_time", "reason", "created_at")
    list_filter = ("date",)
