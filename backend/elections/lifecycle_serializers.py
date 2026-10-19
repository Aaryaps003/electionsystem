
from rest_framework import serializers

from .models import Election


class ElectionTransitionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[
            Election.Status.SCHEDULED,
            Election.Status.OPEN,
            Election.Status.CLOSED,
            Election.Status.RESULTS_PUBLISHED,
        ]
    )
