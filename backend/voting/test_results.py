
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from elections.models import Election, Candidate
from voting.models import Ballot

User = get_user_model()


class ElectionResultsTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="results_admin",
            email="results_admin@example.com",
            password="TestAdminPass123!",
            role="ELECTION_ADMIN",
        )

        now = timezone.now()

        self.election = Election.objects.create(
            title="Results Test Election",
            description="Testing results counting",
            start_time=now - timedelta(hours=2),
            end_time=now - timedelta(hours=1),
            status=Election.Status.CLOSED,
            created_by=self.admin,
        )

        self.candidate_a = Candidate.objects.create(
            election=self.election,
            name="Candidate Alpha",
        )

        self.candidate_b = Candidate.objects.create(
            election=self.election,
            name="Candidate Beta",
        )

        self.candidate_c = Candidate.objects.create(
            election=self.election,
            name="Candidate Gamma",
        )

        self.url = (
            f"/api/voting/results/{self.election.pk}/"
        )

    def publish_results(self):
        self.election.status = Election.Status.RESULTS_PUBLISHED
        self.election.save(update_fields=["status"])

    def test_results_are_hidden_before_publication(self):
        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_results_endpoint_returns_404_for_missing_election(self):
        response = self.client.get(
            "/api/voting/results/99999/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_results_count_ballots_per_candidate(self):
        Ballot.objects.create(
            election=self.election,
            candidate=self.candidate_a,
        )
        Ballot.objects.create(
            election=self.election,
            candidate=self.candidate_a,
        )
        Ballot.objects.create(
            election=self.election,
            candidate=self.candidate_b,
        )

        self.publish_results()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_votes"], 3)

        counts = {
            item["candidate_name"]: item["vote_count"]
            for item in response.data["results"]
        }

        self.assertEqual(counts["Candidate Alpha"], 2)
        self.assertEqual(counts["Candidate Beta"], 1)
        self.assertEqual(counts["Candidate Gamma"], 0)

    def test_results_identify_a_single_winner(self):
        Ballot.objects.create(
            election=self.election,
            candidate=self.candidate_a,
        )
        Ballot.objects.create(
            election=self.election,
            candidate=self.candidate_a,
        )
        Ballot.objects.create(
            election=self.election,
            candidate=self.candidate_b,
        )

        self.publish_results()

        response = self.client.get(self.url)

        self.assertEqual(
            response.data["winners"],
            ["Candidate Alpha"],
        )
        self.assertFalse(response.data["is_tie"])

    def test_results_identify_tied_candidates(self):
        Ballot.objects.create(
            election=self.election,
            candidate=self.candidate_a,
        )
        Ballot.objects.create(
            election=self.election,
            candidate=self.candidate_b,
        )

        self.publish_results()

        response = self.client.get(self.url)

        self.assertEqual(
            set(response.data["winners"]),
            {"Candidate Alpha", "Candidate Beta"},
        )
        self.assertTrue(response.data["is_tie"])

    def test_results_are_hidden_while_election_is_open(self):
        self.election.status = Election.Status.OPEN
        self.election.save(update_fields=["status"])

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
