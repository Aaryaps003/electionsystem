
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from audit.models import AuditEvent
from elections.models import Election, Candidate

User = get_user_model()


class ElectionLifecycleTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="lifecycle_admin",
            email="lifecycle_admin@example.com",
            password="TestAdminPass123!",
            role="ELECTION_ADMIN",
        )

        self.voter = User.objects.create_user(
            username="lifecycle_voter",
            email="lifecycle_voter@example.com",
            password="TestVoterPass123!",
            role="VOTER",
        )

        now = timezone.now()

        self.election = Election.objects.create(
            title="Lifecycle Test Election",
            description="Election for lifecycle tests",
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            status=Election.Status.DRAFT,
            created_by=self.admin,
        )

        Candidate.objects.create(
            election=self.election,
            name="Lifecycle Candidate",
            manifesto="Test manifesto",
        )

    def transition(self, new_status, user=None):
        if user is not None:
            self.client.force_authenticate(user=user)

        return self.client.post(
            f"/api/elections/{self.election.pk}/transition/",
            {"status": new_status},
            format="json",
        )

    def test_admin_can_schedule_draft_election(self):
        response = self.transition(
            Election.Status.SCHEDULED,
            self.admin,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.election.refresh_from_db()
        self.assertEqual(
            self.election.status,
            Election.Status.SCHEDULED,
        )

    def test_voter_cannot_transition_election(self):
        response = self.transition(
            Election.Status.SCHEDULED,
            self.voter,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.election.refresh_from_db()
        self.assertEqual(self.election.status, Election.Status.DRAFT)

    def test_invalid_transition_is_rejected(self):
        response = self.transition(
            Election.Status.OPEN,
            self.admin,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.election.refresh_from_db()
        self.assertEqual(self.election.status, Election.Status.DRAFT)

    def test_scheduling_requires_future_start_time(self):
        self.election.start_time = timezone.now() - timedelta(minutes=5)
        self.election.save(update_fields=["start_time"])

        response = self.transition(
            Election.Status.SCHEDULED,
            self.admin,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.election.refresh_from_db()
        self.assertEqual(self.election.status, Election.Status.DRAFT)

    def test_scheduling_records_audit_event(self):
        response = self.transition(
            Election.Status.SCHEDULED,
            self.admin,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        event = AuditEvent.objects.get(
            election=self.election,
            event_type="ELECTION_STATUS_CHANGED",
        )

        self.assertEqual(event.actor, self.admin)
        self.assertEqual(
            event.metadata["from_status"],
            Election.Status.DRAFT,
        )
        self.assertEqual(
            event.metadata["to_status"],
            Election.Status.SCHEDULED,
        )

    def test_scheduling_requires_at_least_one_candidate(self):
        Candidate.objects.filter(election=self.election).delete()

        response = self.transition(
            Election.Status.SCHEDULED,
            self.admin,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.election.refresh_from_db()
        self.assertEqual(self.election.status, Election.Status.DRAFT)



    def test_cannot_open_before_start_time(self):
        self.election.status = Election.Status.SCHEDULED
        self.election.save(update_fields=["status"])

        response = self.transition(
            Election.Status.OPEN,
            self.admin,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.election.refresh_from_db()
        self.assertEqual(
            self.election.status,
            Election.Status.SCHEDULED,
        )

    def test_cannot_open_after_end_time(self):
        now = timezone.now()
        self.election.status = Election.Status.SCHEDULED
        self.election.start_time = now - timedelta(hours=2)
        self.election.end_time = now - timedelta(hours=1)
        self.election.save(
            update_fields=["status", "start_time", "end_time"]
        )

        response = self.transition(
            Election.Status.OPEN,
            self.admin,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.election.refresh_from_db()
        self.assertEqual(
            self.election.status,
            Election.Status.SCHEDULED,
        )

    def test_cannot_close_before_end_time(self):
        self.election.status = Election.Status.OPEN
        self.election.save(update_fields=["status"])

        response = self.transition(
            Election.Status.CLOSED,
            self.admin,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.election.refresh_from_db()
        self.assertEqual(
            self.election.status,
            Election.Status.OPEN,
        )

    def test_cannot_publish_results_before_closing(self):
        self.election.status = Election.Status.OPEN
        self.election.save(update_fields=["status"])

        response = self.transition(
            Election.Status.RESULTS_PUBLISHED,
            self.admin,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.election.refresh_from_db()
        self.assertEqual(
            self.election.status,
            Election.Status.OPEN,
        )

    def test_nonexistent_election_returns_404(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            "/api/elections/99999/transition/",
            {"status": Election.Status.SCHEDULED},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
