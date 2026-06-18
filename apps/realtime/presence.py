import json
import logging

from django.core.cache import cache

logger = logging.getLogger(__name__)

USER_PRESENCE_PREFIX = "presence:user:"
USER_PRESENCE_TTL = 120
ONLINE_USERS_SET = "presence:online_users"


class UserPresence:
    """Redis-based presence tracker. Uses django_redis cache backend."""

    @staticmethod
    def set_online(user_id, channel_name=None):
        key = f"{USER_PRESENCE_PREFIX}{user_id}"
        data = {"online": True}
        if channel_name:
            data["channel_name"] = channel_name
        cache.set(key, json.dumps(data), timeout=USER_PRESENCE_TTL)
        cache.sadd(ONLINE_USERS_SET, user_id)

    @staticmethod
    def set_offline(user_id):
        key = f"{USER_PRESENCE_PREFIX}{user_id}"
        cache.delete(key)
        cache.srem(ONLINE_USERS_SET, user_id)

    @staticmethod
    def refresh_online(user_id, channel_name=None):
        key = f"{USER_PRESENCE_PREFIX}{user_id}"
        raw = cache.get(key)
        if raw:
            try:
                data = json.loads(raw)
                if channel_name:
                    data["channel_name"] = channel_name
                cache.set(key, json.dumps(data), timeout=USER_PRESENCE_TTL)
            except json.JSONDecodeError:
                pass
        else:
            UserPresence.set_online(user_id, channel_name=channel_name)

    @staticmethod
    def get_presence(user_id):
        key = f"{USER_PRESENCE_PREFIX}{user_id}"
        raw = cache.get(key)
        if not raw:
            return {"user_id": user_id, "online": False, "last_seen": None}
        try:
            data = json.loads(raw)
            return {"user_id": user_id, "online": True, "last_seen": None}
        except json.JSONDecodeError:
            return {"user_id": user_id, "online": False, "last_seen": None}

    @staticmethod
    def get_online_users():
        members = cache.smembers(ONLINE_USERS_SET)
        return [int(u) for u in members if u]

    @staticmethod
    def get_online_users_bulk(user_ids):
        pipeline = {}
        for uid in user_ids:
            pipeline[uid] = UserPresence.get_presence(uid)
        return pipeline


class PresenceRepository:
    """Repository for presence operations."""

    @staticmethod
    def set_online(user_id, channel_name=None):
        UserPresence.set_online(user_id, channel_name=channel_name)

    @staticmethod
    def set_offline(user_id):
        UserPresence.set_offline(user_id)

    @staticmethod
    def get_presence(user_id):
        return UserPresence.get_presence(user_id)

    @staticmethod
    def get_online_users():
        return UserPresence.get_online_users()

    @staticmethod
    def refresh_online(user_id, channel_name=None):
        UserPresence.refresh_online(user_id, channel_name=channel_name)
