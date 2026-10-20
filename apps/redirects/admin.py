from django.contrib import admin

from apps.redirects.models import LegacyRedirect


@admin.register(LegacyRedirect)
class LegacyRedirectAdmin(admin.ModelAdmin):
    list_display = ("from_path", "to_path", "status_code")
    search_fields = ("from_path", "to_path")
