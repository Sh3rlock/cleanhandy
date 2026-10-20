from django.contrib import admin

from apps.company.models import CompanyProfile


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Identity", {"fields": ("legal_name", "about", "founded_year", "website", "service_area", "hours")}),
        ("Contact", {"fields": ("phone", "public_email", "info_email")}),
        ("Social", {"fields": ("facebook_url", "instagram_url", "youtube_url", "linkedin_url")}),
        ("Headquarters", {"fields": ("street_address", "city", "region", "postal_code")}),
        ("Moving capabilities", {"fields": ("provides_truck", "provides_packing", "provides_insurance")}),
    )

    def has_add_permission(self, request):
        return not CompanyProfile.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
