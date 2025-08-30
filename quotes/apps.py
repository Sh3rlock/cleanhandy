from django.apps import AppConfig


class QuotesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'quotes'
    verbose_name = 'Administration'  # This changes the app name in Django admin
