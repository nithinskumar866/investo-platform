from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import View


class IsInvestor(BasePermission):
    def has_permission(self, request: Request, view: View) -> bool:
        return request.user.is_authenticated and request.user.role == "investor"


class IsEntrepreneur(BasePermission):
    def has_permission(self, request: Request, view: View) -> bool:
        return request.user.is_authenticated and request.user.role == "entrepreneur"


class CanManageMatch(BasePermission):
    def has_object_permission(self, request: Request, view: View, obj) -> bool:
        if request.user.role == "admin":
            return True
        if hasattr(obj, "investor"):
            return obj.investor == request.user
        if hasattr(obj, "user"):
            return obj.user == request.user
        return False


class IsMatchOwner(BasePermission):
    def has_object_permission(self, request: Request, view: View, obj) -> bool:
        if hasattr(obj, "investor"):
            return obj.investor == request.user
        return obj.user == request.user
