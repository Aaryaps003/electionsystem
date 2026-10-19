
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from elections.models import Election


class AuditEvent(models.Model):
    election = models.ForeignKey(
        Election,
        on_delete=models.PROTECT,
        related_name="audit_events",
        null=True,
        blank=True,
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="audit_events",
        null=True,
        blank=True,
    )
    event_type = models.CharField(max_length=50)
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    previous_hash = models.CharField(max_length=64, blank=True, default="")
    event_hash = models.CharField(max_length=64, unique=True)

    class Meta:
        ordering = ["id"]

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError("Audit events cannot be modified.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Audit events cannot be deleted.")

    def __str__(self):
        return f"{self.event_type} - {self.timestamp}"
