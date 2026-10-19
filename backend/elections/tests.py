from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import StudentProfile
from audit.models import AuditEvent
from elections.models import Election, Candidate

User = get_user_model()


class ElectionPermissionTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="election_admin_test",
            email="admin_test@example.com",
            password="TestAdminPass123!",
            role="ELECTION_ADMIN",
        )

        self.voter = User.objects.create_user(
            username="election_voter_test",
            email="voter_test@example.com",
            password="TestVoterPass123!",
            role="VOTER",
        )

        self.student_profile = StudentProfile.objects.create(
            user=self.voter,
            student_id="STUDENT-TEST-001",
            department="Computer Science",
            year_of_study=1,
            class_name="MCA FY",
            section="A",
        )

        now = timezone.now()

        self.election = Election.objects.create(
            title="Test Draft Election",
            description="Election used for automated tests",
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            status=Election.Status.DRAFT,
            created_by=self.admin,
        )

    def election_payload(self):
        now = timezone.now()
        return {
            "title": "New Test Election",
            "description": "Created through the API",
            "start_time": (now + timedelta(hours=1)).isoformat(),
            "end_time": (now + timedelta(hours=2)).isoformat(),
        }

    def candidate_payload(self, election_id=None):
        return {
            "election": election_id or self.election.pk,
            "student_profile_id": self.student_profile.pk,
            "name": "Test Candidate",
            "manifesto": "Improving campus life",
            "photo_url": "",
        }

    def test_voter_cannot_create_election(self):
        self.client.force_authenticate(user=self.voter)

        response = self.client.post(
            "/api/elections/create/",
            self.election_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(Election.objects.count(), 1)

    def test_admin_can_create_election(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            "/api/elections/create/",
            self.election_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertTrue(
            Election.objects.filter(
                title="New Test Election"
            ).exists()
        )

        created = Election.objects.get(
            title="New Test Election"
        )
        self.assertEqual(created.created_by, self.admin)
        self.assertEqual(created.status, Election.Status.DRAFT)

    def test_voter_cannot_create_candidate(self):
        self.client.force_authenticate(user=self.voter)

        response = self.client.post(
            "/api/elections/candidates/create/",
            self.candidate_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(Candidate.objects.count(), 0)

    def test_admin_can_add_candidate_to_draft_election(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            "/api/elections/candidates/create/",
            self.candidate_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        candidate = Candidate.objects.get(
            election=self.election,
            name="Test Candidate",
        )

        self.assertEqual(candidate.student, self.student_profile)

        self.assertTrue(
            AuditEvent.objects.filter(
                event_type="CANDIDATE_CREATED",
                election=self.election,
                actor=self.admin,
            ).exists()
        )

    def test_admin_cannot_add_candidate_to_scheduled_election(self):
        self.election.status = Election.Status.SCHEDULED
        self.election.save(update_fields=["status"])

        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            "/api/elections/candidates/create/",
            self.candidate_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertFalse(
            Candidate.objects.filter(
                election=self.election,
                name="Test Candidate",
            ).exists()
        )

    def test_admin_cannot_create_candidate_without_student_profile(self):
        self.client.force_authenticate(user=self.admin)

        payload = self.candidate_payload()
        payload.pop("student_profile_id")

        response = self.client.post(
            "/api/elections/candidates/create/",
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertFalse(
            Candidate.objects.filter(
                election=self.election,
                name="Test Candidate",
            ).exists()
        )

    def test_public_candidate_response_includes_class_and_section(self):
        candidate = Candidate.objects.create(
            election=self.election,
            student=self.student_profile,
            name="Test Candidate",
            manifesto="Improving campus life",
        )

        self.election.status = Election.Status.SCHEDULED
        self.election.save(update_fields=["status"])

        response = self.client.get(
            f"/api/elections/{self.election.pk}/candidates/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        returned_candidate = next(
            item
            for item in response.data
            if item["id"] == candidate.pk
        )

        self.assertEqual(returned_candidate["class_name"], "MCA FY")
        self.assertEqual(returned_candidate["section"], "A")
