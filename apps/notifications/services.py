import logging
from django.db import transaction
from django.db.models import Q
from .models import Notification

logger = logging.getLogger(__name__)


class NotificationService:
    @staticmethod
    def create_notification(user, title, message, notification_type="other",
                            related_object_id=None, related_object_type="",
                            action_url=""):
        notification = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            related_object_id=related_object_id,
            related_object_type=related_object_type,
            action_url=action_url,
        )
        logger.info(f"Notification created for {user.email}: {title}")
        return notification

    @staticmethod
    def create_bulk(users, title, message, notification_type="other",
                    related_object_id=None, related_object_type="",
                    action_url=""):
        notifications = [
            Notification(
                user=user,
                title=title,
                message=message,
                notification_type=notification_type,
                related_object_id=related_object_id,
                related_object_type=related_object_type,
                action_url=action_url,
            )
            for user in users
        ]
        Notification.objects.bulk_create(notifications)
        logger.info(f"Bulk notifications created: {len(notifications)} notifications")
        return notifications

    @staticmethod
    def get_user_notifications(user, unread_only=False, limit=None):
        queryset = Notification.objects.filter(user=user)
        if unread_only:
            queryset = queryset.filter(is_read=False)
        if limit:
            queryset = queryset[:limit]
        return queryset

    @staticmethod
    def get_unread_count(user):
        return Notification.objects.filter(user=user, is_read=False).count()

    @staticmethod
    @transaction.atomic
    def mark_as_read(user, notification_id):
        try:
            notification = Notification.objects.get(pk=notification_id, user=user)
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            return False

    @staticmethod
    @transaction.atomic
    def mark_all_as_read(user):
        count = Notification.objects.filter(user=user, is_read=False).update(is_read=True)
        logger.info(f"Marked {count} notifications as read for {user.email}")
        return count