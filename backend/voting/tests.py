
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from elections.models import Election, Candidate, EligibleVoter
from voting.models import Ballot, VoterParticipation
from voting.services import cast_vote, VoteRejected


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
            name="Candidate A",
        )

        self.other_candidate = Candidate.objects.create(
            election=self.election,
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

        self.election = Election.objects.create(
            title="API Test Election",
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=1),
            status=Election.Status.OPEN,
            created_by=self.admin,
        )

        self.candidate = Candidate.objects.create(
            election=self.election,
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
        )
        self.assertEqual(
            second_response.status_code,
            status.HTTP_400_BAD_REQUEST,
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
