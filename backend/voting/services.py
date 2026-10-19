
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from elections.models import Election, Candidate, EligibleVoter
from audit.services import create_audit_event

from .models import Ballot, VoterParticipation


class VoteRejected(Exception):
    """Raised when a vote fails a business rule."""


@transaction.atomic
def cast_vote(*, voter: User, election_id: int, candidate_id: int):
    # Lock the election record while processing this vote.
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
        raise VoteRejected("Voting is outside the permitted time window.")

    # Check voter eligibility.
    eligible = EligibleVoter.objects.filter(
        election=election,
        student=voter,
        eligible=True,
    ).exists()

    if not eligible:
        raise VoteRejected("You are not eligible for this election.")

    # Validate the candidate belongs to this election.
    try:
        candidate = Candidate.objects.get(
            pk=candidate_id,
            election=election,
        )
    except Candidate.DoesNotExist:
        raise VoteRejected(
            "The selected candidate does not belong to this election."
        )

    # Participation records should be created when eligibility is assigned.
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
        raise VoteRejected("You have already voted in this election.")

    # Store the ballot separately from voter identity.
    ballot = Ballot.objects.create(
        election=election,
        candidate=candidate,
    )

    participation.has_voted = True
    participation.voted_at = now
    participation.save(
        update_fields=["has_voted", "voted_at"]
    )

    # Do not include the voter ID or candidate selection in audit metadata.
    create_audit_event(
        event_type="VOTE_CAST",
        election=election,
        actor=None,
        metadata={"result": "accepted"},
    )

    return ballot
