from django.db import transaction
from django.utils import timezone

from .models import Meeting, MeetingParticipant, MeetingAvailability, MeetingEvent


class MeetingRepository:
    """Data access layer for meeting operations."""

    # ── Meeting CRUD ──────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def create_meeting(data, organizer, investor, meeting_link=""):
        meeting = Meeting.objects.create(
            organizer=organizer,
            startup=data.get("startup"),
            investor=investor,
            title=data["title"],
            description=data.get("description", ""),
            meeting_type=data.get("meeting_type", Meeting.MeetingType.INTRO_CALL),
            scheduled_start=data["scheduled_start"],
            scheduled_end=data["scheduled_end"],
            timezone=data.get("timezone", "UTC"),
            meeting_link=meeting_link,
            location=data.get("location", ""),
            notes=data.get("notes", ""),
        )

        MeetingParticipant.objects.create(
            meeting=meeting, user=organizer, attendance_status="accepted",
        )
        MeetingParticipant.objects.create(
            meeting=meeting, user=investor,
        )

        return meeting

    @staticmethod
    @transaction.atomic
    def update_meeting(meeting, data):
        updatable = [
            "title", "description", "meeting_type", "meeting_link",
            "location", "notes", "scheduled_start", "scheduled_end", "timezone",
        ]
        for field in updatable:
            if field in data:
                setattr(meeting, field, data[field])
        meeting.save()
        return meeting

    @staticmethod
    @transaction.atomic
    def update_status(meeting, status):
        meeting.status = status
        meeting.save(update_fields=["status", "updated_at"])
        return meeting

    # ── Read ──────────────────────────────────────────────────────

    @staticmethod
    def get_meeting(meeting_id):
        return Meeting.objects.select_related(
            "organizer", "investor", "startup",
        ).prefetch_related(
            "participants", "participants__user", "events", "events__actor",
        ).filter(id=meeting_id).first()

    @staticmethod
    def get_user_meetings(user, cursor=None, limit=20):
        qs = Meeting.objects.filter(
            participants__user=user,
        ).select_related(
            "organizer", "investor", "startup",
        ).order_by("-scheduled_start").distinct()
        if cursor:
            qs = qs.filter(scheduled_start__lt=cursor)
        results = list(qs[:limit])
        has_more = qs[limit:].exists() if len(results) == limit else False
        return results, has_more

    @staticmethod
    def get_upcoming_meetings(user, cursor=None, limit=20):
        now = timezone.now()
        qs = Meeting.objects.filter(
            participants__user=user,
            scheduled_start__gte=now,
        ).exclude(
            status__in=[Meeting.Status.CANCELLED, Meeting.Status.COMPLETED],
        ).select_related(
            "organizer", "investor", "startup",
        ).order_by("scheduled_start").distinct()
        if cursor:
            qs = qs.filter(scheduled_start__gt=cursor)
        results = list(qs[:limit])
        has_more = qs[limit:].exists() if len(results) == limit else False
        return results, has_more

    @staticmethod
    def get_past_meetings(user, cursor=None, limit=20):
        now = timezone.now()
        qs = Meeting.objects.filter(
            participants__user=user,
            scheduled_start__lt=now,
        ).exclude(
            status=Meeting.Status.CANCELLED,
        ).select_related(
            "organizer", "investor", "startup",
        ).order_by("-scheduled_start").distinct()
        if cursor:
            qs = qs.filter(scheduled_start__lt=cursor)
        results = list(qs[:limit])
        has_more = qs[limit:].exists() if len(results) == limit else False
        return results, has_more

    @staticmethod
    def get_calendar_meetings(user, start_date, end_date):
        return Meeting.objects.filter(
            participants__user=user,
            scheduled_start__gte=start_date,
            scheduled_start__lte=end_date,
        ).exclude(
            status=Meeting.Status.CANCELLED,
        ).select_related(
            "organizer", "investor", "startup",
        ).order_by("scheduled_start").distinct()

    @staticmethod
    def get_overlapping_meetings(user, start, end):
        return Meeting.objects.filter(
            participants__user=user,
            scheduled_start__lt=end,
            scheduled_end__gt=start,
        ).exclude(
            status__in=[Meeting.Status.CANCELLED, Meeting.Status.COMPLETED],
        ).exists()

    # ── Availability ──────────────────────────────────────────────

    @staticmethod
    def get_availability(user):
        return MeetingAvailability.objects.filter(user=user).order_by("day_of_week", "start_time")

    @staticmethod
    def update_availability(user, slots_data):
        MeetingAvailability.objects.filter(user=user).delete()
        slots = []
        for slot in slots_data:
            slots.append(MeetingAvailability(
                user=user,
                day_of_week=slot["day_of_week"],
                start_time=slot["start_time"],
                end_time=slot["end_time"],
                timezone=slot.get("timezone", "UTC"),
            ))
        return MeetingAvailability.objects.bulk_create(slots)

    @staticmethod
    def has_availability(user):
        return MeetingAvailability.objects.filter(user=user).exists()

    # ── Participants ──────────────────────────────────────────────

    @staticmethod
    def update_participant_status(meeting, user, status):
        participant = MeetingParticipant.objects.filter(
            meeting=meeting, user=user,
        ).first()
        if participant:
            participant.attendance_status = status
            if status == "accepted":
                participant.joined_at = timezone.now()
            participant.save()
        return participant

    @staticmethod
    def get_participant_count(meeting):
        return meeting.participants.count()

    # ── Events ────────────────────────────────────────────────────

    @staticmethod
    def create_event(meeting, actor, action, metadata=None):
        return MeetingEvent.objects.create(
            meeting=meeting,
            actor=actor,
            action=action,
            metadata=metadata or {},
        )

    @staticmethod
    def get_timeline(meeting):
        return MeetingEvent.objects.filter(
            meeting=meeting,
        ).select_related("actor").order_by("created_at")

    # ── Analytics ─────────────────────────────────────────────────

    @staticmethod
    def get_analytics(user, role):
        qs = Meeting.objects.filter(
            participants__user=user,
        ).exclude(status=Meeting.Status.CANCELLED)

        total = qs.count()
        completed = qs.filter(status=Meeting.Status.COMPLETED).count()
        cancelled = Meeting.objects.filter(
            participants__user=user,
            status=Meeting.Status.CANCELLED,
        ).count()
        upcoming = qs.filter(
            scheduled_start__gte=timezone.now(),
        ).count()

        return {
            "total_meetings": total,
            "completed_meetings": completed,
            "cancelled_meetings": cancelled,
            "upcoming_meetings": upcoming,
            "completion_rate": round(
                (completed / total * 100) if total else 0, 1,
            ),
        }
