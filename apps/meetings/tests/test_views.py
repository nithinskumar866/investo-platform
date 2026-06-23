import datetime

import pytest
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone

from conftest import get_data, assert_success_response, assert_error_response

from apps.accounts.models import User
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
def meeting(founder, investor, startup):
    return MeetingFactory(
        organizer=founder, investor=investor, startup=startup,
        scheduled_start=timezone.now() + datetime.timedelta(days=7),
        scheduled_end=timezone.now() + datetime.timedelta(days=7, hours=1),
    )


MEETINGS_LIST = reverse("meeting-list")
AVAILABILITY_LIST = reverse("availability")


def meeting_detail(pk):
    return reverse("meeting-detail", args=[pk])


def meeting_confirm(pk):
    return reverse("meeting-confirm", args=[pk])


def meeting_cancel(pk):
    return reverse("meeting-cancel", args=[pk])


def meeting_reschedule(pk):
    return reverse("meeting-reschedule", args=[pk])


def meeting_complete(pk):
    return reverse("meeting-complete", args=[pk])


def meeting_timeline(pk):
    return reverse("meeting-timeline", args=[pk])


MEETINGS_UPCOMING = reverse("meeting-upcoming")
MEETINGS_PAST = reverse("meeting-past")
MEETINGS_CALENDAR = reverse("meeting-calendar")
MEETINGS_ANALYTICS = reverse("meeting-analytics")


class TestListMeetings:
    def test_returns_meetings(self, founder_client, meeting):
        response = founder_client.get(MEETINGS_LIST)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        ids = [m["id"] for m in data["results"]]
        assert meeting.id in ids

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(MEETINGS_LIST)
        assert response.status_code == 401

    def test_empty_list(self, founder_client):
        response = founder_client.get(MEETINGS_LIST)
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 0


