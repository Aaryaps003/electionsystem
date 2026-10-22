"""Business logic: results, stats, and live broadcasting."""
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models import Count, Q

from .models import Candidate, Voter

GROUP = "results"


def candidate_dict(c):
    return {
        "prn": c.prn,
        "name": c.name,
        "cls": c.cls,
        "division": c.division,
        "votes": c.votes,
        "isNota": c.is_nota,
    }


def results_payload():
    return [candidate_dict(c) for c in Candidate.objects.all()]


def stats_payload():
    total = Voter.objects.count()
    voted = Voter.objects.filter(has_voted=True).count()

    divisions = []
    groups = (
        Voter.objects.values("cls", "division")
        .annotate(total=Count("id"), voted=Count("id", filter=Q(has_voted=True)))
        .order_by("cls", "division")
    )
    for g in groups:
        top = (
            Candidate.objects.filter(cls=g["cls"], division=g["division"], is_nota=False)
            .order_by("-votes", "name")
            .first()
        )
        leader = top if top and top.votes > 0 else None
        divisions.append({
            "cls": g["cls"],
            "division": g["division"],
            "totalVoters": g["total"],
            "votesCast": g["voted"],
            "leaderPrn": leader.prn if leader else None,
            "leaderName": leader.name if leader else None,
            "leaderVotes": leader.votes if leader else 0,
        })

    return {
        "totalVoters": total,
        "votesCast": voted,
        "turnoutPercent": round(voted * 100 / total, 1) if total else 0,
        "divisions": divisions,
    }


def snapshot():
    return {"results": results_payload(), "stats": stats_payload()}


def broadcast_results():
    layer = get_channel_layer()
    if layer is None:
        return
    async_to_sync(layer.group_send)(GROUP, {"type": "results.update", "data": snapshot()})
