
from django.conf import settings
from django.db import models

from elections.models import Election, Candidate


class VoterParticipation(models.Model):
    election = models.ForeignKey(
        Election,
        on_delete=models.CASCADE,
        related_name="participation_records",
    )
    voter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="voting_participation",
    )
    has_voted = models.BooleanField(default=False)
    voted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["election", "voter"],
                name="unique_voter_participation",
            ),
        ]

    def __str__(self):
        return (
            f"Participation {self.voter_id} "
            f"- Election {self.election_id}"
        )


class Ballot(models.Model):
    election = models.ForeignKey(
        Election,
        on_delete=models.PROTECT,
        related_name="ballots",
    )
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.PROTECT,
        related_name="ballots",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ballot {self.pk} - Election {self.election_id}"
