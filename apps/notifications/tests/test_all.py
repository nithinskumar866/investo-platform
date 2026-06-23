import pytest
from django.utils import timezone
from unittest.mock import patch, PropertyMock

from apps.accounts.models import User
from apps.notifications.models import Notification, NotificationPreference
from apps.notifications.services import NotificationService


# ── User fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="user@example.com", password="testpass123", role="entrepreneur",
    )


@pytest.fixture
def founder(db):
    return User.objects.create_user(
        email="founder@example.com", password="testpass123", role="entrepreneur",
    )


@pytest.fixture
def investor(db):
    return User.objects.create_user(
        email="investor@example.com", password="testpass123", role="investor",
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email="admin@example.com", password="testpass123",
    )


@pytest.fixture
def recipient(db):
    return User.objects.create_user(
        email="recipient@example.com", password="testpass123", role="entrepreneur",
    )


@pytest.fixture
def notification(db, recipient, investor):
    return Notification.objects.create(
        recipient=recipient,
        actor=investor,
        notification_type="deal_created",
        title="Investment Interest",
        message="Investor is interested in your startup",
        data={"opportunity_id": 1},
    )


@pytest.fixture
def preferences(db, recipient):
    return NotificationPreference.objects.create(
        user=recipient,
        email_enabled=True,
        push_enabled=True,
        in_app_enabled=True,
        matching_notifications=True,
        investment_notifications=True,
        chat_notifications=True,
        document_notifications=True,
        marketing_notifications=False,
    )


# ── Model tests ──────────────────────────────────────────────────────────

class TestNotificationModel:
    def test_create_notification(self, notification):
        assert notification.pk is not None
        assert notification.title == "Investment Interest"
        assert notification.notification_type == "deal_created"
        assert notification.is_read is False

    def test_notification_type_choices(self):
        types = dict(Notification.Type.choices)
        assert "new_match" in types
        assert "deal_created" in types
        assert "system" in types

    def test_category(self, notification):
        assert notification.category() == "investments"

    def test_str(self, notification):
        assert str(notification) == "Investment Interest (recipient@example.com)"


class TestNotificationPreferenceModel:
    def test_create_preferences(self, preferences):
        assert preferences.pk is not None
        assert preferences.email_enabled is True

    def test_defaults(self, recipient):
        prefs = NotificationPreference.objects.create(user=recipient)
        assert prefs.marketing_notifications is False


# ── Service tests ────────────────────────────────────────────────────────

