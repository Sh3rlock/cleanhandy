from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Quote, Service, ServiceCategory, CleaningExtra, HomeType, 
    SquareFeetOption, NewsletterSubscriber, Booking, Contact, 
    Review, ContactInfo, AboutContent, HourlyRate, HandymanQuote, PostEventCleaningQuote
)

# ============================================================================
# ADMIN SITE CUSTOMIZATION
# ============================================================================

# Customize the admin site
admin.site.site_header = "CleanHandy Administration"
admin.site.site_title = "CleanHandy Admin"
admin.site.index_title = "Welcome to CleanHandy Administration"

# Set site URL for better navigation
admin.site.site_url = "/"

# Override the app list to rename the quotes app to "Administration"
original_get_app_list = admin.site.get_app_list

def custom_get_app_list(request):
    """Custom app list that renames the quotes app to Administration"""
    app_list = original_get_app_list(request)
    
    # Rename the quotes app to "Administration"
    for app in app_list:
        if app['app_label'] == 'quotes':
            app['name'] = 'Administration'
            app['verbose_name'] = 'Administration'
            break
    
    return app_list

# Apply the custom app list function
admin.site.get_app_list = custom_get_app_list

# ============================================================================
# BASIC MODEL REGISTRATIONS
# ============================================================================

admin.site.register(Service)
admin.site.register(ServiceCategory)
admin.site.register(CleaningExtra)
admin.site.register(HomeType)
admin.site.register(SquareFeetOption)
admin.site.register(Review)

# ============================================================================
# HOURLY RATE ADMIN - CONFIGURABLE PRICING
# ============================================================================

