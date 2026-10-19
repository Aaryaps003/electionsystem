
import hashlib
import json

from django.db import transaction
from django.utils import timezone

from .models import AuditEvent


GENESIS_HASH = ""


def calculate_event_hash(
    event_type,
    election_id,
    actor_id,
    timestamp,
    metadata,
    previous_hash,
):
    payload = {
        "event_type": event_type,
        "election_id": election_id,
        "actor_id": actor_id,
        "timestamp": timestamp.isoformat(),
        "metadata": metadata,
        "previous_hash": previous_hash,
    }

    canonical_json = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    return hashlib.sha256(
        canonical_json.encode("utf-8")
    ).hexdigest()


@transaction.atomic
def create_audit_event(
    event_type,
    election=None,
    actor=None,
    metadata=None,
):
    metadata = metadata or {}

    if not isinstance(metadata, dict):
        raise ValueError("Audit metadata must be a dictionary.")

    # Never put candidate selections or secrets in audit metadata.
    previous_event = (
        AuditEvent.objects
        .order_by("-id")
        .first()
    )

    previous_hash = (
        previous_event.event_hash
        if previous_event
        else GENESIS_HASH
    )

    timestamp = timezone.now()

    event_hash = calculate_event_hash(
        event_type=event_type,
        election_id=election.pk if election else None,
        actor_id=actor.pk if actor else None,
        timestamp=timestamp,
        metadata=metadata,
        previous_hash=previous_hash,
    )

    return AuditEvent.objects.create(
        event_type=event_type,
        election=election,
        actor=actor,
        timestamp=timestamp,
        metadata=metadata,
        previous_hash=previous_hash,
        event_hash=event_hash,
    )


def verify_audit_chain():
    previous_hash = GENESIS_HASH

    for event in AuditEvent.objects.order_by("id"):
        if event.previous_hash != previous_hash:
            return {
                "valid": False,
                "event_id": event.pk,
                "reason": "Previous hash mismatch",
            }

        expected_hash = calculate_event_hash(
            event_type=event.event_type,
            election_id=event.election_id,
            actor_id=event.actor_id,
            timestamp=event.timestamp,
            metadata=event.metadata,
            previous_hash=event.previous_hash,
        )

        if event.event_hash != expected_hash:
            return {
                "valid": False,
                "event_id": event.pk,
                "reason": "Event hash mismatch",
            }

        previous_hash = event.event_hash

    return {
        "valid": True,
        "event_id": None,
        "reason": "Audit chain verified",
    }
