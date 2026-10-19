
from rest_framework import serializers

from .models import Election, Candidate


class CandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = [
            "id",
            "election",
            "name",
            "manifesto",
            "photo_url",
            "created_at",
        ]
        read_only_fields = fields


class ElectionSerializer(serializers.ModelSerializer):
    candidates = CandidateSerializer(many=True, read_only=True)

    class Meta:
        model = Election
        fields = [
            "id",
            "title",
            "description",
            "start_time",
            "end_time",
            "status",
            "created_at",
            "updated_at",
            "candidates",
        ]
        read_only_fields = fields
