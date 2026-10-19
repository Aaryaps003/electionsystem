from rest_framework import serializers

from accounts.models import StudentProfile
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
    student_profile_id = serializers.PrimaryKeyRelatedField(
        source="student",
        queryset=StudentProfile.objects.select_related("user").filter(
            user__role="VOTER",
            user__is_active=True,
        ),
        write_only=True,
    )

    class Meta:
        model = Candidate
        fields = [
            "id",
            "election",
            "student_profile_id",
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

    def validate(self, attrs):
        student_profile = attrs.get("student")

        if student_profile is None:
            raise serializers.ValidationError({
                "student_profile_id": (
                    "A registered student profile is required."
                )
            })

        if not student_profile.class_name.strip():
            raise serializers.ValidationError({
                "student_profile_id": (
                    "The student's class must be configured."
                )
            })

        if not student_profile.section.strip():
            raise serializers.ValidationError({
                "student_profile_id": (
                    "The student's section must be configured."
                )
            })

        return attrs
