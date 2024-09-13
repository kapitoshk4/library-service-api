from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS


class IsAdminAllOrAuthenticatedReadOnly(permissions.BasePermission):
    def has_permission(self, request, view) -> bool:
        return bool(
            (
                request.method in SAFE_METHODS
                and request.user
                and request.user.is_authenticated
            )
            or (request.user and request.user.is_staff)
        )
