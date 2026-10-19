
from django.urls import path

from .views import (
    ElectionListView,
    ElectionDetailView,
    CandidateListView,
    ElectionCreateView,
    CandidateCreateView,
    ElectionTransitionView,
    EligibilityAssignmentView,
)

urlpatterns = [
    # Public election endpoints
    path(
        "",
        ElectionListView.as_view(),
        name="election-list",
    ),
    path(
        "<int:pk>/transition/",
        ElectionTransitionView.as_view(),
        name="election-transition",
    ),
    path(
        "<int:pk>/eligibility/",
        EligibilityAssignmentView.as_view(),
        name="eligibility-assignment",
    ),
    path(
        "<int:pk>/",
        ElectionDetailView.as_view(),
        name="election-detail",
    ),
    path(
        "<int:election_id>/candidates/",
        CandidateListView.as_view(),
        name="candidate-list",
    ),

    # Administrator endpoints
    path(
        "create/",
        ElectionCreateView.as_view(),
        name="election-create",
    ),
    path(
        "candidates/create/",
        CandidateCreateView.as_view(),
        name="candidate-create",
    ),
]
