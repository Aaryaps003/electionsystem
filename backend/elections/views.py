
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import ValidationError

from accounts.permissions import IsElectionAdmin
from audit.services import create_audit_event

from .models import Election, Candidate
from .serializers import ElectionSerializer, CandidateSerializer
from .admin_serializers import (
    ElectionCreateSerializer,
    CandidateCreateSerializer,
)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as http_status

from .lifecycle import (
    transition_election,
    ElectionTransitionError,
)
from .lifecycle_serializers import ElectionTransitionSerializer


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as http_status

from .eligibility_services import (
    assign_eligible_voter,
    EligibilityAssignmentError,
)
from .eligibility_serializers import EligibilityAssignmentSerializer

class ElectionListView(generics.ListAPIView):
    serializer_class = ElectionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Election.objects.exclude(
            status=Election.Status.DRAFT
        ).prefetch_related("candidates")


class ElectionDetailView(generics.RetrieveAPIView):
    serializer_class = ElectionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Election.objects.exclude(
            status=Election.Status.DRAFT
        ).prefetch_related("candidates")


class CandidateListView(generics.ListAPIView):
    serializer_class = CandidateSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Candidate.objects.filter(
            election_id=self.kwargs["election_id"]
        ).exclude(
            election__status=Election.Status.DRAFT
        )


class ElectionCreateView(generics.CreateAPIView):
    serializer_class = ElectionCreateSerializer
    permission_classes = [IsElectionAdmin]

    def perform_create(self, serializer):
        election = serializer.save(
            created_by=self.request.user,
            status=Election.Status.DRAFT,
        )

        create_audit_event(
            event_type="ELECTION_CREATED",
            election=election,
            actor=self.request.user,
            metadata={"status": election.status},
        )


class CandidateCreateView(generics.CreateAPIView):
    serializer_class = CandidateCreateSerializer
    permission_classes = [IsElectionAdmin]

    def perform_create(self, serializer):
        candidate = serializer.save()

        create_audit_event(
            event_type="CANDIDATE_CREATED",
            election=candidate.election,
            actor=self.request.user,
            metadata={"candidate_id": candidate.pk},
        )



class ElectionTransitionView(APIView):
    permission_classes = [IsElectionAdmin]

    def post(self, request, pk):
        serializer = ElectionTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            election = transition_election(
                election_id=pk,
                new_status=serializer.validated_data["status"],
                actor=request.user,
            )
        except ElectionTransitionError as exc:
            message = str(exc)

            if message == "Election not found.":
                return Response(
                    {"detail": message},
                    status=http_status.HTTP_404_NOT_FOUND,
                )

            return Response(
                {"detail": message},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "id": election.pk,
                "title": election.title,
                "status": election.status,
            },
            status=http_status.HTTP_200_OK,
        )



class EligibilityAssignmentView(APIView):
    permission_classes = [IsElectionAdmin]

    def post(self, request, pk):
        serializer = EligibilityAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            student = assign_eligible_voter(
                election_id=pk,
                student_id=serializer.validated_data["student_id"],
                actor=request.user,
            )
        except EligibilityAssignmentError as exc:
            message = str(exc)

            if message in {
                "Election not found.",
                "Student account not found.",
            }:
                return Response(
                    {"detail": message},
                    status=http_status.HTTP_404_NOT_FOUND,
                )

            return Response(
                {"detail": message},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": "Voter eligibility assigned successfully.",
                "election_id": pk,
                "student_id": student.pk,
            },
            status=http_status.HTTP_201_CREATED,
        )
