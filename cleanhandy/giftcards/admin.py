from django.contrib import admin
from .models import GiftCard, DiscountCode

@admin.register(GiftCard)
class GiftCardAdmin(admin.ModelAdmin):
    list_display = ("code", "amount", "balance", "is_active", "purchaser_email", "recipient_email", "created_at")
    search_fields = ("code", "recipient_email", "purchaser_email")
    list_filter = ("is_active", "created_at")

@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_type", "value", "usage_limit", "times_used", "is_active", "expires_at")
    search_fields = ("code",)
    list_filter = ("is_active", "discount_type", "expires_at")
