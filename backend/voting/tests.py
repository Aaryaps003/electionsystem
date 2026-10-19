 
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User, StudentProfile
from elections.models import Election, Candidate, EligibleVoter
from voting.models import Ballot, VoterParticipation
from voting.services import cast_vote, VoteRejected
from audit.models import AuditEvent
from audit.services import verify_audit_chain


class CastVoteTests(TestCase):

    def setUp(self):
        now = timezone.now()

        self.admin = User.objects.create_user(
            username="admin_test",
            email="admin@example.com",
            password="testpass123",
            role=User.Role.ELECTION_ADMIN,
        )

        self.voter = User.objects.create_user(
            username="voter_test",
            email="voter@example.com",
            password="testpass123",
            role=User.Role.VOTER,
        )

        self.other_voter = User.objects.create_user(
            username="other_voter_test",
            email="other@example.com",
            password="testpass123",
            role=User.Role.VOTER,
        )

        # Voter: MCA FY, Section A
        self.voter_profile = StudentProfile.objects.create(
            user=self.voter,
            student_id="VOTER001",
            department="MCA",
            year_of_study=1,
            class_name="MCA FY",
            section="A",
        )

        # Candidate: MCA FY, Section A
        self.candidate_user = User.objects.create_user(
            username="candidate_test",
            email="candidate@example.com",
            password="TestCandidatePass123!",
            role=User.Role.VOTER,
        )

        self.candidate_profile = StudentProfile.objects.create(
            user=self.candidate_user,
            student_id="CAND001",
            department="MCA",
            year_of_study=1,
            class_name="MCA FY",
            section="A",
        )

        self.election = Election.objects.create(
            title="Test Election",
            description="Election for automated tests",
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=1),
            status=Election.Status.OPEN,
            created_by=self.admin,
        )

        self.candidate = Candidate.objects.create(
            election=self.election,
            student=self.candidate_profile,
            name="Candidate A",
        )

        self.other_candidate = Candidate.objects.create(
            election=self.election,
            student=self.candidate_profile,
            name="Candidate B",
        )

        EligibleVoter.objects.create(
            election=self.election,
            student=self.voter,
            eligible=True,
        )

        VoterParticipation.objects.create(
            election=self.election,
            voter=self.voter,
        )

        VoterParticipation.objects.create(
            election=self.election,
            voter=self.other_voter,
        )

    def test_eligible_voter_can_cast_vote(self):
        ballot = cast_vote(
            voter=self.voter,
            election_id=self.election.id,
            candidate_id=self.candidate.id,
        )

        self.assertEqual(ballot.election_id, self.election.id)
        self.assertEqual(ballot.candidate_id, self.candidate.id)
        self.assertEqual(Ballot.objects.count(), 1)

        participation = VoterParticipation.objects.get(
            election=self.election,
            voter=self.voter,
        )

        self.assertTrue(participation.has_voted)
        self.assertIsNotNone(participation.voted_at)

    def test_ineligible_voter_is_rejected(self):
        with self.assertRaises(VoteRejected):
            cast_vote(
                voter=self.other_voter,
                election_id=self.election.id,
                candidate_id=self.candidate.id,
            )

        self.assertEqual(Ballot.objects.count(), 0)

    def test_candidate_from_another_election_is_rejected(self):
        another_election = Election.objects.create(
            title="Another Election",
            start_time=timezone.now() - timedelta(hours=1),
            end_time=timezone.now() + timedelta(hours=1),
            status=Election.Status.OPEN,
            created_by=self.admin,
        )

        foreign_candidate = Candidate.objects.create(
            election=another_election,
            student=self.candidate_profile,
            name="Foreign Candidate",
        )

        with self.assertRaises(VoteRejected):
            cast_vote(
                voter=self.voter,
                election_id=self.election.id,
                candidate_id=foreign_candidate.id,
            )

        self.assertEqual(Ballot.objects.count(), 0)

    def test_closed_election_rejects_vote(self):
        self.election.status = Election.Status.CLOSED
        self.election.save(update_fields=["status"])

        with self.assertRaises(VoteRejected):
            cast_vote(
                voter=self.voter,
                election_id=self.election.id,
                candidate_id=self.candidate.id,
            )

        self.assertEqual(Ballot.objects.count(), 0)

    def test_voter_cannot_vote_twice(self):
        cast_vote(
            voter=self.voter,
            election_id=self.election.id,
            candidate_id=self.candidate.id,
        )

        with self.assertRaises(VoteRejected):
            cast_vote(
                voter=self.voter,
                election_id=self.election.id,
                candidate_id=self.other_candidate.id,
            )

        self.assertEqual(Ballot.objects.count(), 1)

    def test_voter_cannot_vote_for_candidate_from_another_section(self):
        section_b_user = User.objects.create_user(
            username="section_b_candidate",
            email="section_b_candidate@example.com",
            password="TestCandidatePass123!",
            role=User.Role.VOTER,
        )

        section_b_profile = StudentProfile.objects.create(
            user=section_b_user,
            student_id="CAND002",
            department="MCA",
            year_of_study=1,
            class_name="MCA FY",
            section="B",
        )

        section_b_candidate = Candidate.objects.create(
            election=self.election,
            student=section_b_profile,
            name="Section B Candidate",
        )

        with self.assertRaises(VoteRejected):
            cast_vote(
                voter=self.voter,
                election_id=self.election.id,
                candidate_id=section_b_candidate.id,
            )

        self.assertEqual(Ballot.objects.count(), 0)

        participation = VoterParticipation.objects.get(
            election=self.election,
            voter=self.voter,
        )

        self.assertFalse(participation.has_voted)


