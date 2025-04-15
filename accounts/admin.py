# accounts/admin.py
from django.contrib import admin
from .models import CustomerProfile, CustomerAddress

admin.site.register(CustomerProfile)
admin.site.register(CustomerAddress)

