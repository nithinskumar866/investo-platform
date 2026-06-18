from django.db import transaction
from django.db.models import Count, Avg, Q
from django.utils import timezone

from .models import Notification, NotificationPreference


class NotificationRepository:
    """Data access layer for notification operations."""

    # ── Create ────────────────────────────────────────────────────

    @staticmethod
    def create_notification(recipient, title, message,
                            notification_type=Notification.Type.SYSTEM,
                            actor=None, data=None):
        return Notification.objects.create(
            recipient=recipient,
            actor=actor,
            title=title,
            message=message,
            notification_type=notification_type,
            data=data or {},
        )

    @staticmethod
    def bulk_create_notifications(notifications_data):
        objs = [
            Notification(
                recipient=nd["recipient"],
                actor=nd.get("actor"),
                title=nd["title"],
                message=nd["message"],
                notification_type=nd.get("notification_type",
                                          Notification.Type.SYSTEM),
                data=nd.get("data", {}),
            )
            for nd in notifications_data
        ]
        return Notification.objects.bulk_create(objs)

    # ── Read ──────────────────────────────────────────────────────

    @staticmethod
    def get_user_notifications(user, cursor=None, limit=20):
        qs = Notification.objects.filter(recipient=user).select_related(
            "actor",
        ).order_by("-created_at")
        if cursor:
            qs = qs.filter(created_at__lt=cursor)
        return list(qs[:limit]), (
            qs[limit:].exists() if len(qs) == limit else False
        )

    @staticmethod
    def get_unread_notifications(user, cursor=None, limit=20):
        qs = Notification.objects.filter(
            recipient=user, is_read=False,
        ).select_related("actor").order_by("-created_at")
        if cursor:
            qs = qs.filter(created_at__lt=cursor)
        return list(qs[:limit]), (
            qs[limit:].exists() if len(qs) == limit else False
        )

    @staticmethod
    def get_notification(pk, user):
        return Notification.objects.filter(
            pk=pk, recipient=user,
        ).select_related("actor").first()

    @staticmethod
    def get_unread_count(user):
        return Notification.objects.filter(
            recipient=user, is_read=False,
        ).count()

    # ── Update ────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def mark_read(notification):
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=["is_read", "read_at"])
        return notification

    @staticmethod
    @transaction.atomic
    def mark_all_read(user):
        now = timezone.now()
        return Notification.objects.filter(
            recipient=user, is_read=False,
        ).update(is_read=True, read_at=now)

    # ── Delete ────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def delete_notification(pk, user):
        deleted, _ = Notification.objects.filter(
            pk=pk, recipient=user,
        ).delete()
        return deleted > 0

    # ── Preferences ───────────────────────────────────────────────

    @staticmethod
    def get_preferences(user):
        prefs, _ = NotificationPreference.objects.get_or_create(user=user)
        return prefs

    @staticmethod
    @transaction.atomic
    def update_preferences(user, data):
        prefs = NotificationRepository.get_preferences(user)
        allowed_fields = {
            "email_enabled", "push_enabled", "in_app_enabled",
            "matching_notifications", "investment_notifications",
            "chat_notifications", "document_notifications",
            "marketing_notifications",
        }
        for field, value in data.items():
            if field in allowed_fields and isinstance(value, bool):
                setattr(prefs, field, value)
        prefs.save()
        return prefs

    # ── Analytics ─────────────────────────────────────────────────

    @staticmethod
    def get_analytics(user):
        qs = Notification.objects.filter(recipient=user)
        total = qs.count()
        read_count = qs.filter(is_read=True).count()
        read_rate = round(read_count / total * 100, 1) if total else 0.0

        by_type = list(
            qs.values("notification_type").annotate(
                count=Count("id"),
                read_count=Count("id", filter=Q(is_read=True)),
            ).order_by("-count")
        )

        avg_response = qs.filter(
            read_at__isnull=False,
        ).values("recipient").annotate(
            avg_seconds=Avg(
                # read_at - created_at in seconds
            ),
        )

        return {
            "total_notifications": total,
            "unread_count": qs.filter(is_read=False).count(),
            "read_rate": read_rate,
            "read_count": read_count,
            "by_type": by_type,
            "volume_last_7_days": qs.filter(
                created_at__gte=timezone.now() - timezone.timedelta(days=7),
            ).count(),
        }
