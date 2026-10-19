from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from audit.services import create_audit_event
from .models import StudentProfile
from .permissions import IsElectionAdmin
from .serializers import StudentManagementSerializer

User = get_user_model()


class StudentListCreateView(generics.ListCreateAPIView):
    serializer_class = StudentManagementSerializer
    permission_classes = [IsElectionAdmin]

    def get_queryset(self):
        return (
            User.objects.filter(role=User.Role.VOTER)
            .select_related("student_profile")
            .order_by("username")
        )

    @transaction.atomic
    def perform_create(self, serializer):
        student = serializer.save()

        create_audit_event(
            event_type="STUDENT_CREATED",
            actor=self.request.user,
            metadata={
                "student_profile_id": student.student_profile.pk,
                "operation": "create",
            },
        )


class StudentDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = StudentManagementSerializer
    permission_classes = [IsElectionAdmin]
    http_method_names = ["get", "patch", "head", "options"]

    def get_queryset(self):
        return (
            User.objects.filter(role=User.Role.VOTER)
            .select_related("student_profile")
        )

    @transaction.atomic
    def perform_update(self, serializer):
        student = serializer.save()

        create_audit_event(
            event_type="STUDENT_UPDATED",
            actor=self.request.user,
            metadata={
                "student_profile_id": student.student_profile.pk,
                "operation": "update",
            },
        )
