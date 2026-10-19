
from rest_framework import serializers


class CandidateResultSerializer(serializers.Serializer):
    candidate_id = serializers.IntegerField()
    candidate_name = serializers.CharField()
    vote_count = serializers.IntegerField()


class ElectionResultsSerializer(serializers.Serializer):
    election_id = serializers.IntegerField()
    election_title = serializers.CharField()
    total_votes = serializers.IntegerField()
    results = CandidateResultSerializer(many=True)
    winners = serializers.ListField(
        child=serializers.CharField()
    )
    is_tie = serializers.BooleanField()
