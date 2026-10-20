from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from apps.content.models import ServicePage
from apps.booking.models import (
    ConversionEvent,
    Invoice,
    Job,
    PriceVariable,
    PriceVariableCategory,
    PricingGuideRow,
    Property,
    QuoteEstimate,
    QuoteLineItem,
    QuotePayment,
    QuoteRequest,
    TaxSettings,
)


class QuoteLineItemInline(admin.TabularInline):
    model = QuoteLineItem
    extra = 0


class QuoteEstimateInline(admin.StackedInline):
    model = QuoteEstimate
    extra = 0


class InvoiceInline(admin.TabularInline):
    model = Invoice
    extra = 0


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("id", "label", "kind", "borough", "sqft_band", "owner")
    list_filter = ("borough", "kind", "sqft_band")
    search_fields = ("label", "street", "owner__email")


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "service", "borough", "status", "subtotal", "tax_amount", "total", "contact_email", "pdf_link", "created_at")
    list_filter = ("status", "service", "property__borough")
    search_fields = ("contact_name", "contact_email", "contact_phone")
    inlines = [QuoteLineItemInline, QuoteEstimateInline]
    date_hierarchy = "created_at"

    @admin.display(description="Borough")
    def borough(self, obj):
        return obj.property.get_borough_display()

    @admin.display(description="PDF")
    def pdf_link(self, obj):
        url = reverse("staff_quote_pdf", args=[obj.pk])
        return format_html('<a href="{}">Download</a>', url)


@admin.register(QuotePayment)
class QuotePaymentAdmin(admin.ModelAdmin):
    list_display = ("quote", "kind", "amount", "status", "paid_at")
    list_filter = ("kind", "status")
    search_fields = ("quote__contact_email", "stripe_payment_link_id")


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("id", "quote", "status", "scheduled_date")
    list_filter = ("status",)
    inlines = [InvoiceInline]


class PriceVariableInline(admin.TabularInline):
    model = PriceVariable
    extra = 0


@admin.register(PriceVariableCategory)
class PriceVariableCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "input_type", "is_active", "sort_order")
    list_filter = ("input_type", "is_active")
    filter_horizontal = ("services",)
    inlines = [PriceVariableInline]

    def get_queryset(self, request):
        return super().get_queryset(request).exclude(slug="painting-size")

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "services":
            kwargs["queryset"] = ServicePage.objects.exclude(slug="painting")
        return super().formfield_for_manytomany(db_field, request, **kwargs)


@admin.register(TaxSettings)
class TaxSettingsAdmin(admin.ModelAdmin):
    list_display = ("tax_rate", "is_active")


@admin.register(PricingGuideRow)
class PricingGuideRowAdmin(admin.ModelAdmin):
    list_display = ("label", "sqft_band", "cleaners", "hours", "service", "sort_order")
    list_editable = ("sort_order",)


@admin.register(ConversionEvent)
class ConversionEventAdmin(admin.ModelAdmin):
    list_display = ("kind", "path", "user", "quote", "created_at")
    list_filter = ("kind",)
    date_hierarchy = "created_at"
