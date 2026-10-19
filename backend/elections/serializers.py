from rest_framework import serializers

from .models import Election, Candidate


class CandidateSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(
        source="student.class_name",
        read_only=True,
        allow_null=True,
    )
    section = serializers.CharField(
        source="student.section",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = Candidate
        fields = [
            "id",
            "election",
            "name",
            "manifesto",
            "photo_url",
            "class_name",
            "section",
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
