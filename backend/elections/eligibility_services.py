
from django.contrib.auth import get_user_model
from django.db import transaction

from audit.services import create_audit_event
from voting.models import VoterParticipation

from .models import Election, EligibleVoter


class EligibilityAssignmentError(Exception):
    pass


@transaction.atomic
def assign_eligible_voter(*, election_id, student_id, actor):
    try:
        election = Election.objects.select_for_update().get(
            pk=election_id
        )
    except Election.DoesNotExist:
        raise EligibilityAssignmentError("Election not found.")

    if election.status != Election.Status.DRAFT:
        raise EligibilityAssignmentError(
            "Voter eligibility can only be managed for draft elections."
        )

    User = get_user_model()

    try:
        student = User.objects.get(pk=student_id)
    except User.DoesNotExist:
        raise EligibilityAssignmentError("Student account not found.")

    if not student.is_active:
        raise EligibilityAssignmentError(
            "An inactive account cannot be made eligible."
        )

    if student.role != "VOTER":
        raise EligibilityAssignmentError(
            "Only voter accounts can be assigned eligibility."
        )

    if EligibleVoter.objects.filter(
        election=election,
        student=student,
    ).exists():
        raise EligibilityAssignmentError(
            "This student has already been assigned to the election."
        )

    EligibleVoter.objects.create(
        election=election,
        student=student,
        eligible=True,
    )

    VoterParticipation.objects.create(
        election=election,
        voter=student,
    )

    create_audit_event(
        event_type="VOTER_ELIGIBILITY_ASSIGNED",
        election=election,
        actor=actor,
        metadata={"student_id": student.pk},
    )

    return student
