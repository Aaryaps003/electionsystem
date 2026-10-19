
from rest_framework import serializers

from .models import Election, Candidate


class ElectionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Election
        fields = [
            "id",
            "title",
            "description",
            "start_time",
            "end_time",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        start_time = attrs.get("start_time")
        end_time = attrs.get("end_time")

        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError(
                "Election end time must be after its start time."
            )

        return attrs


class CandidateCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = [
            "id",
            "election",
            "name",
            "manifesto",
            "photo_url",
        ]
        read_only_fields = ["id"]

    def validate_election(self, election):
        if election.status != Election.Status.DRAFT:
            raise serializers.ValidationError(
                "Candidates can only be added to draft elections."
            )

        return election