class VotingAPITests(APITestCase):

    def setUp(self):
        now = timezone.now()

        self.admin = User.objects.create_user(
            username="api_admin",
            email="api_admin@example.com",
            password="TestAdminPass123!",
            role=User.Role.ELECTION_ADMIN,
        )

        self.voter = User.objects.create_user(
            username="api_voter",
            email="api_voter@example.com",
            password="TestVoterPass123!",
            role=User.Role.VOTER,
        )

        self.other_voter = User.objects.create_user(
            username="api_other",
            email="api_other@example.com",
            password="TestOtherPass123!",
            role=User.Role.VOTER,
        )

        # Voter: MCA FY, Section A
        self.voter_profile = StudentProfile.objects.create(
            user=self.voter,
            student_id="APIVOTER001",
            department="MCA",
            year_of_study=1,
            class_name="MCA FY",
            section="A",
        )

        # Candidate: MCA FY, Section A
        self.candidate_user = User.objects.create_user(
            username="api_candidate",
            email="api_candidate@example.com",
            password="TestCandidatePass123!",
            role=User.Role.VOTER,
        )

        self.candidate_profile = StudentProfile.objects.create(
            user=self.candidate_user,
            student_id="APICAND001",
            department="MCA",
            year_of_study=1,
            class_name="MCA FY",
            section="A",
        )

        self.election = Election.objects.create(
            title="API Test Election",
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=1),
            status=Election.Status.OPEN,
            created_by=self.admin,
        )

        self.candidate = Candidate.objects.create(
            election=self.election,
            student=self.candidate_profile,
            name="API Candidate",
        )

        EligibleVoter.objects.create(
            election=self.election,
            student=self.voter,
            eligible=True,
        )

        VoterParticipation.objects.create(
            election=self.election,
            voter=self.voter,
        )

        VoterParticipation.objects.create(
            election=self.election,
            voter=self.other_voter,
        )

        refresh = RefreshToken.for_user(self.voter)
        self.access_token = str(refresh.access_token)

        self.vote_url = "/api/voting/cast/"

        self.payload = {
            "election_id": self.election.id,
            "candidate_id": self.candidate.id,
        }

    def authenticate_as(self, user):
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

    def test_unauthenticated_request_is_rejected(self):
        response = self.client.post(
            self.vote_url,
            self.payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.assertEqual(Ballot.objects.count(), 0)

    def test_authenticated_voter_can_vote(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )

        response = self.client.post(
            self.vote_url,
            self.payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            response.data,
        )
        self.assertEqual(Ballot.objects.count(), 1)

    def test_duplicate_vote_is_rejected_by_api(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )

        first_response = self.client.post(
            self.vote_url,
            self.payload,
            format="json",
        )

        second_response = self.client.post(
            self.vote_url,
            self.payload,
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED,
            first_response.data,
        )
        self.assertEqual(
            second_response.status_code,
            status.HTTP_400_BAD_REQUEST,
            second_response.data,
        )
        self.assertEqual(Ballot.objects.count(), 1)

    def test_eligible_voter_can_check_eligibility(self):
        self.authenticate_as(self.voter)

        response = self.client.get(
            f"/api/voting/eligibility/{self.election.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertTrue(response.data["eligible"])
        self.assertFalse(response.data["has_voted"])
        self.assertTrue(response.data["can_vote"])

    def test_ineligible_voter_cannot_vote(self):
        self.authenticate_as(self.other_voter)

        response = self.client.get(
            f"/api/voting/eligibility/{self.election.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertFalse(response.data["eligible"])
        self.assertFalse(response.data["has_voted"])
        self.assertFalse(response.data["can_vote"])

    def test_nonexistent_election_returns_404(self):
        self.authenticate_as(self.voter)

        response = self.client.get(
            "/api/voting/eligibility/999999/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_api_rejects_candidate_from_another_section(self):
        section_b_user = User.objects.create_user(
            username="api_section_b_candidate",
            email="api_section_b_candidate@example.com",
            password="TestCandidatePass123!",
            role=User.Role.VOTER,
        )

        section_b_profile = StudentProfile.objects.create(
            user=section_b_user,
            student_id="APISECCAND002",
            department="MCA",
            year_of_study=1,
            class_name="MCA FY",
            section="B",
        )

        section_b_candidate = Candidate.objects.create(
            election=self.election,
            student=section_b_profile,
            name="API Section B Candidate",
        )

        self.authenticate_as(self.voter)

        payload = {
            "election_id": self.election.id,
            "candidate_id": section_b_candidate.id,
        }

        response = self.client.post(
            self.vote_url,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            response.data,
        )

        self.assertEqual(Ballot.objects.count(), 0)

        participation = VoterParticipation.objects.get(
            election=self.election,
            voter=self.voter,
        )

        self.assertFalse(participation.has_voted)

        # The API rejection must be recorded without voter or candidate identity.
        event = AuditEvent.objects.get(
            event_type="CROSS_SECTION_VOTE_REJECTED"
        )
        self.assertEqual(event.election_id, self.election.pk)
        self.assertIsNone(event.actor_id)
        self.assertEqual(
            event.metadata,
            {
                "result": "rejected",
                "reason": "section_mismatch",
            },
        )
        self.assertNotIn("voter_id", event.metadata)
        self.assertNotIn("candidate_id", event.metadata)

        # The rejection event must preserve the audit hash chain.
        chain_result = verify_audit_chain()
        self.assertTrue(chain_result["valid"], chain_result)
 
