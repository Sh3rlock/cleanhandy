# models.py
import uuid
from django.db import models
from django.contrib.auth.models import User


def generate_giftcard_code():
    return uuid.uuid4().hex[:12].upper()

class GiftCard(models.Model):
    code = models.CharField(max_length=12, unique=True, default=generate_giftcard_code)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    balance = models.DecimalField(max_digits=8, decimal_places=2)
    purchaser_email = models.EmailField()
    recipient_email = models.EmailField()
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

# models.py
class DiscountCode(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount_type = models.CharField(choices=[("fixed", "Fixed"), ("percent", "Percent")], max_length=10)
    value = models.DecimalField(max_digits=6, decimal_places=2)
    usage_limit = models.IntegerField(default=1)
    times_used = models.IntegerField(default=0)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def is_valid(self):
        return self.is_active and (self.usage_limit > self.times_used) and (not self.expires_at or timezone.now() < self.expires_at)


