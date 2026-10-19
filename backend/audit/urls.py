
from django.urls import path

from .views import (
    AuditEventListView,
    AuditChainVerificationView,
)

urlpatterns = [
    path("events/", AuditEventListView.as_view(), name="audit-events"),
    path("verify/", AuditChainVerificationView.as_view(), name="audit-verify"),
]
