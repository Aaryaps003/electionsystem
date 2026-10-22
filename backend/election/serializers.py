from rest_framework import serializers

from .models import Candidate, Voter


class VoterSerializer(serializers.ModelSerializer):
    hasVoted = serializers.BooleanField(source="has_voted", read_only=True)
    cls = serializers.CharField(max_length=30)
    username = serializers.CharField(max_length=60)
    password = serializers.CharField(write_only=True, min_length=6, trim_whitespace=False)

    class Meta:
        model = Voter
        fields = ["prn", "name", "cls", "division", "username", "password", "hasVoted"]

    def validate_prn(self, value):
        return value.strip()

    def validate_division(self, value):
        return value.strip().upper()

    def validate_username(self, value):
        value = value.strip().lower()
        if Voter.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("That username is already taken.")
        return value

    def create(self, validated_data):
        raw = validated_data.pop("password")
        voter = Voter(**validated_data)
        voter.set_password(raw)
        voter.save()
        return voter


class CandidateInputSerializer(serializers.ModelSerializer):
    cls = serializers.CharField(max_length=30)

    class Meta:
        model = Candidate
        fields = ["prn", "name", "cls", "division"]

    def validate_prn(self, value):
        return value.strip()

    def validate_division(self, value):
        return value.strip().upper()
