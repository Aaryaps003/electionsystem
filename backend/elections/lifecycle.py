
from django.db import transaction
from django.utils import timezone

from audit.services import create_audit_event
from .models import Election


class ElectionTransitionError(Exception):
    pass


ALLOWED_TRANSITIONS = {
    Election.Status.DRAFT: {Election.Status.SCHEDULED},
    Election.Status.SCHEDULED: {Election.Status.OPEN},
    Election.Status.OPEN: {Election.Status.CLOSED},
    Election.Status.CLOSED: {Election.Status.RESULTS_PUBLISHED},
    Election.Status.RESULTS_PUBLISHED: set(),
}


@transaction.atomic
def transition_election(*, election_id, new_status, actor):
    try:
        election = Election.objects.select_for_update().get(
            pk=election_id
        )
    except Election.DoesNotExist:
        raise ElectionTransitionError("Election not found.")

    current_status = election.status

    if new_status not in ALLOWED_TRANSITIONS.get(current_status, set()):
        raise ElectionTransitionError(
            f"Transition from {current_status} to {new_status} is not allowed."
        )

    now = timezone.now()

    if new_status == Election.Status.SCHEDULED:
        if election.start_time <= now:
            raise ElectionTransitionError(
                "An election can only be scheduled if its start time is in the future."
            )

        if not election.candidates.exists():
            raise ElectionTransitionError(
                "Add at least one candidate before scheduling the election."
            )

    elif new_status == Election.Status.OPEN:
        if now < election.start_time:
            raise ElectionTransitionError(
                "The election cannot open before its start time."
            )

        if now >= election.end_time:
            raise ElectionTransitionError(
                "The election cannot open because its end time has passed."
            )

        if not election.candidates.exists():
            raise ElectionTransitionError(
                "An election must have at least one candidate before opening."
            )

    elif new_status == Election.Status.CLOSED:
        if now < election.end_time:
            raise ElectionTransitionError(
                "The election cannot close before its end time."
            )

    election.status = new_status
    election.save(update_fields=["status", "updated_at"])

    create_audit_event(
        event_type="ELECTION_STATUS_CHANGED",
        election=election,
        actor=actor,
        metadata={
            "from_status": current_status,
            "to_status": new_status,
        },
    )

    return election
