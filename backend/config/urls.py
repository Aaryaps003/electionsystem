
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/elections/", include("elections.urls")),
    path("api/voting/", include("voting.urls")),
    path("api/audit/", include("audit.urls")),
]
