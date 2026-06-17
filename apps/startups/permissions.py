from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsStartupOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class IsStartupOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role == "admin":
            return True
        return obj.owner == request.user


class CanCreateStartup(BasePermission):
    def has_permission(self, request, view):
        if view.action in ("create",):
            return request.user.is_authenticated and request.user.role == "entrepreneur"
        return True


class CanManageStartup(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if request.user.role == "admin":
            return True
        return obj.owner == request.user and request.user.role == "entrepreneur"
