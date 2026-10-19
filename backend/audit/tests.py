
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from elections.models import Election, Candidate, EligibleVoter
from voting.models import Ballot, VoterParticipation
from voting.services import cast_vote
from audit.models import AuditEvent
from audit.services import create_audit_event, verify_audit_chain


class AuditChainTests(TestCase):

    def setUp(self):
        now = timezone.now()

        self.admin = User.objects.create_user(
            username="audit_admin",
            email="audit_admin@example.com",
            password="TestAdminPass123!",
            role=User.Role.ELECTION_ADMIN,
        )

        self.voter = User.objects.create_user(
            username="audit_voter",
            email="audit_voter@example.com",
            password="TestVoterPass123!",
            role=User.Role.VOTER,
        )

        self.election = Election.objects.create(
            title="Audit Test Election",
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=1),
            status=Election.Status.OPEN,
            created_by=self.admin,
        )

        self.candidate = Candidate.objects.create(
            election=self.election,
            name="Audit Candidate",
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

    def test_new_audit_event_has_valid_hash_chain(self):
        create_audit_event(
            event_type="TEST_EVENT",
            election=self.election,
            actor=self.admin,
            metadata={"action": "test"},
        )

        result = verify_audit_chain()

        self.assertTrue(result["valid"], result)

    def test_each_event_links_to_previous_hash(self):
        first = create_audit_event(
            event_type="FIRST_EVENT",
            metadata={"sequence": 1},
        )

        second = create_audit_event(
            event_type="SECOND_EVENT",
            metadata={"sequence": 2},
        )

        self.assertEqual(second.previous_hash, first.event_hash)

        result = verify_audit_chain()
        self.assertTrue(result["valid"], result)

    def test_metadata_tampering_is_detected(self):
        event = create_audit_event(
            event_type="TAMPER_TEST",
            metadata={"status": "original"},
        )

        # Bypass the model's instance-level save protection deliberately.
        AuditEvent.objects.filter(pk=event.pk).update(
            metadata={"status": "modified"}
        )

        result = verify_audit_chain()

        self.assertFalse(result["valid"])
        self.assertEqual(result["event_id"], event.pk)
        self.assertEqual(result["reason"], "Event hash mismatch")

    def test_accepted_vote_creates_audit_event(self):
        cast_vote(
            voter=self.voter,
            election_id=self.election.pk,
            candidate_id=self.candidate.pk,
        )

        event = AuditEvent.objects.get(event_type="VOTE_CAST")

        self.assertEqual(event.election_id, self.election.pk)
        self.assertIsNone(event.actor_id)
        self.assertEqual(event.metadata, {"result": "accepted"})
        self.assertNotIn("candidate_id", event.metadata)
        self.assertNotIn("voter_id", event.metadata)

        result = verify_audit_chain()
        self.assertTrue(result["valid"], result)


    def test_event_hash_tampering_is_detected(self):
        event = create_audit_event(
            event_type="HASH_TAMPER_TEST",
            metadata={"status": "original"},
        )

        # Deliberately bypass model-level immutability for testing.
        AuditEvent.objects.filter(pk=event.pk).update(
            event_hash="f" * 64
        )

        result = verify_audit_chain()

        self.assertFalse(result["valid"])
        self.assertEqual(result["event_id"], event.pk)
        self.assertEqual(result["reason"], "Event hash mismatch")

    def test_previous_hash_mismatch_is_detected(self):
        first = create_audit_event(
            event_type="CHAIN_FIRST",
            metadata={"sequence": 1},
        )

        second = create_audit_event(
            event_type="CHAIN_SECOND",
            metadata={"sequence": 2},
        )

        # Deliberately corrupt the link for this test.
        AuditEvent.objects.filter(pk=second.pk).update(
            previous_hash="f" * 64
        )

        result = verify_audit_chain()

        self.assertFalse(result["valid"])
        self.assertEqual(result["event_id"], second.pk)
        self.assertEqual(result["reason"], "Previous hash mismatch")

