from django.urls import path

from . import views

urlpatterns = [
    # admin
    path("admin/login/", views.admin_login),
    path("admin/voters/", views.list_voters),
    path("admin/addVoter/", views.add_voter),
    path("admin/resetPassword/", views.reset_password),
    path("admin/addCandidate/", views.add_candidate),
    path("admin/export/", views.export_results),
    # voter
    path("voter/login/", views.voter_login),
    path("voter/ballot/", views.ballot),
    path("vote/", views.cast_vote),
    # results
    path("results/", views.results),
    path("results/stats/", views.results_stats),
]
