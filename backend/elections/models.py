
from django.conf import settings
from django.db import models
from django.db.models import Q


class Election(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SCHEDULED = "SCHEDULED", "Scheduled"
        OPEN = "OPEN", "Open"
        CLOSED = "CLOSED", "Closed"
        RESULTS_PUBLISHED = "RESULTS_PUBLISHED", "Results Published"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_elections",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(end_time__gt=models.F("start_time")),
                name="election_end_after_start",
            ),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Candidate(models.Model):
    election = models.ForeignKey(
        Election,
        on_delete=models.CASCADE,
        related_name="candidates",
    )
    name = models.CharField(max_length=150)
    manifesto = models.TextField(blank=True)
    photo_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["election", "name"],
                name="unique_candidate_name_per_election",
            ),
        ]
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} - {self.election.title}"


class EligibleVoter(models.Model):
    election = models.ForeignKey(
        Election,
        on_delete=models.CASCADE,
        related_name="eligible_voters",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="election_eligibilities",
    )
    eligible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["election", "student"],
                name="unique_eligible_voter_per_election",
            ),
        ]

    def __str__(self):
        return f"{self.student_id} - {self.election.title}"
