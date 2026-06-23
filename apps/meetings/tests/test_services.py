import datetime

import pytest
from unittest.mock import patch

from django.utils import timezone

from apps.accounts.models import User
from apps.meetings.models import Meeting, MeetingEvent
from apps.meetings.services import MeetingService
from apps.common.exceptions import ApplicationError
from apps.common.tests.factories import (
    UserFactory, FounderFactory, InvestorFactory,
    StartupFactory, MatchScoreFactory, MeetingFactory,
    MeetingAvailabilityFactory,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def founder():
    return FounderFactory()


@pytest.fixture
def investor():
    return InvestorFactory()


@pytest.fixture
def startup(founder):
    return StartupFactory(owner=founder)


@pytest.fixture
def match(investor, startup):
    return MatchScoreFactory(investor=investor, startup=startup)


@pytest.fixture
def meeting(founder, investor, startup, match):
    return MeetingFactory(
        organizer=founder, investor=investor, startup=startup,
        scheduled_start=timezone.now() + datetime.timedelta(days=7),
        scheduled_end=timezone.now() + datetime.timedelta(days=7, hours=1),
    )


SCHEDULE_DATA = {
    "title": "Intro Call",
    "meeting_type": "intro_call",
    "scheduled_start": timezone.now() + datetime.timedelta(days=10),
    "scheduled_end": timezone.now() + datetime.timedelta(days=10, hours=1),
    "timezone": "UTC",
}


class TestScheduleMeeting:
    @patch("apps.notifications.services.NotificationService.notify")
    @patch("apps.activity_feed.services.ActivityFeedService.publish_activity")
    @patch("apps.realtime.services.RealtimeService.broadcast_to_user")
    def test_creates_meeting_and_event(
        self, mock_broadcast, mock_activity, mock_notify,
        founder, investor, startup, match,
    ):
        data = {**SCHEDULE_DATA, "investor_id": investor.id, "startup": startup.id}
        meeting = MeetingService.schedule_meeting(founder, data)
        assert meeting.title == "Intro Call"
        assert meeting.organizer == founder
        assert meeting.investor == investor
        assert meeting.status == Meeting.Status.SCHEDULED
        event = MeetingEvent.objects.filter(meeting=meeting).first()
        assert event is not None
        assert event.action == MeetingEvent.Action.CREATED

    @patch("apps.notifications.services.NotificationService.notify")
    @patch("apps.activity_feed.services.ActivityFeedService.publish_activity")
    @patch("apps.realtime.services.RealtimeService.broadcast_to_user")
    def test_creates_participants(
        self, mock_broadcast, mock_activity, mock_notify,
        founder, investor, startup, match,
    ):
        data = {**SCHEDULE_DATA, "investor_id": investor.id, "startup": startup.id}
        meeting = MeetingService.schedule_meeting(founder, data)
        assert meeting.participants.count() == 2

    def test_raises_if_investor_not_found(self, founder):
        data = {**SCHEDULE_DATA, "investor_id": 99999}
        with pytest.raises(ApplicationError) as exc:
            MeetingService.schedule_meeting(founder, data)
        assert exc.value.code == "NOT_FOUND"

    def test_raises_if_same_user(self, founder):
        data = {**SCHEDULE_DATA, "investor_id": founder.id}
        with pytest.raises(ApplicationError) as exc:
            MeetingService.schedule_meeting(founder, data)
        assert exc.value.code == "SELF_MEETING"

    def test_raises_if_role_mismatch(self, founder):
        other_founder = FounderFactory()
        data = {**SCHEDULE_DATA, "investor_id": other_founder.id}
        with pytest.raises(ApplicationError) as exc:
            MeetingService.schedule_meeting(founder, data)
        assert exc.value.code == "ROLE_MISMATCH"


class TestConfirmMeeting:
    def test_changes_status_to_confirmed(self, founder, meeting):
        result = MeetingService.confirm_meeting(meeting.id, founder)
        assert result.status == Meeting.Status.CONFIRMED

    def test_raises_if_already_completed(self, founder, meeting):
        meeting.status = Meeting.Status.COMPLETED
        meeting.save()
        with pytest.raises(ApplicationError) as exc:
            MeetingService.confirm_meeting(meeting.id, founder)
        assert exc.value.code == "INVALID_STATUS"

    def test_raises_if_already_cancelled(self, founder, meeting):
        meeting.status = Meeting.Status.CANCELLED
        meeting.save()
        with pytest.raises(ApplicationError) as exc:
            MeetingService.confirm_meeting(meeting.id, founder)
        assert exc.value.code == "INVALID_STATUS"


class TestCancelMeeting:
    def test_changes_status_to_cancelled(self, founder, meeting):
        result = MeetingService.cancel_meeting(meeting.id, founder)
        assert result.status == Meeting.Status.CANCELLED

    def test_raises_if_already_cancelled(self, founder, meeting):
        meeting.status = Meeting.Status.CANCELLED
        meeting.save()
        with pytest.raises(ApplicationError) as exc:
            MeetingService.cancel_meeting(meeting.id, founder)
        assert exc.value.code == "ALREADY_CLOSED"

    def test_raises_if_already_completed(self, founder, meeting):
        meeting.status = Meeting.Status.COMPLETED
        meeting.save()
        with pytest.raises(ApplicationError) as exc:
            MeetingService.cancel_meeting(meeting.id, founder)
        assert exc.value.code == "ALREADY_CLOSED"


class TestRescheduleMeeting:
    def test_updates_times(self, founder, meeting):
        new_start = meeting.scheduled_start + datetime.timedelta(days=1)
        new_end = meeting.scheduled_end + datetime.timedelta(days=1)
        result = MeetingService.reschedule_meeting(meeting.id, founder, {
            "scheduled_start": new_start,
            "scheduled_end": new_end,
        })
        assert result.scheduled_start == new_start
        assert result.scheduled_end == new_end

    def test_raises_if_closed(self, founder, meeting):
        meeting.status = Meeting.Status.CANCELLED
        meeting.save()
        with pytest.raises(ApplicationError) as exc:
            MeetingService.reschedule_meeting(meeting.id, founder, {
                "scheduled_start": meeting.scheduled_start,
                "scheduled_end": meeting.scheduled_end,
            })
        assert exc.value.code == "ALREADY_CLOSED"

    def test_creates_rescheduled_event(self, founder, meeting):
        new_start = meeting.scheduled_start + datetime.timedelta(days=1)
        new_end = meeting.scheduled_end + datetime.timedelta(days=1)
        MeetingService.reschedule_meeting(meeting.id, founder, {
            "scheduled_start": new_start,
            "scheduled_end": new_end,
        })
        event = MeetingEvent.objects.filter(
            meeting=meeting, action=MeetingEvent.Action.RESCHEDULED,
        ).first()
        assert event is not None
        assert "old_start" in event.metadata
        assert "new_start" in event.metadata


class TestCompleteMeeting:
    def test_changes_status_to_completed(self, founder, meeting):
        meeting.status = Meeting.Status.CONFIRMED
        meeting.save()
        result = MeetingService.complete_meeting(meeting.id, founder)
        assert result.status == Meeting.Status.COMPLETED

    def test_raises_if_already_cancelled(self, founder, meeting):
        meeting.status = Meeting.Status.CANCELLED
        meeting.save()
        with pytest.raises(ApplicationError) as exc:
            MeetingService.complete_meeting(meeting.id, founder)
        assert exc.value.code == "ALREADY_CLOSED"

    def test_raises_if_already_completed(self, founder, meeting):
        meeting.status = Meeting.Status.COMPLETED
        meeting.save()
        with pytest.raises(ApplicationError) as exc:
            MeetingService.complete_meeting(meeting.id, founder)
        assert exc.value.code == "ALREADY_CLOSED"

    def test_updates_notes(self, founder, meeting):
        meeting.status = Meeting.Status.CONFIRMED
        meeting.save()
        result = MeetingService.complete_meeting(meeting.id, founder, notes="Great meeting")
        assert result.notes == "Great meeting"


class TestListMeetings:
    def test_returns_user_meetings(self, founder, meeting):
        meetings, has_more = MeetingService.list_meetings(founder)
        assert meeting.id in [m.id for m in meetings]

    def test_does_not_return_other_user_meetings(self, founder, meeting):
        stranger = UserFactory()
        meetings, has_more = MeetingService.list_meetings(stranger)
        assert len(meetings) == 0


class TestListUpcoming:
    def test_filters_upcoming(self, founder, meeting):
        meetings, has_more = MeetingService.list_upcoming(founder)
        assert meeting.id in [m.id for m in meetings]

    def test_excludes_past(self, founder, meeting):
        meeting.scheduled_start = timezone.now() - datetime.timedelta(days=10)
        meeting.scheduled_end = timezone.now() - datetime.timedelta(days=10, hours=-1)
        meeting.save()
        meetings, has_more = MeetingService.list_upcoming(founder)
        assert meeting.id not in [m.id for m in meetings]


class TestGetCalendar:
    def test_returns_meetings_in_range(self, founder, meeting):
        start = meeting.scheduled_start - datetime.timedelta(days=1)
        end = meeting.scheduled_end + datetime.timedelta(days=1)
        result = MeetingService.get_calendar(founder, start, end)
        assert meeting.id in [m.id for m in result]

    def test_excludes_out_of_range(self, founder, meeting):
        start = meeting.scheduled_start - datetime.timedelta(days=30)
        end = meeting.scheduled_start - datetime.timedelta(days=20)
        result = MeetingService.get_calendar(founder, start, end)
        assert meeting.id not in [m.id for m in result]


class TestGetAnalytics:
    def test_returns_stats(self, founder, meeting):
        analytics = MeetingService.get_analytics(founder)
        assert "total_meetings" in analytics
        assert "completed_meetings" in analytics
        assert "cancelled_meetings" in analytics
        assert "upcoming_meetings" in analytics
        assert "completion_rate" in analytics

    def test_counts_reflect_reality(self, founder, meeting):
        analytics = MeetingService.get_analytics(founder)
        assert analytics["total_meetings"] == 1
        assert analytics["upcoming_meetings"] >= 1


class TestUpdateAvailability:
    def test_creates_slots(self, founder):
        slots_data = [
            {"day_of_week": 0, "start_time": datetime.time(9, 0), "end_time": datetime.time(12, 0)},
            {"day_of_week": 0, "start_time": datetime.time(13, 0), "end_time": datetime.time(17, 0)},
            {"day_of_week": 2, "start_time": datetime.time(9, 0), "end_time": datetime.time(17, 0)},
        ]
        slots = MeetingService.update_availability(founder, slots_data)
        assert len(slots) == 3
        assert all(s.user == founder for s in slots)

    def test_replaces_existing_slots(self, founder):
        MeetingAvailabilityFactory(user=founder, day_of_week=0)
        assert founder.meeting_availabilities.count() == 1
        slots_data = [
            {"day_of_week": 1, "start_time": datetime.time(10, 0), "end_time": datetime.time(16, 0)},
        ]
        MeetingService.update_availability(founder, slots_data)
        assert founder.meeting_availabilities.count() == 1
        assert founder.meeting_availabilities.first().day_of_week == 1

    def test_get_availability(self, founder):
        MeetingAvailabilityFactory(user=founder, day_of_week=0)
        slots = MeetingService.get_availability(founder)
        assert len(slots) == 1
