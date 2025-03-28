from django.contrib import admin
from django.utils.html import format_html
from .models import Quote, Service, CleaningExtra, HomeType, SquareFeetOption

admin.site.register(Service)
admin.site.register(CleaningExtra)
admin.site.register(HomeType)
admin.site.register(SquareFeetOption)


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ["id", "customer", "date", "price", "status", "pdf_link"]
    readonly_fields = ["pdf_preview", "pdf_file"]
    
    def pdf_link(self, obj):
        if obj.pdf_file:
            return format_html('<a href="{}" target="_blank">Download PDF</a>', obj.pdf_file.url)
        return "-"
    pdf_link.short_description = "PDF Quote"

    def pdf_preview(self, obj):
        if obj.pdf_file:
            return format_html('<iframe src="{}" width="100%" height="500px"></iframe>', obj.pdf_file.url)
        return "No PDF available"
    pdf_preview.short_description = "PDF Preview"

