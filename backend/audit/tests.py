 
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from accounts.models import User, StudentProfile
from elections.models import Election, Candidate, EligibleVoter
from voting.models import Ballot, VoterParticipation
from voting.services import cast_vote, VoteRejected
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

        self.voter_profile = StudentProfile.objects.create(
            user=self.voter,
            student_id="AUDITVOTER001",
            department="MCA",
            year_of_study=1,
            class_name="MCA FY",
            section="A",
        )

        self.candidate_user = User.objects.create_user(
            username="audit_candidate",
            email="audit_candidate@example.com",
            password="TestCandidatePass123!",
            role=User.Role.VOTER,
        )

        self.candidate_profile = StudentProfile.objects.create(
            user=self.candidate_user,
            student_id="AUDITCAND001",
            department="MCA",
            year_of_study=1,
            class_name="MCA FY",
            section="A",
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
            student=self.candidate_profile,
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

        AuditEvent.objects.filter(pk=event.pk).update(
            event_hash="f" * 64
        )

        result = verify_audit_chain()

        self.assertFalse(result["valid"])
        self.assertEqual(result["event_id"], event.pk)
        self.assertEqual(result["reason"], "Event hash mismatch")

    def test_previous_hash_mismatch_is_detected(self):
        create_audit_event(
            event_type="CHAIN_FIRST",
            metadata={"sequence": 1},
        )

        second = create_audit_event(
            event_type="CHAIN_SECOND",
            metadata={"sequence": 2},
        )

        AuditEvent.objects.filter(pk=second.pk).update(
            previous_hash="f" * 64
        )

        result = verify_audit_chain()

        self.assertFalse(result["valid"])
        self.assertEqual(result["event_id"], second.pk)
        self.assertEqual(result["reason"], "Previous hash mismatch")

    def test_rejected_cross_section_vote_is_audited(self):
        section_b_user = User.objects.create_user(
            username="audit_section_b_candidate",
            email="audit_section_b_candidate@example.com",
            password="TestCandidatePass123!",
            role=User.Role.VOTER,
        )

        section_b_profile = StudentProfile.objects.create(
            user=section_b_user,
            student_id="AUDITCAND002",
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
                election_id=self.election.pk,
                candidate_id=section_b_candidate.pk,
            )

        # The rejected attempt must not create a ballot.
        self.assertEqual(Ballot.objects.count(), 0)

        # The rejection event must survive the vote transaction rollback.
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

        # The voter must still be able to vote for a valid candidate.
        participation = VoterParticipation.objects.get(
            election=self.election,
            voter=self.voter,
        )
        self.assertFalse(participation.has_voted)

        # Rejection logging must preserve the hash chain.
        result = verify_audit_chain()
        self.assertTrue(result["valid"], result)
 