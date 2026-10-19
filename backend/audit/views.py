
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAuditor
from .models import AuditEvent
from .serializers import AuditEventSerializer
from .services import verify_audit_chain


class AuditEventListView(generics.ListAPIView):
    serializer_class = AuditEventSerializer
    permission_classes = [IsAuthenticated, IsAuditor]

    def get_queryset(self):
        queryset = (
            AuditEvent.objects
            .select_related("actor", "election")
            .order_by("id")
        )

        election_id = self.request.query_params.get("election_id")

        if election_id is not None:
            if not election_id.isdigit() or int(election_id) < 1:
                return AuditEvent.objects.none()

            queryset = queryset.filter(
                election_id=int(election_id)
            )

        return queryset


class AuditChainVerificationView(APIView):
    permission_classes = [IsAuthenticated, IsAuditor]

    def get(self, request):
        result = verify_audit_chain()

        response_status = (
            status.HTTP_200_OK
            if result["valid"]
            else status.HTTP_409_CONFLICT
        )

        return Response(result, status=response_status)
