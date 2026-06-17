import logging
import traceback

from django.conf import settings
from django.http import Http404
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    ValidationError,
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
    NotFound,
    MethodNotAllowed,
    NotAcceptable,
    Throttled,
    ParseError,
)

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        errors = response.data
        status_code = response.status_code

        wrapped = _wrap_errors(errors)

        response.data = {
            "status": "error",
            "error": {
                "code": _get_error_code(exc, status_code),
                "message": wrapped.get("message", "An error occurred"),
                "details": wrapped.get("details", {}),
            },
        }

    elif isinstance(exc, ApplicationError):
        response = Response(
            {
                "status": "error",
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                },
            },
            status=exc.status_code,
        )

    elif isinstance(exc, Http404):
        response = Response(
            {
                "status": "error",
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Resource not found.",
                    "details": {},
                },
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    elif isinstance(exc, DjangoPermissionDenied):
        response = Response(
            {
                "status": "error",
                "error": {
                    "code": "PERMISSION_DENIED",
                    "message": "You do not have permission to perform this action.",
                    "details": {},
                },
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    else:
        logger.error(
            "Unhandled exception: %s: %s\n%s",
            type(exc).__name__,
            exc,
            "".join(traceback.format_tb(exc.__traceback__)) if settings.DEBUG else "",
        )

        response = Response(
            {
                "status": "error",
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred."
                    if not settings.DEBUG
                    else str(exc),
                    "details": {},
                },
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response


def _wrap_errors(errors):
    if isinstance(errors, dict):
        detail = errors.pop("detail", None)
        if detail:
            return {"message": detail, "details": errors}
        return {"message": "Validation error", "details": errors}
    elif isinstance(errors, list):
        msg = str(errors[0]) if errors else "Error"
        return {"message": msg, "details": errors}
    return {"message": str(errors), "details": {}}


def _get_error_code(exc, status_code):
    mapping = {
        ValidationError: "VALIDATION_ERROR",
        AuthenticationFailed: "AUTHENTICATION_FAILED",
        NotAuthenticated: "NOT_AUTHENTICATED",
        PermissionDenied: "PERMISSION_DENIED",
        NotFound: "NOT_FOUND",
        MethodNotAllowed: "METHOD_NOT_ALLOWED",
        NotAcceptable: "NOT_ACCEPTABLE",
        Throttled: "RATE_LIMITED",
        ParseError: "PARSE_ERROR",
    }

    for exc_type, code in mapping.items():
        if isinstance(exc, exc_type):
            return code

    if status_code == 403:
        return "PERMISSION_DENIED"

    return "APPLICATION_ERROR"


class ApplicationError(Exception):
    def __init__(
        self,
        message: str,
        code: str = "APPLICATION_ERROR",
        status_code: int = 400,
        details: dict | None = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)
