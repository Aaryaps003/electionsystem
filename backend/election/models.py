from django.contrib.auth.hashers import check_password, make_password
from django.db import models


class Voter(models.Model):
    prn = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=120)
    cls = models.CharField("class", max_length=30)
    division = models.CharField(max_length=10)
    has_voted = models.BooleanField(default=False)

    # Login credentials. The password is stored hashed, never in plain text.
    username = models.CharField(max_length=60, unique=True, null=True, blank=True)
    password = models.CharField(max_length=128, blank=True, default="")

    class Meta:
        ordering = ["cls", "division", "prn"]

    def set_password(self, raw):
        self.password = make_password(raw)

    def check_password(self, raw):
        return bool(self.password) and check_password(raw, self.password)

    def __str__(self):
        return f"{self.prn} - {self.name}"


class Candidate(models.Model):
    """A candidate for a class + division. NOTA is stored as a candidate with is_nota=True."""

    prn = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=120)
    cls = models.CharField("class", max_length=30)
    division = models.CharField(max_length=10)
    votes = models.PositiveIntegerField(default=0)
    is_nota = models.BooleanField(default=False)

    class Meta:
        ordering = ["cls", "division", "is_nota", "name"]

    def __str__(self):
        return f"{self.name} ({self.cls}-{self.division})"
