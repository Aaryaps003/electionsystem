
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        VOTER = "VOTER", "Voter"
        ELECTION_ADMIN = "ELECTION_ADMIN", "Election Administrator"
        AUDITOR = "AUDITOR", "Auditor"

    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.VOTER,
    )

    def __str__(self):
        return f"{self.username} ({self.role})"



class StudentProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )
    student_id = models.CharField(max_length=30, unique=True)
    department = models.CharField(max_length=100, blank=True)
    year_of_study = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    # NEW: academic grouping for section-based voting
    class_name = models.CharField(max_length=100, blank=True)
    section = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.student_id} - {self.user.username}"