@admin.register(HourlyRate)
class HourlyRateAdmin(admin.ModelAdmin):
    list_display = [
        'get_service_type_display_formatted', 
        'get_hourly_rate_formatted', 
        'is_active',  # Include actual field for list_editable
        'created_at', 
        'updated_at'
    ]
    list_filter = ['is_active', 'service_type', 'created_at']
    search_fields = ['service_type', 'description']
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ['is_active']
    list_display_links = ['get_service_type_display_formatted']
    list_per_page = 20
    ordering = ['service_type']
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }
    
    fieldsets = (
        ('Rate Information', {
            'fields': ('service_type', 'hourly_rate', 'is_active'),
            'description': 'Configure hourly rates for different service types'
        }),
        ('Description', {
            'fields': ('description',),
            'description': 'Add notes or additional information about this rate'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
            'description': 'Automatically managed timestamps'
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Get readonly fields - make service_type readonly when editing existing objects"""
        try:
            base_readonly = tuple(self.readonly_fields) if self.readonly_fields else ()
            if obj:  # Editing an existing object
                if 'service_type' not in base_readonly:
                    base_readonly = base_readonly + ('service_type',)
            return base_readonly
        except Exception as e:
            print(f"Error in get_readonly_fields: {e}")
            return ('created_at', 'updated_at', 'service_type')
    
    def get_service_type_display_formatted(self, obj):
        """Format service type display with better styling"""
        return format_html(
            '<span style="color: #2E86AB; font-weight: bold;">{}</span>',
            obj.get_service_type_display()
        )
    get_service_type_display_formatted.short_description = 'Service Type'
    
    def get_hourly_rate_formatted(self, obj):
        """Format hourly rate with currency symbol and better styling"""
        return format_html(
            '<span style="color: #28A745; font-weight: bold; font-size: 14px;">${}</span>',
            obj.hourly_rate
        )
    get_hourly_rate_formatted.short_description = 'Hourly Rate'
    
    def get_status_badge(self, obj):
        """Display active status as a colored badge"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28A745; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">✓ Active</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #DC3545; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">✗ Inactive</span>'
            )
    get_status_badge.short_description = 'Status'
    
    actions = ['activate_rates', 'deactivate_rates']
    
    def activate_rates(self, request, queryset):
        try:
            updated = queryset.update(is_active=True)
            self.message_user(request, f'✅ Successfully activated {updated} hourly rate(s).')
        except Exception as e:
            self.message_user(request, f'❌ Error activating rates: {str(e)}', level='ERROR')
    activate_rates.short_description = "🚀 Activate selected hourly rates"
    
    def deactivate_rates(self, request, queryset):
        try:
            updated = queryset.update(is_active=False)
            self.message_user(request, f'✅ Successfully deactivated {updated} hourly rate(s).')
        except Exception as e:
            self.message_user(request, f'❌ Error deactivating rates: {str(e)}', level='ERROR')
    deactivate_rates.short_description = "⏸️ Deactivate selected hourly rates"

# ============================================================================
# NEWSLETTER SUBSCRIBER ADMIN
# ============================================================================

@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'subscribed_at', 'get_status_badge']
    list_filter = ['subscribed_at']
    search_fields = ['email']
    readonly_fields = ['subscribed_at']
    list_per_page = 50
    ordering = ['-subscribed_at']
    
    fieldsets = (
        ('Subscriber Information', {
            'fields': ('email', 'subscribed_at'),
            'description': 'Newsletter subscriber details'
        }),
    )
    
    def get_status_badge(self, obj):
        """Display subscription status as a colored badge"""
        return format_html(
            '<span style="background-color: #17A2B8; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">📧 Subscribed</span>'
        )
    get_status_badge.short_description = 'Status'
    
    actions = ['export_emails']

    def export_emails(self, request, queryset):
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="newsletter_subscribers.csv"'

        writer = csv.writer(response)
        writer.writerow(['Email', 'Subscribed At'])

        for sub in queryset:
            writer.writerow([sub.email, sub.subscribed_at])

        return response

    export_emails.short_description = "📥 Export Selected to CSV"



# ============================================================================
# BOOKING ADMIN
# ============================================================================

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        "id", "get_name_display", "get_service_display", "get_business_type_display", 
        "get_frequency_display", "date", "get_price_formatted", "get_status_badge", "pdf_link"
    ]
    list_filter = ["status", "service_cat", "business_type", "cleaning_frequency", "created_at"]
    search_fields = ["name", "email", "phone", "address", "business_type"]
    readonly_fields = ["pdf_preview", "pdf_file", "created_at"]
    list_per_page = 25
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'email', 'phone', 'status'),
            'description': 'Customer contact information'
        }),
        ('Service Details', {
            'fields': ('service_cat', 'business_type', 'crew_size_hours', 'cleaning_frequency', 'cleaning_type', 'num_cleaners', 'hours_requested'),
            'description': 'Service configuration and requirements'
        }),
        ('Location', {
            'fields': ('address', 'apartment', 'city', 'state', 'zip_code'),
            'description': 'Service location details'
        }),
        ('Scheduling', {
            'fields': ('date', 'hour', 'recurrence_pattern', 'job_description'),
            'description': 'Service scheduling information'
        }),
        ('Marketing', {
            'fields': ('hear_about_us',),
            'description': 'How the customer heard about us'
        }),
        ('Pricing', {
            'fields': ('price', 'gift_card', 'gift_card_discount'),
            'description': 'Pricing and payment information'
        }),
        ('Documents', {
            'fields': ('pdf_preview', 'pdf_file'),
            'description': 'Generated documents'
        }),
    )
    
    def get_name_display(self, obj):
        """Format name display with better styling"""
        return format_html(
            '<span style="color: #2E86AB; font-weight: bold;">{}</span>',
            obj.name
        )
    get_name_display.short_description = 'Customer Name'
    
    def get_service_display(self, obj):
        """Format service display with better styling"""
        if obj.service_cat:
            return format_html(
                '<span style="color: #6F42C1; font-weight: bold;">{}</span>',
                obj.service_cat.name
            )
        return "No Service"
    get_service_display.short_description = 'Service Category'
    
    def get_business_type_display(self, obj):
        """Format business type display with better styling"""
        if obj.business_type:
            return format_html(
                '<span style="color: #17A2B8; font-weight: bold;">{}</span>',
                obj.business_type.replace('_', ' ').title()
            )
        return "Not Specified"
    get_business_type_display.short_description = 'Business Type'
    
    def get_frequency_display(self, obj):
        """Format frequency display with better styling"""
        if obj.cleaning_frequency:
            return format_html(
                '<span style="color: #FD7E14; font-weight: bold;">{}</span>',
                obj.cleaning_frequency.replace('_', ' ').title()
            )
        return "One Time"
    get_frequency_display.short_description = 'Frequency'
    
    def get_price_formatted(self, obj):
        """Format price with currency symbol and better styling"""
        if obj.price:
            return format_html(
                '<span style="color: #28A745; font-weight: bold; font-size: 14px;">${}</span>',
                obj.price
            )
        return "Not Set"
    get_price_formatted.short_description = 'Price'
    
    def get_status_badge(self, obj):
        """Display status as a colored badge"""
        status_colors = {
            'pending': '#FFC107',
            'confirmed': '#28A745',
            'cancelled': '#DC3545',
            'completed': '#17A2B8',
            'in_progress': '#6F42C1'
        }
        color = status_colors.get(obj.status, '#6C757D')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">{}</span>',
            color, obj.status.replace('_', ' ').title()
        )
    get_status_badge.short_description = 'Status'
    
    def pdf_link(self, obj):
        if obj.pdf_file:
            return format_html(
                '<a href="{}" target="_blank" style="color: #007BFF; text-decoration: none;">📄 Download PDF</a>',
                obj.pdf_file.url
            )
        return "No PDF"
    pdf_link.short_description = 'PDF Quote'

    def pdf_preview(self, obj):
        if obj.pdf_file:
            return format_html('<iframe src="{}" width="100%" height="500px" style="border: 1px solid #ddd; border-radius: 4px;"></iframe>', obj.pdf_file.url)
        return "No PDF available"
    pdf_preview.short_description = 'PDF Preview'

