
from django.urls import path

from .views import (
    CastVoteView,
    VoterEligibilityView,
    ElectionResultsView,
)

urlpatterns = [
    path("cast/", CastVoteView.as_view(), name="cast-vote"),
    path(
        "eligibility/<int:election_id>/",
        VoterEligibilityView.as_view(),
        name="voter-eligibility",
    ),
    path(
        "results/<int:election_id>/",
        ElectionResultsView.as_view(),
        name="election-results",
    ),
]
