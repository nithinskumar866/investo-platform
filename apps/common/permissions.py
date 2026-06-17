from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request
from rest_framework.views import View


class IsOwner(BasePermission):
    def has_object_permission(self, request: Request, view: View, obj) -> bool:
        if hasattr(obj, "owner"):
            return obj.owner == request.user
        if hasattr(obj, "user"):
            return obj.user == request.user
        return False


class IsRole(BasePermission):
    def __init__(self, *roles: str):
        super().__init__()
        self.allowed_roles = roles

    def has_permission(self, request: Request, view: View) -> bool:
        return request.user.is_authenticated and request.user.role in self.allowed_roles


class IsAdmin(BasePermission):
    def has_permission(self, request: Request, view: View) -> bool:
        return request.user.is_authenticated and request.user.role == "admin"


class IsReadOnly(BasePermission):
    def has_permission(self, request: Request, view: View) -> bool:
        return request.method in SAFE_METHODS


class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request: Request, view: View, obj) -> bool:
        if request.user.role == "admin":
            return True
        return IsOwner().has_object_permission(request, view, obj)


class IsVerified(BasePermission):
    def has_permission(self, request: Request, view: View) -> bool:
        return request.user.is_authenticated and request.user.is_verified


class IsEntrepreneur(BasePermission):
    def has_permission(self, request: Request, view: View) -> bool:
        return request.user.is_authenticated and request.user.role == "entrepreneur"


class IsInvestor(BasePermission):
    def has_permission(self, request: Request, view: View) -> bool:
        return request.user.is_authenticated and request.user.role == "investor"


class IsMentor(BasePermission):
    def has_permission(self, request: Request, view: View) -> bool:
        return request.user.is_authenticated and request.user.role == "mentor"


class IsTalent(BasePermission):
    def has_permission(self, request: Request, view: View) -> bool:
        return request.user.is_authenticated and request.user.role == "talent"


class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request: Request, view: View, obj) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return IsOwner().has_object_permission(request, view, obj)
