
from rest_framework import serializers

from .models import AuditEvent


class AuditEventSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(
        source="actor.username",
        read_only=True,
        default=None,
    )

    election_title = serializers.CharField(
        source="election.title",
        read_only=True,
        default=None,
    )

    class Meta:
        model = AuditEvent
        fields = [
            "id",
            "event_type",
            "election",
            "election_title",
            "actor",
            "actor_username",
            "timestamp",
            "metadata",
            "previous_hash",
            "event_hash",
        ]
        read_only_fields = fields
