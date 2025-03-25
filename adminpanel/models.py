# models.py (in quotes or adminpanel app)

from django.db import models

class BlockedTimeSlot(models.Model):
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    reason = models.CharField(max_length=255, blank=True)
    all_day = models.BooleanField(default=False)  # ✅ New field

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.all_day:
            return f"{self.date} (All Day Blocked)"
        return f"{self.date} | {self.start_time}–{self.end_time} ({self.reason})"
