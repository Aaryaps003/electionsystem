
from rest_framework.permissions import BasePermission


class IsElectionAdmin(BasePermission):
    """
    Allow access only to authenticated, active election administrators.
    """

    message = "Only election administrators can perform this action."

    def has_permission(self, request, view):
        user = request.user

        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and user.role == "ELECTION_ADMIN"
        )


class IsAuditor(BasePermission):
    """
    Allow access only to authenticated, active auditors.
    """

    message = "Only auditors can perform this action."

    def has_permission(self, request, view):
        user = request.user

        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and user.role == "AUDITOR"
        )