class TestNotificationService:
    def test_notify_creates_notification(self, recipient, investor):
        with patch("apps.notifications.services.RealtimeService"):
            with patch("apps.notifications.services.EmailService"):
                n = NotificationService.notify(
                    recipient=recipient,
                    notification_type="new_match",
                    title="New Match",
                    message="You have a new match",
                    actor=investor,
                    data={"score": 85},
                )
        assert n is not None
        assert n.title == "New Match"
        assert n.recipient == recipient

    def test_notify_respects_disabled_preferences(self, recipient, investor):
        prefs = NotificationPreference.objects.create(
            user=recipient, in_app_enabled=False,
        )
        n = NotificationService.notify(
            recipient=recipient,
            notification_type="new_match",
            title="Should not appear",
            message="",
        )
        assert n is None

    def test_notify_deduplicates(self, recipient, investor):
        with patch("apps.notifications.services.RealtimeService"):
            with patch("apps.notifications.services.EmailService"):
                NotificationService.notify(
                    recipient=recipient,
                    notification_type="new_match",
                    title="Duplicate Test",
                    message="First",
                )
                n2 = NotificationService.notify(
                    recipient=recipient,
                    notification_type="new_match",
                    title="Duplicate Test",
                    message="Second (should be deduped)",
                )
        assert n2 is None

    def test_notify_sends_email(self, recipient, investor):
        NotificationPreference.objects.create(user=recipient)
        with patch("apps.notifications.services.RealtimeService"):
            with patch(
                "apps.notifications.services.EmailService.send_match_notification",
            ) as mock_email:
                NotificationService.notify(
                    recipient=recipient,
                    notification_type="new_match",
                    title="Email Test",
                    message="Test",
                    actor=investor,
                    data={"score": 90},
                )
        mock_email.assert_called_once()

    def test_mark_read(self, notification, recipient):
        result = NotificationService.mark_read(notification.id, recipient)
        assert result is not None
        notification.refresh_from_db()
        assert notification.is_read is True

    def test_mark_read_not_found(self, recipient):
        result = NotificationService.mark_read(9999, recipient)
        assert result is None

    def test_mark_all_read(self, recipient, investor):
        for i in range(3):
            Notification.objects.create(
                recipient=recipient, actor=investor,
                notification_type="system", title=f"Test {i}", message="",
            )
        count = NotificationService.mark_all_read(recipient)
        assert count == 3
        assert Notification.objects.filter(recipient=recipient, is_read=True).count() == 3

    def test_get_notifications(self, notification, recipient):
        notes, has_more = NotificationService.get_notifications(recipient)
        assert notification in notes

    def test_get_unread(self, notification, recipient):
        notes, has_more = NotificationService.get_unread(recipient)
        assert notification in notes

    def test_get_unread_count(self, notification, recipient):
        count = NotificationService.get_unread_count(recipient)
        assert count == 1

    def test_delete_notification(self, notification, recipient):
        result = NotificationService.delete_notification(notification.id, recipient)
        assert result is True
        assert Notification.objects.filter(id=notification.id).count() == 0

    def test_get_preferences(self, preferences, recipient):
        prefs = NotificationService.get_preferences(recipient)
        assert prefs == preferences

    def test_update_preferences(self, preferences, recipient):
        updated = NotificationService.update_preferences(
            recipient, {"email_enabled": False, "marketing_notifications": True},
        )
        assert updated.email_enabled is False
        assert updated.marketing_notifications is True

    def test_notify_many(self, recipient, investor):
        with patch("apps.notifications.services.RealtimeService"):
            with patch("apps.notifications.services.EmailService"):
                results = NotificationService.notify_many([
                    {
                        "recipient": recipient,
                        "notification_type": "system",
                        "title": "Bulk 1",
                        "message": "Bulk message 1",
                        "actor": investor,
                        "data": {},
                    },
                ])
        assert len(results) == 1


# ── View tests ──────────────────────────────────────────────────────────

class TestNotificationViewSet:
    def test_list_notifications(self, investor_client, notification):
        resp = investor_client.get("/api/v1/notifications/")
        assert resp.status_code == 200

    def test_unread(self, investor_client, notification):
        resp = investor_client.get("/api/v1/notifications/unread/")
        assert resp.status_code == 200

    def test_unread_count(self, investor_client, notification):
        resp = investor_client.get("/api/v1/notifications/unread-count/")
        assert resp.status_code == 200
        assert "count" in resp.json()

    def test_read(self, investor_client, notification):
        resp = investor_client.post(
            f"/api/v1/notifications/{notification.id}/read/",
        )
        assert resp.status_code == 200

    def test_read_all(self, investor_client, notification):
        resp = investor_client.post("/api/v1/notifications/read-all/")
        assert resp.status_code == 200

    def test_destroy(self, investor_client, notification):
        resp = investor_client.delete(
            f"/api/v1/notifications/{notification.id}/",
        )
        assert resp.status_code == 204

    def test_preferences_get(self, investor_client, preferences):
        resp = investor_client.get("/api/v1/notifications/preferences/")
        assert resp.status_code == 200

    def test_preferences_update(self, investor_client):
        resp = investor_client.patch(
            "/api/v1/notifications/preferences/",
            {"email_enabled": False},
            format="json",
        )
        assert resp.status_code == 200

    def test_analytics(self, investor_client, notification):
        resp = investor_client.get("/api/v1/notifications/analytics/")
        assert resp.status_code == 200
