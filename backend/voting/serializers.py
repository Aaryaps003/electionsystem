
from rest_framework import serializers


class VoterEligibilitySerializer(serializers.Serializer):
    election_id = serializers.IntegerField()
    election_title = serializers.CharField()
    election_status = serializers.CharField()
    eligible = serializers.BooleanField()
    has_voted = serializers.BooleanField()
    can_vote = serializers.BooleanField()
    message = serializers.CharField()


from rest_framework import serializers


class CastVoteSerializer(serializers.Serializer):
    election_id = serializers.IntegerField(min_value=1)
    candidate_id = serializers.IntegerField(min_value=1)


class VoterEligibilitySerializer(serializers.Serializer):
    election_id = serializers.IntegerField()
    election_title = serializers.CharField()
    election_status = serializers.CharField()
    eligible = serializers.BooleanField()
    has_voted = serializers.BooleanField()
    can_vote = serializers.BooleanField()
    message = serializers.CharField()
