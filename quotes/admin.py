from django.contrib import admin
from django.utils.html import format_html
from .models import Quote, Service, CleaningExtra, HomeType, SquareFeetOption,NewsletterSubscriber, Booking, Contact, Review, ContactInfo, AboutContent

admin.site.register(Service)
admin.site.register(CleaningExtra)
admin.site.register(HomeType)
admin.site.register(SquareFeetOption)
admin.site.register(Review)
@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'subscribed_at')
    actions = ['export_emails']

    def export_emails(self, request, queryset):
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="subscribers.csv"'

        writer = csv.writer(response)
        writer.writerow(['Email', 'Subscribed At'])

        for sub in queryset:
            writer.writerow([sub.email, sub.subscribed_at])

        return response

    export_emails.short_description = "Export Selected to CSV"


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

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "date", "price", "status", "pdf_link"]
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

@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    list_display = ['email', 'phone', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['email', 'phone', 'address']
    readonly_fields = ['created_at', 'updated_at']
    
    def has_add_permission(self, request):
        # Only allow one active contact info record
        if ContactInfo.objects.filter(is_active=True).exists():
            return False
        return super().has_add_permission(request)
    
    def save_model(self, request, obj, form, change):
        if obj.is_active:
            # Deactivate all other records when making this one active
            ContactInfo.objects.exclude(pk=obj.pk).update(is_active=False)
        super().save_model(request, obj, form, change)

@admin.register(AboutContent)
class AboutContentAdmin(admin.ModelAdmin):
    list_display = ['title', 'subtitle', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'subtitle', 'content']
    readonly_fields = ['created_at', 'updated_at']
    
    def has_add_permission(self, request):
        # Only allow one active about content record
        if AboutContent.objects.filter(is_active=True).exists():
            return False
        return super().has_add_permission(request)
    
    def save_model(self, request, obj, form, change):
        if obj.is_active:
            # Deactivate all other records when making this one active
            AboutContent.objects.exclude(pk=obj.pk).update(is_active=False)
        super().save_model(request, obj, form, change)