class TestCreateMeeting:
    @patch("apps.notifications.services.NotificationService.notify")
    @patch("apps.activity_feed.services.ActivityFeedService.publish_activity")
    @patch("apps.realtime.services.RealtimeService.broadcast_to_user")
    def test_creates_meeting(
        self, mock_rt, mock_af, mock_notify,
        founder_client, founder, investor, startup, match,
    ):
        start = timezone.now() + datetime.timedelta(days=10)
        end = start + datetime.timedelta(hours=1)
        response = founder_client.post(MEETINGS_LIST, {
            "title": "Pitch Meeting",
            "meeting_type": "pitch_meeting",
            "investor_id": investor.id,
            "startup": startup.id,
            "scheduled_start": start.isoformat(),
            "scheduled_end": end.isoformat(),
            "timezone": "UTC",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Pitch Meeting"
        assert data["status"] == "scheduled"

    def test_unauthenticated_returns_401(self, api_client, investor):
        response = api_client.post(MEETINGS_LIST, {
            "title": "Test", "investor_id": investor.id,
            "scheduled_start": timezone.now().isoformat(),
            "scheduled_end": (timezone.now() + datetime.timedelta(hours=1)).isoformat(),
        })
        assert response.status_code == 401


class TestRetrieveMeeting:
    def test_retrieves_meeting(self, founder_client, meeting):
        response = founder_client.get(meeting_detail(meeting.id))
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == meeting.id

    def test_non_participant_cannot_access(self, meeting):
        stranger = UserFactory()
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        client = APIClient()
        refresh = RefreshToken.for_user(stranger)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        response = client.get(meeting_detail(meeting.id))
        assert response.status_code == 403

    def test_unauthenticated_returns_401(self, api_client, meeting):
        response = api_client.get(meeting_detail(meeting.id))
        assert response.status_code == 401


class TestUpdateMeeting:
    def test_organizer_can_update(self, founder_client, meeting):
        response = founder_client.patch(
            meeting_detail(meeting.id),
            {"title": "Updated Title"},
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"

    def test_non_organizer_cannot_update(self, investor_client, meeting):
        response = investor_client.patch(
            meeting_detail(meeting.id),
            {"title": "Hacked"},
        )
        assert response.status_code == 403

    def test_unauthenticated_returns_401(self, api_client, meeting):
        response = api_client.patch(
            meeting_detail(meeting.id),
            {"title": "Test"},
        )
        assert response.status_code == 401


class TestConfirmMeeting:
    def test_confirm(self, founder_client, meeting):
        response = founder_client.post(meeting_confirm(meeting.id))
        assert response.status_code == 200
        assert response.json()["status"] == "confirmed"

    def test_unauthenticated_returns_401(self, api_client, meeting):
        response = api_client.post(meeting_confirm(meeting.id))
        assert response.status_code == 401


class TestCancelMeeting:
    def test_cancel(self, founder_client, meeting):
        response = founder_client.post(meeting_cancel(meeting.id), {"reason": "Conflict"})
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

    def test_unauthenticated_returns_401(self, api_client, meeting):
        response = api_client.post(meeting_cancel(meeting.id))
        assert response.status_code == 401


class TestRescheduleMeeting:
    def test_reschedule(self, founder_client, meeting):
        new_start = meeting.scheduled_start + datetime.timedelta(days=3)
        new_end = meeting.scheduled_end + datetime.timedelta(days=3)
        response = founder_client.post(meeting_reschedule(meeting.id), {
            "scheduled_start": new_start.isoformat(),
            "scheduled_end": new_end.isoformat(),
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "scheduled"

    def test_unauthenticated_returns_401(self, api_client, meeting):
        response = api_client.post(meeting_reschedule(meeting.id), {
            "scheduled_start": timezone.now().isoformat(),
            "scheduled_end": (timezone.now() + datetime.timedelta(hours=1)).isoformat(),
        })
        assert response.status_code == 401


class TestCompleteMeeting:
    def test_complete(self, founder_client, meeting):
        meeting.status = "confirmed"
        meeting.save()
        response = founder_client.post(meeting_complete(meeting.id), {"notes": "Done!"})
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

    def test_unauthenticated_returns_401(self, api_client, meeting):
        response = api_client.post(meeting_complete(meeting.id))
        assert response.status_code == 401


class TestUpcoming:
    def test_returns_upcoming(self, founder_client, meeting):
        response = founder_client.get(MEETINGS_UPCOMING)
        assert response.status_code == 200
        data = response.json()
        ids = [m["id"] for m in data["results"]]
        assert meeting.id in ids

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(MEETINGS_UPCOMING)
        assert response.status_code == 401


class TestPast:
    def test_returns_past(self, founder_client, meeting):
        meeting.scheduled_start = timezone.now() - datetime.timedelta(days=10)
        meeting.scheduled_end = timezone.now() - datetime.timedelta(days=10) + datetime.timedelta(hours=1)
        meeting.save()
        response = founder_client.get(MEETINGS_PAST)
        assert response.status_code == 200
        data = response.json()
        ids = [m["id"] for m in data["results"]]
        assert meeting.id in ids

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(MEETINGS_PAST)
        assert response.status_code == 401


class TestCalendar:
    def test_returns_meetings_in_range(self, founder_client, meeting):
        start = meeting.scheduled_start - datetime.timedelta(days=1)
        end = meeting.scheduled_end + datetime.timedelta(days=1)
        response = founder_client.get(
            MEETINGS_CALENDAR,
            {"start": start.isoformat(), "end": end.isoformat()},
        )
        assert response.status_code == 200
        ids = [m["id"] for m in response.json()]
        assert meeting.id in ids

    def test_missing_params_returns_400(self, founder_client):
        response = founder_client.get(MEETINGS_CALENDAR)
        assert response.status_code == 400

    def test_invalid_date_returns_400(self, founder_client):
        response = founder_client.get(
            MEETINGS_CALENDAR,
            {"start": "not-a-date", "end": "also-not-a-date"},
        )
        assert response.status_code == 400

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(MEETINGS_CALENDAR)
        assert response.status_code == 401


class TestAnalytics:
    def test_returns_analytics(self, founder_client, meeting):
        response = founder_client.get(MEETINGS_ANALYTICS)
        assert response.status_code == 200
        data = response.json()
        assert "total_meetings" in data

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(MEETINGS_ANALYTICS)
        assert response.status_code == 401


class TestTimeline:
    def test_returns_timeline(self, founder_client, meeting):
        response = founder_client.get(meeting_timeline(meeting.id))
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_unauthenticated_returns_401(self, api_client, meeting):
        response = api_client.get(meeting_timeline(meeting.id))
        assert response.status_code == 401


class TestAvailability:
    def test_list_availability(self, founder_client, founder):
        MeetingAvailabilityFactory(user=founder, day_of_week=0)
        response = founder_client.get(AVAILABILITY_LIST)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_create_availability(self, founder_client):
        response = founder_client.post(AVAILABILITY_LIST, [
            {"day_of_week": 0, "start_time": "09:00:00", "end_time": "17:00:00"},
            {"day_of_week": 2, "start_time": "09:00:00", "end_time": "17:00:00"},
        ], format="json")
        assert response.status_code == 201
        assert len(response.json()) == 2

    def test_unauthenticated_list_returns_401(self, api_client):
        response = api_client.get(AVAILABILITY_LIST)
        assert response.status_code == 401

    def test_unauthenticated_create_returns_401(self, api_client):
        response = api_client.post(
            AVAILABILITY_LIST,
            [{"day_of_week": 0, "start_time": "09:00", "end_time": "17:00"}],
            format="json",
        )
        assert response.status_code == 401
