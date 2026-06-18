import logging

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.db import close_old_connections
from rest_framework_simplejwt.tokens import AccessToken

logger = logging.getLogger(__name__)


@database_sync_to_async
def get_user_from_token(token_str):
    try:
        token = AccessToken(token_str)
        user_id = token.payload.get("user_id")
        if user_id is None:
            return None
        User = get_user_model()
        user = User.objects.get(id=user_id, is_active=True)
        close_old_connections()
        return user
    except Exception:
        close_old_connections()
        return None


class JWTAuthMiddleware(BaseMiddleware):
    """Authenticate WebSocket connections via JWT token."""

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        token = None

        for part in query_string.split("&"):
            if part.startswith("token="):
                token = part[6:]
                break

        if token is None:
            headers = dict(scope.get("headers", []))
            auth_header = headers.get(b"authorization", b"").decode()
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]

        if token:
            user = await get_user_from_token(token)
            if user is not None:
                scope["user"] = user

        return await super().__call__(scope, receive, send)
