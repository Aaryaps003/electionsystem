 
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from elections.models import Election, Candidate, EligibleVoter
from audit.services import create_audit_event

from .models import Ballot, VoterParticipation


class VoteRejected(Exception):
    """Raised when a vote fails a business rule."""


class _CrossSectionVoteRejected(VoteRejected):
    """Identifies cross-section rejections for audit logging."""


@transaction.atomic
def _cast_vote_atomic(*, voter: User, election_id: int, candidate_id: int):
    try:
        election = Election.objects.select_for_update().get(
            pk=election_id
        )
    except Election.DoesNotExist:
        raise VoteRejected("Election not found.")

    now = timezone.now()

    if election.status != Election.Status.OPEN:
        raise VoteRejected("This election is not open.")

    if not (election.start_time <= now < election.end_time):
        raise VoteRejected(
            "Voting is outside the permitted time window."
        )

    # Verify that the voter is eligible for this election.
    eligible = EligibleVoter.objects.filter(
        election=election,
        student=voter,
        eligible=True,
    ).exists()

    if not eligible:
        raise VoteRejected(
            "You are not eligible for this election."
        )

    # Ensure the candidate belongs to this election.
    try:
        candidate = Candidate.objects.select_related(
            "student__user"
        ).get(
            pk=candidate_id,
            election=election,
        )
    except Candidate.DoesNotExist:
        raise VoteRejected(
            "The selected candidate does not belong to this election."
        )

    # Require a configured voter profile.
    try:
        voter_profile = voter.student_profile
    except User.student_profile.RelatedObjectDoesNotExist:
        raise VoteRejected(
            "Your student profile is not configured."
        )

    if candidate.student_id is None:
        raise VoteRejected(
            "This candidate does not have a linked student profile."
        )

    candidate_profile = candidate.student

    # Require class and section for both students.
    if (
        not voter_profile.class_name
        or not voter_profile.section
        or not candidate_profile.class_name
        or not candidate_profile.section
    ):
        raise VoteRejected(
            "Class and section must be configured for both students."
        )

    same_class = (
        voter_profile.class_name.strip().casefold()
        == candidate_profile.class_name.strip().casefold()
    )

    same_section = (
        voter_profile.section.strip().casefold()
        == candidate_profile.section.strip().casefold()
    )

    if not same_class or not same_section:
        raise _CrossSectionVoteRejected(
            "You can only vote for a candidate from your own class and section."
        )

    # Lock participation to prevent duplicate voting.
    try:
        participation = (
            VoterParticipation.objects
            .select_for_update()
            .get(election=election, voter=voter)
        )
    except VoterParticipation.DoesNotExist:
        raise VoteRejected(
            "Voting participation has not been initialized."
        )

    if participation.has_voted:
        raise VoteRejected(
            "You have already voted in this election."
        )

    # Save the anonymous ballot separately from voter identity.
    ballot = Ballot.objects.create(
        election=election,
        candidate=candidate,
    )

    participation.has_voted = True
    participation.voted_at = now
    participation.save(
        update_fields=["has_voted", "voted_at"]
    )

    # Accepted-vote audit: do not expose voter or candidate identity.
    create_audit_event(
        event_type="VOTE_CAST",
        election=election,
        actor=None,
        metadata={"result": "accepted"},
    )

    return ballot


def cast_vote(*, voter: User, election_id: int, candidate_id: int):
    """
    Cast a vote atomically.

    Cross-section rejections are audited after the failed vote
    transaction rolls back, allowing the audit event to persist.
    """
    try:
        return _cast_vote_atomic(
            voter=voter,
            election_id=election_id,
            candidate_id=candidate_id,
        )

    except _CrossSectionVoteRejected:
        # The inner atomic transaction has rolled back by this point.
        # Fetch the election and record the rejection independently.
        election = Election.objects.filter(pk=election_id).first()

        create_audit_event(
            event_type="CROSS_SECTION_VOTE_REJECTED",
            election=election,
            actor=None,
            metadata={
                "result": "rejected",
                "reason": "section_mismatch",
            },
        )

        # Preserve the original rejection for the API layer.
        raise
 