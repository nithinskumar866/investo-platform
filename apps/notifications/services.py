import logging
from django.utils import timezone

from apps.common.email_service import EmailService

from .models import Notification, NotificationPreference
from .repositories import NotificationRepository

logger = logging.getLogger(__name__)


class NotificationService:
    """Business logic for notification operations."""

    DEDUP_WINDOW_SECONDS = 60

    CATEGORY_TO_PREF_FIELD = {
        "matches": "matching_notifications",
        "messages": "chat_notifications",
        "investments": "investment_notifications",
        "documents": "document_notifications",
        "system": None,
    }

    # ── Core notify ───────────────────────────────────────────────

    @classmethod
    def notify(cls, recipient, notification_type, title, message,
               actor=None, data=None):
        """Single-recipient notification with preference check and dedup."""
        if not cls._should_notify(recipient, notification_type):
            return None

        if cls._is_duplicate(recipient, notification_type, title):
            logger.debug(
                f"Deduplicated notification for {recipient.email}: {title}",
            )
            return None

        notification = NotificationRepository.create_notification(
            recipient=recipient,
            title=title,
            message=message,
            notification_type=notification_type,
            actor=actor,
            data=data,
        )

        cls._broadcast(notification)
        cls._send_email(recipient, notification_type, title, message, data)
        return notification

    @classmethod
    def notify_many(cls, recipients_data):
        """Bulk notification with preference checks per recipient.

        recipients_data: list of dicts with keys:
            recipient, notification_type, title, message, actor, data
        """
        filtered = []
        for nd in recipients_data:
            if cls._should_notify(
                nd["recipient"], nd["notification_type"],
            ):
                if not cls._is_duplicate(
                    nd["recipient"], nd["notification_type"], nd["title"],
                ):
                    filtered.append(nd)

        if not filtered:
            return []

        notifications = NotificationRepository.bulk_create_notifications(
            filtered,
        )

        for n in notifications:
            cls._broadcast(n)

        return notifications

    @classmethod
    def notify_future_module(cls, recipient, notification_type, title,
                             message, actor=None, data=None):
        """Future-proof notify method — modules call this without
        importing notification internals. Signature is stable."""
        return cls.notify(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            message=message,
            actor=actor,
            data=data,
        )

    # ── Preference & Dedup checks ─────────────────────────────────

    @classmethod
    def _should_notify(cls, recipient, notification_type):
        if notification_type not in dict(Notification.Type.choices):
            return True

        category = Notification.TYPE_GROUP_MAP.get(
            notification_type, "system",
        )
        pref_field = cls.CATEGORY_TO_PREF_FIELD.get(category)

        if pref_field is None:
            return True

        prefs = NotificationRepository.get_preferences(recipient)

        if not prefs.in_app_enabled:
            return False

        return getattr(prefs, pref_field, True)

    @classmethod
    def _is_duplicate(cls, recipient, notification_type, title):
        cutoff = timezone.now() - timezone.timedelta(
            seconds=cls.DEDUP_WINDOW_SECONDS,
        )
        from django.db.models import Q
        return Notification.objects.filter(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            created_at__gte=cutoff,
        ).exists()

    # ── Email dispatch ───────────────────────────────────────────

    @staticmethod
    def _send_email(recipient, notification_type, title, message, data=None):
        prefs = NotificationRepository.get_preferences(recipient)
        if not prefs.email_enabled:
            return

        type_to_email = {
            "new_match": "send_match_notification",
            "system": "send_generic",
        }
        email_method = type_to_email.get(notification_type)
        if email_method == "send_match_notification":
            EmailService.send_match_notification(
                recipient_email=recipient.email,
                recipient_name=recipient.first_name or recipient.email,
                match_type=data.get("match_type", "startup") if data else "startup",
                context={
                    "score": data.get("score", 0) if data else 0,
                    "startup_name": data.get("startup_name", "") if data else "",
                    "investor_name": data.get("investor_name", "") if data else "",
                    "investor_type": data.get("investor_type", "") if data else "",
                    "industry": data.get("industry", "") if data else "",
                    "stage": data.get("stage", "") if data else "",
                    "match_url": data.get("match_url", "") if data else "",
                },
            )
        elif notification_type.startswith("meeting"):
            EmailService.send_meeting_reminder(
                recipient_email=recipient.email,
                recipient_name=recipient.first_name or recipient.email,
                meeting_context={
                    "meeting_title": title,
                    "meeting_date": data.get("scheduled_start", "") if data else "",
                    "meeting_time": data.get("scheduled_start", "") if data else "",
                    "meeting_link": data.get("meeting_link", "") if data else "",
                    "meeting_url": data.get("meeting_url", "") if data else "",
                },
            )
        elif notification_type == "welcome":
            EmailService.send_welcome(
                recipient_email=recipient.email,
                recipient_name=recipient.first_name or recipient.email,
                dashboard_url=data.get("dashboard_url", "") if data else "",
            )

    # ── WebSocket broadcast via Channels ─────────────────────────

    @staticmethod
    def _broadcast(notification):
        from apps.realtime.services import RealtimeService
        RealtimeService.broadcast_to_notifications(
            user_id=notification.recipient_id,
            event_type="notification_created",
            payload={
                "notification": {
                    "id": notification.id,
                    "type": notification.notification_type,
                    "title": notification.title,
                    "message": notification.message,
                    "created_at": notification.created_at.isoformat(),
                },
            },
        )

    # ── Query methods ─────────────────────────────────────────────

    @staticmethod
    def get_notifications(user, cursor=None, limit=20):
        return NotificationRepository.get_user_notifications(
            user, cursor=cursor, limit=limit,
        )

    @staticmethod
    def get_unread(user, cursor=None, limit=20):
        return NotificationRepository.get_unread_notifications(
            user, cursor=cursor, limit=limit,
        )

    @staticmethod
    def get_unread_count(user):
        return NotificationRepository.get_unread_count(user)

    # ── Mutations ─────────────────────────────────────────────────

    @staticmethod
    def mark_read(notification_id, user):
        notification = NotificationRepository.get_notification(
            notification_id, user,
        )
        if not notification:
            return None
        NotificationRepository.mark_read(notification)
        return notification

    @staticmethod
    def mark_all_read(user):
        return NotificationRepository.mark_all_read(user)

    @staticmethod
    def delete_notification(notification_id, user):
        return NotificationRepository.delete_notification(
            notification_id, user,
        )

    # ── Preferences ───────────────────────────────────────────────

    @staticmethod
    def get_preferences(user):
        return NotificationRepository.get_preferences(user)

    @staticmethod
    def update_preferences(user, data):
        return NotificationRepository.update_preferences(user, data)

    # ── Analytics ─────────────────────────────────────────────────

    @staticmethod
    def get_analytics(user):
        return NotificationRepository.get_analytics(user)
