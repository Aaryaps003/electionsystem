
from django.db.models import Count

from elections.models import Election, Candidate
from .models import Ballot


class ResultsError(Exception):
    pass


def get_election_results(*, election_id):
    try:
        election = Election.objects.get(pk=election_id)
    except Election.DoesNotExist:
        raise ResultsError("Election not found.")

    if election.status != Election.Status.RESULTS_PUBLISHED:
        raise ResultsError(
            "Results are not available for this election."
        )

    candidates = (
        Candidate.objects.filter(election=election)
        .annotate(vote_count=Count("ballots"))
        .order_by("name")
    )

    results = [
        {
            "candidate_id": candidate.pk,
            "candidate_name": candidate.name,
            "vote_count": candidate.vote_count,
        }
        for candidate in candidates
    ]

    total_votes = Ballot.objects.filter(
        election=election
    ).count()

    highest_votes = max(
        (item["vote_count"] for item in results),
        default=0,
    )

    winners = [
        item["candidate_name"]
        for item in results
        if item["vote_count"] == highest_votes
    ] if results else []

    return {
        "election_id": election.pk,
        "election_title": election.title,
        "total_votes": total_votes,
        "results": results,
        "winners": winners,
        "is_tie": len(winners) > 1,
    }
