from django.core.exceptions import ValidationError
from django.db import models


class LegacyRedirect(models.Model):
    from_path = models.CharField(max_length=300, unique=True)
    to_path = models.CharField(max_length=300)
    status_code = models.PositiveSmallIntegerField(default=301)

    class Meta:
        ordering = ["from_path"]

    def __str__(self):
        return f"{self.from_path} → {self.to_path}"

    def clean(self):
        if not self.from_path.startswith("/") or self.from_path.startswith("//"):
            raise ValidationError({"from_path": "Use a site path that starts with a single slash."})
        if not self.to_path.startswith("/") or self.to_path.startswith("//"):
            raise ValidationError({"to_path": "Use a site path that starts with a single slash."})
        if self.status_code not in (301, 302):
            raise ValidationError({"status_code": "Use 301 or 302."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
