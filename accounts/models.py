# accounts/models.py
from django.db import models
from django.contrib.auth.models import User

class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.full_name or self.user.username

class CustomerAddress(models.Model):
    profile = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='addresses')
    street_address = models.CharField(max_length=255)
    apt_suite = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100, null=True, blank=True, default="New York")
    state = models.CharField(max_length=50, null=True, blank=True, default="NY")

    def __str__(self):
        return f"{self.street_address}, {self.zip_code}"

