import datetime

import pytest
from django.db import IntegrityError
from django.utils import timezone

from apps.accounts.models import User
from apps.meetings.models import Meeting, MeetingParticipant, MeetingAvailability, MeetingEvent
from apps.common.tests.factories import UserFactory, InvestorFactory, StartupFactory, MeetingFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def investor():
    return InvestorFactory()


@pytest.fixture
def startup():
    return StartupFactory()


@pytest.fixture
def meeting(user, investor):
    return MeetingFactory(
        organizer=user, investor=investor,
        scheduled_start=timezone.now() + datetime.timedelta(days=7),
        scheduled_end=timezone.now() + datetime.timedelta(days=7, hours=1),
    )


class TestMeeting:
    def test_create_meeting_with_default_status(self, user, investor, startup):
        meeting = Meeting.objects.create(
            organizer=user,
            startup=startup,
            investor=investor,
            title="Intro Call",
            scheduled_start=timezone.now() + datetime.timedelta(days=1),
            scheduled_end=timezone.now() + datetime.timedelta(days=1, hours=1),
        )
        assert meeting.status == Meeting.Status.SCHEDULED
        assert meeting.title == "Intro Call"
        assert meeting.meeting_type == Meeting.MeetingType.INTRO_CALL

    def test_meeting_str(self, user, investor):
        start = timezone.now() + datetime.timedelta(days=1)
        meeting = Meeting.objects.create(
            organizer=user,
            investor=investor,
            title="Strategy Sync",
            scheduled_start=start,
            scheduled_end=start + datetime.timedelta(hours=1),
        )
        assert str(meeting) == f"Strategy Sync ({start.date()})"

    def test_meeting_status_choices(self, user, investor):
        start = timezone.now() + datetime.timedelta(days=1)
        meeting = Meeting.objects.create(
            organizer=user, investor=investor, title="Test",
            scheduled_start=start, scheduled_end=start + datetime.timedelta(hours=1),
            status=Meeting.Status.CONFIRMED,
        )
        assert meeting.status == "confirmed"
        meeting.status = Meeting.Status.COMPLETED
        meeting.save()
        meeting.refresh_from_db()
        assert meeting.status == "completed"

    def test_meeting_type_choices(self, user, investor):
        start = timezone.now() + datetime.timedelta(days=1)
        meeting = Meeting.objects.create(
            organizer=user, investor=investor, title="DD",
            scheduled_start=start, scheduled_end=start + datetime.timedelta(hours=1),
            meeting_type=Meeting.MeetingType.DUE_DILIGENCE,
        )
        assert meeting.meeting_type == "due_diligence"


class TestMeetingParticipant:
    def test_create_participant(self, user, meeting):
        participant = MeetingParticipant.objects.create(
            meeting=meeting, user=user,
        )
        assert participant.attendance_status == MeetingParticipant.Attendance.PENDING

    def test_unique_constraint(self, user, meeting):
        MeetingParticipant.objects.create(meeting=meeting, user=user)
        with pytest.raises(IntegrityError):
            MeetingParticipant.objects.create(meeting=meeting, user=user)

    def test_str(self, user, meeting):
        participant = MeetingParticipant.objects.create(meeting=meeting, user=user)
        assert str(participant) == f"{user.email} - pending"


class TestMeetingAvailability:
    def test_create_availability_slot(self, user):
        slot = MeetingAvailability.objects.create(
            user=user,
            day_of_week=0,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(17, 0),
        )
        assert slot.day_of_week == 0
        assert slot.start_time == datetime.time(9, 0)

    def test_day_of_week_constraints(self, user):
        for day in range(7):
            slot = MeetingAvailability.objects.create(
                user=user, day_of_week=day,
                start_time=datetime.time(9, 0),
                end_time=datetime.time(10, 0),
            )
            assert slot.day_of_week == day

    def test_day_of_week_out_of_range_raises(self, user):
        with pytest.raises(IntegrityError):
            MeetingAvailability.objects.create(
                user=user, day_of_week=7,
                start_time=datetime.time(9, 0),
                end_time=datetime.time(10, 0),
            )

    def test_unique_together(self, user):
        MeetingAvailability.objects.create(
            user=user, day_of_week=0,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0),
        )
        with pytest.raises(IntegrityError):
            MeetingAvailability.objects.create(
                user=user, day_of_week=0,
                start_time=datetime.time(9, 0),
                end_time=datetime.time(10, 0),
            )

    def test_str(self, user):
        slot = MeetingAvailability.objects.create(
            user=user, day_of_week=0,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(17, 0),
        )
        assert str(slot) == f"{user.email} - Mon 09:00:00-17:00:00"


class TestMeetingEvent:
    def test_create_event(self, user, meeting):
        event = MeetingEvent.objects.create(
            meeting=meeting,
            actor=user,
            action=MeetingEvent.Action.CREATED,
        )
        assert event.action == "created"
        assert event.actor == user
        assert event.metadata == {}

    def test_action_choices(self, user, meeting):
        for action, _ in MeetingEvent.Action.choices:
            event = MeetingEvent.objects.create(
                meeting=meeting, actor=user, action=action,
            )
            assert event.action == action

    def test_str(self, user, meeting):
        event = MeetingEvent.objects.create(
            meeting=meeting, actor=user,
            action=MeetingEvent.Action.CREATED,
        )
        assert str(event) == f"created by {user.email}"
