from django.contrib import admin
from .models import Booking

class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "quote", "confirmed", "created_at")
    search_fields = ("quote__name", "quote__email")

admin.site.register(Booking, BookingAdmin)
