
from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from elections.models import Election, EligibleVoter
from .serializers import CastVoteSerializer, VoterEligibilitySerializer
from .models import VoterParticipation
from .services import cast_vote, VoteRejected
from rest_framework.permissions import AllowAny
from .results import get_election_results, ResultsError
from .results_serializers import ElectionResultsSerializer

class CastVoteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CastVoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            ballot = cast_vote(
                voter=request.user,
                election_id=serializer.validated_data["election_id"],
                candidate_id=serializer.validated_data["candidate_id"],
            )
        except VoteRejected as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": "Vote recorded successfully.",
                "ballot_id": ballot.pk,
            },
            status=status.HTTP_201_CREATED,
        )


class VoterEligibilityView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, election_id):
        try:
            election = Election.objects.get(pk=election_id)
        except Election.DoesNotExist:
            return Response(
                {"detail": "Election not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        eligible = EligibleVoter.objects.filter(
            election=election,
            student=request.user,
            eligible=True,
        ).exists()

        participation = VoterParticipation.objects.filter(
            election=election,
            voter=request.user,
        ).first()

        has_voted = (
            participation.has_voted
            if participation
            else False
        )

        now = timezone.now()
        within_time = (
            election.start_time <= now < election.end_time
        )

        can_vote = (
            eligible
            and not has_voted
            and election.status == Election.Status.OPEN
            and within_time
        )

        if not eligible:
            message = "You are not eligible for this election."
        elif has_voted:
            message = "You have already voted in this election."
        elif election.status != Election.Status.OPEN:
            message = "This election is not open."
        elif not within_time:
            message = "Voting is outside the permitted time window."
        else:
            message = "You are eligible to vote."

        data = {
            "election_id": election.pk,
            "election_title": election.title,
            "election_status": election.status,
            "eligible": eligible,
            "has_voted": has_voted,
            "can_vote": can_vote,
            "message": message,
        }

        serializer = VoterEligibilitySerializer(data=data)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data)



class ElectionResultsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, election_id):
        try:
            data = get_election_results(
                election_id=election_id
            )
        except ResultsError as exc:
            message = str(exc)

            if message == "Election not found.":
                return Response(
                    {"detail": message},
                    status=status.HTTP_404_NOT_FOUND,
                )

            return Response(
                {"detail": message},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ElectionResultsSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data)
