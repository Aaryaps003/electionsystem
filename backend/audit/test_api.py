
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from elections.models import Election
from audit.services import create_audit_event
from audit.models import AuditEvent
User = get_user_model()


class AuditAPITests(APITestCase):
    def setUp(self):
        self.auditor = User.objects.create_user(
            username="audit_tester",
            email="audit_tester@example.com",
            password="TestPass123!",
            role="AUDITOR",
        )

        self.voter = User.objects.create_user(
            username="audit_voter",
            email="audit_voter@example.com",
            password="TestPass123!",
            role="VOTER",
        )

        self.admin = User.objects.create_user(
            username="audit_admin",
            email="audit_admin@example.com",
            password="TestPass123!",
            role="ELECTION_ADMIN",
        )

        now = timezone.now()

        self.election = Election.objects.create(
            title="Audit API Test Election",
            description="Testing audit endpoints",
            start_time=now + timedelta(days=1),
            end_time=now + timedelta(days=2),
            status=Election.Status.DRAFT,
            created_by=self.admin,
        )

        self.other_election = Election.objects.create(
            title="Another Audit Test Election",
            description="Testing audit filtering",
            start_time=now + timedelta(days=3),
            end_time=now + timedelta(days=4),
            status=Election.Status.DRAFT,
            created_by=self.admin,
        )

        create_audit_event(
            event_type="TEST_EVENT_ONE",
            election=self.election,
            actor=self.admin,
            metadata={"source": "test"},
        )

        create_audit_event(
            event_type="TEST_EVENT_TWO",
            election=self.other_election,
            actor=self.admin,
            metadata={"source": "test"},
        )

        self.events_url = "/api/audit/events/"
        self.verify_url = "/api/audit/verify/"

    def test_auditor_can_list_audit_events(self):
        self.client.force_authenticate(user=self.auditor)

        response = self.client.get(self.events_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_auditor_can_verify_audit_chain(self):
        self.client.force_authenticate(user=self.auditor)

        response = self.client.get(self.verify_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["valid"])
        self.assertEqual(
            response.data["reason"],
            "Audit chain verified",
        )

    def test_unauthenticated_user_cannot_access_audit_events(self):
        response = self.client.get(self.events_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_voter_cannot_access_audit_endpoints(self):
        self.client.force_authenticate(user=self.voter)

        events_response = self.client.get(self.events_url)
        verify_response = self.client.get(self.verify_url)

        self.assertEqual(
            events_response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            verify_response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_auditor_can_filter_events_by_election(self):
        self.client.force_authenticate(user=self.auditor)

        response = self.client.get(
            self.events_url,
            {"election_id": self.election.pk},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["event_type"],
            "TEST_EVENT_ONE",
        )

    def test_invalid_election_filter_returns_no_events(self):
        self.client.force_authenticate(user=self.auditor)

        response = self.client.get(
            self.events_url,
            {"election_id": "invalid"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


    def test_verify_endpoint_reports_corrupted_chain(self):
        self.client.force_authenticate(user=self.auditor)

        event = AuditEvent.objects.first()

        AuditEvent.objects.filter(pk=event.pk).update(
            event_hash="f" * 64
        )

        response = self.client.get(self.verify_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_409_CONFLICT,
        )
        self.assertFalse(response.data["valid"])
        self.assertEqual(
            response.data["reason"],
            "Event hash mismatch",
        )
