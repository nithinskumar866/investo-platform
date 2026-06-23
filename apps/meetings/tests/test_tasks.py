import datetime

import pytest
from unittest.mock import patch

from django.utils import timezone

from apps.meetings.models import Meeting
from apps.meetings.tasks import (
    meeting_reminder_24h,
    meeting_reminder_1h,
    missed_meeting_followup,
    daily_agenda_email,
)
from apps.common.tests.factories import (
    UserFactory, MeetingFactory,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def upcoming_meeting():
    now = timezone.now()
    meeting = MeetingFactory(
        scheduled_start=now + datetime.timedelta(hours=24),
        scheduled_end=now + datetime.timedelta(hours=25),
        status=Meeting.Status.SCHEDULED,
    )
    return meeting


@pytest.fixture
def soon_meeting():
    now = timezone.now()
    meeting = MeetingFactory(
        scheduled_start=now + datetime.timedelta(hours=1),
        scheduled_end=now + datetime.timedelta(hours=2),
        status=Meeting.Status.CONFIRMED,
    )
    return meeting


@pytest.fixture
def past_meeting():
    now = timezone.now()
    meeting = MeetingFactory(
        scheduled_start=now - datetime.timedelta(hours=2),
        scheduled_end=now - datetime.timedelta(hours=1),
        status=Meeting.Status.SCHEDULED,
    )
    return meeting


@pytest.fixture
def today_meeting():
    now = timezone.now()
    meeting = MeetingFactory(
        scheduled_start=now + datetime.timedelta(hours=3),
        scheduled_end=now + datetime.timedelta(hours=4),
        status=Meeting.Status.CONFIRMED,
    )
    return meeting


class TestMeetingReminder24h:
    @patch("apps.notifications.services.NotificationService.notify")
    def test_creates_notifications_for_upcoming_meetings(self, mock_notify, upcoming_meeting):
        count = meeting_reminder_24h()
        assert count == 2
        assert mock_notify.call_count == 2

    @patch("apps.notifications.services.NotificationService.notify")
    def test_does_not_notify_for_outside_window(self, mock_notify):
        now = timezone.now()
        MeetingFactory(
            scheduled_start=now + datetime.timedelta(hours=48),
            scheduled_end=now + datetime.timedelta(hours=49),
            status=Meeting.Status.SCHEDULED,
        )
        count = meeting_reminder_24h()
        assert count == 0

    @patch("apps.notifications.services.NotificationService.notify")
    def test_notifies_organizer_and_investor(self, mock_notify, upcoming_meeting):
        count = meeting_reminder_24h()
        assert count == 2
        recipients = [call.kwargs["recipient"] for call in mock_notify.call_args_list]
        assert upcoming_meeting.organizer in recipients
        assert upcoming_meeting.investor in recipients


class TestMeetingReminder1h:
    @patch("apps.notifications.services.NotificationService.notify")
    def test_creates_notifications_for_soon_meetings(self, mock_notify, soon_meeting):
        count = meeting_reminder_1h()
        assert count == 2
        assert mock_notify.call_count == 2

    @patch("apps.notifications.services.NotificationService.notify")
    def test_does_not_notify_for_outside_window(self, mock_notify):
        now = timezone.now()
        MeetingFactory(
            scheduled_start=now + datetime.timedelta(hours=3),
            scheduled_end=now + datetime.timedelta(hours=4),
            status=Meeting.Status.CONFIRMED,
        )
        count = meeting_reminder_1h()
        assert count == 0

    @patch("apps.notifications.services.NotificationService.notify")
    def test_notifies_correct_users(self, mock_notify, soon_meeting):
        meeting_reminder_1h()
        recipients = [call.kwargs["recipient"] for call in mock_notify.call_args_list]
        assert soon_meeting.organizer in recipients
        assert soon_meeting.investor in recipients


class TestMissedMeetingFollowup:
    @patch("apps.notifications.services.NotificationService.notify")
    def test_creates_notifications_for_missed_meetings(self, mock_notify, past_meeting):
        count = missed_meeting_followup()
        assert count == 2
        assert mock_notify.call_count == 2

    @patch("apps.notifications.services.NotificationService.notify")
    def test_does_not_notify_completed_meetings(self, mock_notify):
        now = timezone.now()
        MeetingFactory(
            scheduled_start=now - datetime.timedelta(hours=2),
            scheduled_end=now - datetime.timedelta(hours=1),
            status=Meeting.Status.COMPLETED,
        )
        count = missed_meeting_followup()
        assert count == 0

    @patch("apps.notifications.services.NotificationService.notify")
    def test_does_not_notify_cancelled_meetings(self, mock_notify):
        now = timezone.now()
        MeetingFactory(
            scheduled_start=now - datetime.timedelta(hours=2),
            scheduled_end=now - datetime.timedelta(hours=1),
            status=Meeting.Status.CANCELLED,
        )
        count = missed_meeting_followup()
        assert count == 0


class TestDailyAgendaEmail:
    @patch("apps.notifications.services.NotificationService.notify")
    def test_creates_notifications(self, mock_notify, today_meeting):
        count = daily_agenda_email()
        assert count == 2  # organizer + investor
        assert mock_notify.call_count == 2

    @patch("apps.notifications.services.NotificationService.notify")
    def test_does_not_notify_no_meetings_today(self, mock_notify):
        count = daily_agenda_email()
        assert count == 0

    @patch("apps.notifications.services.NotificationService.notify")
    def test_notifies_both_participants(self, mock_notify, today_meeting):
        daily_agenda_email()
        recipients = [call.kwargs["recipient"] for call in mock_notify.call_args_list]
        assert today_meeting.organizer in recipients
        assert today_meeting.investor in recipients

    @patch("apps.notifications.services.NotificationService.notify")
    def test_agenda_contains_correct_meeting_count(self, mock_notify, today_meeting):
        daily_agenda_email()
        for call in mock_notify.call_args_list:
            data = call.kwargs["data"]
            assert data["meeting_count"] == 1
            assert len(data["meetings"]) == 1
