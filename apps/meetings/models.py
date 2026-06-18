from django.conf import settings
from django.db import models


class Meeting(models.Model):
    class MeetingType(models.TextChoices):
        INTRO_CALL = "intro_call", "Intro Call"
        PITCH_MEETING = "pitch_meeting", "Pitch Meeting"
        DUE_DILIGENCE = "due_diligence", "Due Diligence"
        NEGOTIATION = "negotiation", "Negotiation"
        FOLLOW_UP = "follow_up", "Follow Up"
        INVESTMENT_COMMITTEE = "investment_committee", "Investment Committee"
        CUSTOM = "custom", "Custom"

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        CONFIRMED = "confirmed", "Confirmed"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organized_meetings",
    )
    startup = models.ForeignKey(
        "startups.Startup",
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="meetings",
    )
    investor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="investor_meetings",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    meeting_type = models.CharField(
        max_length=25,
        choices=MeetingType.choices,
        default=MeetingType.INTRO_CALL,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
        db_index=True,
    )
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    timezone = models.CharField(max_length=50, default="UTC")
    meeting_link = models.URLField(blank=True, default="")
    location = models.CharField(max_length=255, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "meetings_meeting"
        ordering = ["-scheduled_start"]
        indexes = [
            models.Index(fields=["organizer", "status"]),
            models.Index(fields=["investor", "status"]),
            models.Index(fields=["startup", "status"]),
            models.Index(fields=["scheduled_start", "scheduled_end"]),
            models.Index(fields=["status", "scheduled_start"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.scheduled_start.date()})"


class MeetingParticipant(models.Model):
    class Attendance(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"
        MAYBE = "maybe", "Maybe"

    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name="participants",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="meeting_participations",
    )
    attendance_status = models.CharField(
        max_length=10,
        choices=Attendance.choices,
        default=Attendance.PENDING,
    )
    joined_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "meetings_participant"
        unique_together = ["meeting", "user"]
        indexes = [
            models.Index(fields=["user", "attendance_status"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.attendance_status}"


class MeetingAvailability(models.Model):
    DAYS_OF_WEEK = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="meeting_availabilities",
    )
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    timezone = models.CharField(max_length=50, default="UTC")

    class Meta:
        db_table = "meetings_availability"
        unique_together = [["user", "day_of_week", "start_time", "end_time"]]
        indexes = [
            models.Index(fields=["user", "day_of_week"]),
        ]
        ordering = ["day_of_week", "start_time"]

    def __str__(self):
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return f"{self.user.email} - {days[self.day_of_week]} {self.start_time}-{self.end_time}"


class MeetingEvent(models.Model):
    class Action(models.TextChoices):
        CREATED = "created", "Created"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"
        RESCHEDULED = "rescheduled", "Rescheduled"
        COMPLETED = "completed", "Completed"
        PARTICIPANT_JOINED = "participant_joined", "Participant Joined"
        PARTICIPANT_LEFT = "participant_left", "Participant Left"
        NOTE_ADDED = "note_added", "Note Added"

    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name="events",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="meeting_events",
    )
    action = models.CharField(max_length=25, choices=Action.choices)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "meetings_event"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["meeting", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.action} by {self.actor.email if self.actor else 'system'}"
