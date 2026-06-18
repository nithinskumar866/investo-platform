import logging
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from django.conf import settings

from apps.common.exceptions import ApplicationError

from .models import Meeting, MeetingEvent
from .repositories import MeetingRepository

logger = logging.getLogger(__name__)

MEETING_LINK_PROVIDERS = {
    "zoom": "https://zoom.us/j/",
    "google_meet": "https://meet.google.com/",
    "teams": "https://teams.microsoft.com/l/meetup-join/",
    "custom": "",
}


class MeetingService:
    """Business logic for meeting operations."""

    @staticmethod
    def _validate_match(organizer, investor, startup):
        from apps.matching.models import MatchScore
        match_exists = MatchScore.objects.filter(
            investor=investor,
            startup=startup,
            status__in=[
                MatchScore.Status.RECOMMENDED,
                MatchScore.Status.SAVED,
                MatchScore.Status.CONTACTED,
            ],
        ).exists() if startup else False

        if not match_exists and startup:
            if organizer.role == "investor":
                match_exists = MatchScore.objects.filter(
                    investor=organizer,
                    startup=startup,
                ).exclude(
                    status=MatchScore.Status.DISMISSED,
                ).exists()
            else:
                match_exists = MatchScore.objects.filter(
                    investor=investor,
                    startup=startup,
                ).exclude(
                    status=MatchScore.Status.DISMISSED,
                ).exists()

        return match_exists

    @staticmethod
    def _validate_participants(organizer, investor):
        if organizer == investor:
            raise ApplicationError(
                "Cannot schedule a meeting with yourself",
                "SELF_MEETING", 400,
            )

        if organizer.role == investor.role:
            raise ApplicationError(
                "Meetings can only be scheduled between an investor and a founder",
                "ROLE_MISMATCH", 400,
            )

    @staticmethod
    def _generate_meeting_link(meeting_type, startup=None):
        if settings.DEBUG:
            return ""

        provider = getattr(settings, "MEETING_PROVIDER", "google_meet")
        base = MEETING_LINK_PROVIDERS.get(provider, "")
        if provider == "custom":
            return getattr(settings, "MEETING_BASE_URL", "") + "/meeting/placeholder"
        return base + "placeholder"

    # ── Core operations ───────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def schedule_meeting(organizer, data):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        investor_id = data.get("investor_id") or data.get("investor")
        startup_raw = data.get("startup")

        try:
            investor = User.objects.get(id=investor_id)
        except Exception:
            raise ApplicationError("Investor not found", "NOT_FOUND", 404)

        MeetingService._validate_participants(organizer, investor)

        startup_obj = None
        if startup_raw:
            startup_id = startup_raw if isinstance(startup_raw, int) else getattr(startup_raw, "id", None)
            if startup_id:
                from apps.startups.repositories import StartupRepository
                startup_obj = StartupRepository.get_by_id(startup_id)
                if not startup_obj:
                    raise ApplicationError("Startup not found", "NOT_FOUND", 404)
            if not MeetingService._validate_match(organizer, investor, startup_obj):
                raise ApplicationError(
                    "Can only schedule meetings with matched investors",
                    "NOT_MATCHED", 400,
                )

        if MeetingRepository.get_overlapping_meetings(
            organizer, data["scheduled_start"], data["scheduled_end"],
        ):
            raise ApplicationError(
                "You have an overlapping meeting at this time",
                "OVERLAPPING", 400,
            )

        if MeetingRepository.get_overlapping_meetings(
            investor, data["scheduled_start"], data["scheduled_end"],
        ):
            raise ApplicationError(
                "The investor has an overlapping meeting at this time",
                "INVESTOR_OVERLAPPING", 400,
            )

        meeting_link = MeetingService._generate_meeting_link(
            data.get("meeting_type", Meeting.MeetingType.INTRO_CALL),
            startup_obj,
        )

        meeting = MeetingRepository.create_meeting(
            data, organizer, investor, meeting_link=meeting_link,
        )

        if startup_obj and meeting.startup_id is None:
            meeting.startup = startup_obj
            meeting.save(update_fields=["startup"])
        elif startup_obj:
            pass

        MeetingRepository.create_event(
            meeting, organizer, MeetingEvent.Action.CREATED,
            {"meeting_type": meeting.meeting_type, "startup_id": startup_obj.id if startup_obj else None},
        )

        from apps.notifications.services import NotificationService
        NotificationService.notify(
            recipient=investor,
            notification_type="system",
            title="Meeting Scheduled",
            message=f"{organizer.email} scheduled a {meeting.get_meeting_type_display()} with you",
            actor=organizer,
            data={
                "meeting_id": meeting.id,
                "scheduled_start": meeting.scheduled_start.isoformat(),
                "meeting_type": meeting.meeting_type,
            },
        )

        from apps.activity_feed.services import ActivityFeedService
        ActivityFeedService.publish_activity(
            actor=organizer,
            activity_type="meeting_scheduled",
            title=f"{organizer.email} scheduled a {meeting.get_meeting_type_display()} with {investor.email}",
            startup=startup_obj,
            investor=investor,
            target_object_id=meeting.id,
            target_object_type="meeting",
            metadata={
                "meeting_type": meeting.meeting_type,
                "scheduled_start": meeting.scheduled_start.isoformat(),
            },
        )

        from apps.realtime.services import RealtimeService
        RealtimeService.broadcast_to_user(
            user_id=organizer.id,
            event_type="meeting_created",
            payload={"meeting": {"id": meeting.id, "title": meeting.title or "", "meeting_type": meeting.meeting_type, "scheduled_start": meeting.scheduled_start.isoformat(), "status": meeting.status}},
        )
        RealtimeService.broadcast_to_user(
            user_id=investor.id,
            event_type="meeting_created",
            payload={"meeting": {"id": meeting.id, "title": meeting.title or "", "meeting_type": meeting.meeting_type, "scheduled_start": meeting.scheduled_start.isoformat(), "status": meeting.status}},
        )

        logger.info(
            f"Meeting scheduled: {meeting.title} by {organizer.email} "
            f"with {investor.email}",
        )
        return meeting

    @staticmethod
    @transaction.atomic
    def confirm_meeting(meeting_id, user):
        meeting = MeetingService._get_meeting(meeting_id, user)

        if meeting.status != Meeting.Status.SCHEDULED:
            raise ApplicationError(
                "Only scheduled meetings can be confirmed",
                "INVALID_STATUS", 400,
            )

        if user not in [meeting.organizer, meeting.investor] and \
           not meeting.participants.filter(user=user).exists():
            raise ApplicationError("Not a participant", "FORBIDDEN", 403)

        MeetingRepository.update_status(meeting, Meeting.Status.CONFIRMED)
        MeetingRepository.update_participant_status(meeting, user, "accepted")

        MeetingRepository.create_event(
            meeting, user, MeetingEvent.Action.CONFIRMED,
        )

        other = meeting.investor if user == meeting.organizer else meeting.organizer
        from apps.notifications.services import NotificationService
        NotificationService.notify(
            recipient=other,
            notification_type="system",
            title="Meeting Confirmed",
            message=f"{user.email} confirmed the meeting '{meeting.title}'",
            actor=user,
            data={"meeting_id": meeting.id},
        )

        from apps.realtime.services import RealtimeService
        RealtimeService.broadcast_to_user(
            user_id=meeting.organizer_id,
            event_type="meeting_confirmed",
            payload={"meeting": {"id": meeting.id, "title": meeting.title or "", "status": meeting.status}},
        )
        RealtimeService.broadcast_to_user(
            user_id=meeting.investor_id,
            event_type="meeting_confirmed",
            payload={"meeting": {"id": meeting.id, "title": meeting.title or "", "status": meeting.status}},
        )

        return meeting

    @staticmethod
    @transaction.atomic
    def cancel_meeting(meeting_id, user, reason=None):
        meeting = MeetingService._get_meeting(meeting_id, user)

        if meeting.status in [Meeting.Status.COMPLETED, Meeting.Status.CANCELLED]:
            raise ApplicationError(
                "Meeting is already closed", "ALREADY_CLOSED", 400,
            )

        MeetingRepository.update_status(meeting, Meeting.Status.CANCELLED)
        MeetingRepository.create_event(
            meeting, user, MeetingEvent.Action.CANCELLED,
            {"reason": reason},
        )

        other = meeting.investor if user == meeting.organizer else meeting.organizer
        from apps.notifications.services import NotificationService
        NotificationService.notify(
            recipient=other,
            notification_type="system",
            title="Meeting Cancelled",
            message=f"{user.email} cancelled '{meeting.title}'",
            actor=user,
            data={"meeting_id": meeting.id, "reason": reason},
        )

        from apps.realtime.services import RealtimeService
        RealtimeService.broadcast_to_user(
            user_id=meeting.organizer_id,
            event_type="meeting_cancelled",
            payload={"meeting": {"id": meeting.id, "title": meeting.title or "", "status": meeting.status}, "reason": reason},
        )
        RealtimeService.broadcast_to_user(
            user_id=meeting.investor_id,
            event_type="meeting_cancelled",
            payload={"meeting": {"id": meeting.id, "title": meeting.title or "", "status": meeting.status}, "reason": reason},
        )

        return meeting

    @staticmethod
    @transaction.atomic
    def reschedule_meeting(meeting_id, user, data):
        meeting = MeetingService._get_meeting(meeting_id, user)

        if meeting.status in [Meeting.Status.COMPLETED, Meeting.Status.CANCELLED]:
            raise ApplicationError(
                "Cannot reschedule a closed meeting", "ALREADY_CLOSED", 400,
            )

        old_start = meeting.scheduled_start
        old_end = meeting.scheduled_end

        if "scheduled_start" in data:
            meeting.scheduled_start = data["scheduled_start"]
        if "scheduled_end" in data:
            meeting.scheduled_end = data["scheduled_end"]
        if "timezone" in data:
            meeting.timezone = data["timezone"]
        meeting.save()

        MeetingRepository.update_status(meeting, Meeting.Status.SCHEDULED)

        MeetingRepository.create_event(
            meeting, user, MeetingEvent.Action.RESCHEDULED,
            {
                "old_start": old_start.isoformat(),
                "new_start": meeting.scheduled_start.isoformat(),
                "old_end": old_end.isoformat(),
                "new_end": meeting.scheduled_end.isoformat(),
            },
        )

        other = meeting.investor if user == meeting.organizer else meeting.organizer
        from apps.notifications.services import NotificationService
        NotificationService.notify(
            recipient=other,
            notification_type="system",
            title="Meeting Rescheduled",
            message=f"{user.email} rescheduled '{meeting.title}'",
            actor=user,
            data={
                "meeting_id": meeting.id,
                "old_start": old_start.isoformat(),
                "new_start": meeting.scheduled_start.isoformat(),
            },
        )

        from apps.realtime.services import RealtimeService
        RealtimeService.broadcast_to_user(
            user_id=meeting.organizer_id,
            event_type="meeting_updated",
            payload={"meeting": {"id": meeting.id, "title": meeting.title or "", "scheduled_start": meeting.scheduled_start.isoformat(), "status": meeting.status}},
        )
        RealtimeService.broadcast_to_user(
            user_id=meeting.investor_id,
            event_type="meeting_updated",
            payload={"meeting": {"id": meeting.id, "title": meeting.title or "", "scheduled_start": meeting.scheduled_start.isoformat(), "status": meeting.status}},
        )

        return meeting

    @staticmethod
    @transaction.atomic
    def complete_meeting(meeting_id, user, notes=None):
        meeting = MeetingService._get_meeting(meeting_id, user)

        if meeting.status in [Meeting.Status.CANCELLED, Meeting.Status.COMPLETED]:
            raise ApplicationError(
                "Meeting is already closed", "ALREADY_CLOSED", 400,
            )

        MeetingRepository.update_status(meeting, Meeting.Status.COMPLETED)
        if notes:
            meeting.notes = notes
            meeting.save(update_fields=["notes"])

        MeetingRepository.create_event(
            meeting, user, MeetingEvent.Action.COMPLETED,
        )

        other = meeting.investor if user == meeting.organizer else meeting.organizer
        from apps.notifications.services import NotificationService
        NotificationService.notify(
            recipient=other,
            notification_type="system",
            title="Meeting Completed",
            message=f"{user.email} marked '{meeting.title}' as completed",
            actor=user,
            data={"meeting_id": meeting.id},
        )

        from apps.activity_feed.services import ActivityFeedService
        ActivityFeedService.publish_activity(
            actor=user,
            activity_type="meeting_completed",
            title=f"{user.email} completed meeting '{meeting.title}'",
            startup=meeting.startup,
            investor=meeting.investor if user == meeting.organizer else meeting.organizer,
            target_object_id=meeting.id,
            target_object_type="meeting",
        )

        from apps.realtime.services import RealtimeService
        RealtimeService.broadcast_to_user(
            user_id=meeting.organizer_id,
            event_type="meeting_updated",
            payload={"meeting": {"id": meeting.id, "title": meeting.title or "", "status": meeting.status}},
        )
        RealtimeService.broadcast_to_user(
            user_id=meeting.investor_id,
            event_type="meeting_updated",
            payload={"meeting": {"id": meeting.id, "title": meeting.title or "", "status": meeting.status}},
        )

        return meeting

    # ── Read ──────────────────────────────────────────────────────

    @staticmethod
    def _get_meeting(meeting_id, user):
        meeting = MeetingRepository.get_meeting(meeting_id)
        if not meeting:
            raise ApplicationError("Meeting not found", "NOT_FOUND", 404)

        if user not in [meeting.organizer, meeting.investor] and \
           not meeting.participants.filter(user=user).exists():
            raise ApplicationError("Not a participant", "FORBIDDEN", 403)
        return meeting

    @staticmethod
    def get_meeting(meeting_id, user):
        return MeetingService._get_meeting(meeting_id, user)

    @staticmethod
    def list_meetings(user, cursor=None, limit=20):
        return MeetingRepository.get_user_meetings(user, cursor=cursor, limit=limit)

    @staticmethod
    def list_upcoming(user, cursor=None, limit=20):
        return MeetingRepository.get_upcoming_meetings(user, cursor=cursor, limit=limit)

    @staticmethod
    def list_past(user, cursor=None, limit=20):
        return MeetingRepository.get_past_meetings(user, cursor=cursor, limit=limit)

    @staticmethod
    def get_calendar(user, start_date, end_date):
        return MeetingRepository.get_calendar_meetings(user, start_date, end_date)

    # ── Availability ──────────────────────────────────────────────

    @staticmethod
    def get_availability(user):
        return MeetingRepository.get_availability(user)

    @staticmethod
    def update_availability(user, slots_data):
        return MeetingRepository.update_availability(user, slots_data)

    # ── Timeline ──────────────────────────────────────────────────

    @staticmethod
    def get_timeline(meeting_id, user):
        meeting = MeetingService._get_meeting(meeting_id, user)
        return MeetingRepository.get_timeline(meeting)

    # ── Analytics ─────────────────────────────────────────────────

    @staticmethod
    def get_analytics(user):
        role = getattr(user, "role", None)
        return MeetingRepository.get_analytics(user, role)



