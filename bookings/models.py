from django.db import models
from quotes.models import Quote

class Booking(models.Model):
    quote = models.OneToOneField(Quote, on_delete=models.CASCADE)
    confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking {self.id} - {self.quote.name}"