# ============================================================================
# CONTACT INFO ADMIN
# ============================================================================

@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    list_display = ['email', 'phone', 'get_status_badge', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['email', 'phone', 'address']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('email', 'phone', 'address'),
            'description': 'Primary contact details'
        }),
        ('Status', {
            'fields': ('is_active',),
            'description': 'Control which contact info is displayed on the website'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
            'description': 'Automatically managed timestamps'
        }),
    )
    
    def get_status_badge(self, obj):
        """Display active status as a colored badge"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28A745; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">✓ Active</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #DC3545; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">✗ Inactive</span>'
            )
    get_status_badge.short_description = 'Status'
    
    # Override the is_active field display in list view
    def is_active(self, obj):
        """Custom display for is_active field in list view"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28A745; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">✓ Active</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #DC3545; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">✗ Inactive</span>'
            )
    is_active.short_description = 'Status'
    is_active.admin_order_field = 'is_active'  # Allow sorting by this field
    
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

# ============================================================================
# ABOUT CONTENT ADMIN
# ============================================================================

@admin.register(AboutContent)
class AboutContentAdmin(admin.ModelAdmin):
    list_display = ['title', 'subtitle', 'get_status_badge', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'subtitle', 'content']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Content Information', {
            'fields': ('title', 'subtitle', 'content'),
            'description': 'About page content details'
        }),
        ('Status', {
            'fields': ('is_active',),
            'description': 'Control which about content is displayed on the website'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
            'description': 'Automatically managed timestamps'
        }),
    )
    
    def get_status_badge(self, obj):
        """Display active status as a colored badge"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28A745; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">✓ Active</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #DC3545; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">✗ Inactive</span>'
            )
    get_status_badge.short_description = 'Status'
    
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

# ============================================================================
# HANDYMAN QUOTE ADMIN
# ============================================================================

@admin.register(HandymanQuote)
class HandymanQuoteAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'get_name_display', 'get_email_display', 'get_phone_display', 
        'get_address_short', 'get_status_badge', 'created_at', 'actions_column'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'email', 'phone_number', 'address', 'job_description']
    readonly_fields = ['created_at']
    list_per_page = 25
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('name', 'email', 'phone_number'),
            'description': 'Customer contact details'
        }),
        ('Job Details', {
            'fields': ('address', 'job_description'),
            'description': 'Location and job requirements'
        }),
        ('Status & Management', {
            'fields': ('status', 'admin_notes'),
            'description': 'Quote status and internal notes'
        }),
        ('System Information', {
            'fields': ('created_at',),
            'classes': ('collapse',),
            'description': 'Automatically managed timestamps'
        }),
    )
    
    def get_name_display(self, obj):
        """Format name display with better styling"""
        return format_html(
            '<span style="color: #2E86AB; font-weight: bold;">{}</span>',
            obj.name
        )
    get_name_display.short_description = 'Customer Name'
    get_name_display.admin_order_field = 'name'
    
    def get_email_display(self, obj):
        """Format email display with better styling"""
        return format_html(
            '<span style="color: #6F42C1; font-weight: bold;">{}</span>',
            obj.email
        )
    get_email_display.short_description = 'Email'
    get_email_display.admin_order_field = 'email'
    
    def get_phone_display(self, obj):
        """Format phone display with better styling"""
        return format_html(
            '<span style="color: #17A2B8; font-weight: bold;">{}</span>',
            obj.phone_number
        )
    get_phone_display.short_description = 'Phone'
    get_phone_display.admin_order_field = 'phone_number'
    
    def get_address_short(self, obj):
        """Display shortened address"""
        if len(obj.address) > 50:
            return format_html(
                '<span style="color: #FD7E14;" title="{}">{}...</span>',
                obj.address, obj.address[:50]
            )
        return format_html(
            '<span style="color: #FD7E14;">{}</span>',
            obj.address
        )
    get_address_short.short_description = 'Address'
    get_address_short.admin_order_field = 'address'
    
    def get_status_badge(self, obj):
        """Display status as a colored badge"""
        status_colors = {
            'pending': '#FFC107',
            'contacted': '#17A2B8',
            'quoted': '#28A745',
            'completed': '#6F42C1',
            'cancelled': '#DC3545'
        }
        status_icons = {
            'pending': '⏳',
            'contacted': '📞',
            'quoted': '💰',
            'completed': '✅',
            'cancelled': '❌'
        }
        color = status_colors.get(obj.status, '#6C757D')
        icon = status_icons.get(obj.status, '❓')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">{} {}</span>',
            color, icon, obj.status.replace('_', ' ').title()
        )
    get_status_badge.short_description = 'Status'
    get_status_badge.admin_order_field = 'status'
    
    def actions_column(self, obj):
        """Display action buttons"""
        return format_html(
            '<div style="display: flex; gap: 5px;">'
            '<a href="/admin/quotes/handymanquote/{}/change/" style="color: #007BFF; text-decoration: none;" title="Edit">✏️</a>'
            '<a href="/admin/quotes/handymanquote/{}/delete/" style="color: #DC3545; text-decoration: none;" title="Delete">🗑️</a>'
            '</div>',
            obj.id, obj.id
        )
    actions_column.short_description = 'Actions'
    
    actions = ['mark_as_contacted', 'mark_as_quoted', 'mark_as_completed', 'mark_as_cancelled', 'export_quotes']
    
    def mark_as_contacted(self, request, queryset):
        """Mark selected quotes as contacted"""
        try:
            updated = queryset.update(status='contacted')
            self.message_user(request, f'✅ Successfully marked {updated} quote(s) as contacted.')
        except Exception as e:
            self.message_user(request, f'❌ Error updating status: {str(e)}', level='ERROR')
    mark_as_contacted.short_description = "📞 Mark as Contacted"
    
    def mark_as_quoted(self, request, queryset):
        """Mark selected quotes as quoted"""
        try:
            updated = queryset.update(status='quoted')
            self.message_user(request, f'✅ Successfully marked {updated} quote(s) as quoted.')
        except Exception as e:
            self.message_user(request, f'❌ Error updating status: {str(e)}', level='ERROR')
    mark_as_quoted.short_description = "💰 Mark as Quoted"
    
    def mark_as_completed(self, request, queryset):
        """Mark selected quotes as completed"""
        try:
            updated = queryset.update(status='completed')
            self.message_user(request, f'✅ Successfully marked {updated} quote(s) as completed.')
        except Exception as e:
            self.message_user(request, f'❌ Error updating status: {str(e)}', level='ERROR')
    mark_as_completed.short_description = "✅ Mark as Completed"
    
    def mark_as_cancelled(self, request, queryset):
        """Mark selected quotes as cancelled"""
        try:
            updated = queryset.update(status='cancelled')
            self.message_user(request, f'✅ Successfully marked {updated} quote(s) as cancelled.')
        except Exception as e:
            self.message_user(request, f'❌ Error updating status: {str(e)}', level='ERROR')
    mark_as_cancelled.short_description = "❌ Mark as Cancelled"
    
    def export_quotes(self, request, queryset):
        """Export selected quotes to CSV"""
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="handyman_quotes.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Name', 'Email', 'Phone', 'Address', 'Job Description', 
            'Status', 'Admin Notes', 'Created At'
        ])

        for quote in queryset:
            writer.writerow([
                quote.id, quote.name, quote.email, quote.phone_number,
                quote.address, quote.job_description, quote.status,
                quote.admin_notes or '', quote.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])

        return response
    export_quotes.short_description = "📥 Export Selected to CSV"
    
    def get_queryset(self, request):
        """Optimize queryset for better performance"""
        return super().get_queryset(request).select_related()
    
    def has_delete_permission(self, request, obj=None):
        """Allow deletion of handyman quotes"""
        return True
    
    def has_add_permission(self, request):
        """Allow adding new handyman quotes"""
        return True
    
    def has_change_permission(self, request, obj=None):
        """Allow editing handyman quotes"""
        return True


# ============================================================================
# POST EVENT CLEANING QUOTE ADMIN
# ============================================================================

@admin.register(PostEventCleaningQuote)
class PostEventCleaningQuoteAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'get_name_display', 'get_email_display', 'get_phone_display', 
        'get_address_short', 'event_type', 'venue_size', 'get_status_badge', 
        'event_date', 'cleaning_date', 'created_at', 'actions_column'
    ]
    list_filter = ['status', 'event_type', 'venue_size', 'created_at', 'event_date']
    search_fields = ['name', 'email', 'phone_number', 'address', 'event_description', 'special_requirements']
    readonly_fields = ['created_at']
    list_per_page = 25
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('name', 'email', 'phone_number', 'address')
        }),
        ('Event Details', {
            'fields': ('event_type', 'venue_size', 'event_date', 'cleaning_date', 'event_description')
        }),
        ('Additional Information', {
            'fields': ('special_requirements',),
            'classes': ('collapse',)
        }),
        ('Quote Management', {
            'fields': ('status', 'admin_notes', 'created_at')
        }),
    )
    
    def get_name_display(self, obj):
        return obj.name
    get_name_display.short_description = 'Name'
    
    def get_email_display(self, obj):
        return obj.email
    get_email_display.short_description = 'Email'
    
    def get_phone_display(self, obj):
        return obj.phone_number
    get_phone_display.short_description = 'Phone'
    
    def get_address_short(self, obj):
        return obj.address[:50] + '...' if len(obj.address) > 50 else obj.address
    get_address_short.short_description = 'Address'
    
    def get_status_badge(self, obj):
        status_colors = {
            'pending': 'warning',
            'contacted': 'info',
            'quoted': 'primary',
            'completed': 'success',
            'cancelled': 'danger'
        }
        color = status_colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_status_display()
        )
    get_status_badge.short_description = 'Status'
    
    def actions_column(self, obj):
        return format_html(
            '<a href="{}" class="btn btn-sm btn-outline-primary">View</a>',
            reverse('admin:quotes_posteventcleaningquote_change', args=[obj.pk])
        )
    actions_column.short_description = 'Actions'
    
    def has_add_permission(self, request):
        """Allow adding post event cleaning quotes"""
        return True
    
    def has_change_permission(self, request, obj=None):
        """Allow editing post event cleaning quotes"""
        return True
    
    def has_delete_permission(self, request, obj=None):
        """Allow deleting post event cleaning quotes"""
        return True

