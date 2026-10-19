
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from audit.models import AuditEvent
from elections.models import Election, EligibleVoter
from voting.models import VoterParticipation

User = get_user_model()


class EligibilityAssignmentTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="eligibility_admin",
            email="eligibility_admin@example.com",
            password="TestAdminPass123!",
            role="ELECTION_ADMIN",
        )

        self.voter = User.objects.create_user(
            username="eligibility_voter",
            email="eligibility_voter@example.com",
            password="TestVoterPass123!",
            role="VOTER",
        )

        now = timezone.now()

        self.election = Election.objects.create(
            title="Eligibility Test Election",
            description="Election for eligibility tests",
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            status=Election.Status.DRAFT,
            created_by=self.admin,
        )

        self.url = (
            f"/api/elections/{self.election.pk}/eligibility/"
        )

    def assign(self, student_id=None, user=None):
        if user is not None:
            self.client.force_authenticate(user=user)

        return self.client.post(
            self.url,
            {"student_id": student_id or self.voter.pk},
            format="json",
        )

    def test_admin_can_assign_eligible_voter(self):
        self.client.force_authenticate(user=self.admin)

        response = self.assign()

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertTrue(
            EligibleVoter.objects.filter(
                election=self.election,
                student=self.voter,
                eligible=True,
            ).exists()
        )

    def test_assignment_creates_participation_record(self):
        self.client.force_authenticate(user=self.admin)

        response = self.assign()

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertTrue(
            VoterParticipation.objects.filter(
                election=self.election,
                voter=self.voter,
                has_voted=False,
            ).exists()
        )

    def test_assignment_creates_audit_event(self):
        self.client.force_authenticate(user=self.admin)

        response = self.assign()

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        event = AuditEvent.objects.get(
            election=self.election,
            event_type="VOTER_ELIGIBILITY_ASSIGNED",
        )
        self.assertEqual(event.actor, self.admin)
        self.assertEqual(
            event.metadata["student_id"],
            self.voter.pk,
        )

    def test_duplicate_assignment_is_rejected(self):
        self.client.force_authenticate(user=self.admin)

        first_response = self.assign()
        second_response = self.assign()

        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(
            second_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            EligibleVoter.objects.filter(
                election=self.election,
                student=self.voter,
            ).count(),
            1,
        )
        self.assertEqual(
            VoterParticipation.objects.filter(
                election=self.election,
                voter=self.voter,
            ).count(),
            1,
        )

    def test_voter_cannot_assign_eligibility(self):
        self.client.force_authenticate(user=self.voter)

        response = self.assign()

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertFalse(
            EligibleVoter.objects.filter(
                election=self.election,
            ).exists()
        )

    def test_inactive_account_cannot_be_assigned(self):
        self.voter.is_active = False
        self.voter.save(update_fields=["is_active"])

        self.client.force_authenticate(user=self.admin)

        response = self.assign()

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertFalse(
            EligibleVoter.objects.filter(
                election=self.election,
                student=self.voter,
            ).exists()
        )

    def test_nonexistent_student_returns_404(self):
        self.client.force_authenticate(user=self.admin)

        response = self.assign(student_id=99999)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_nonexistent_election_returns_404(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            "/api/elections/99999/eligibility/",
            {"student_id": self.voter.pk},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
