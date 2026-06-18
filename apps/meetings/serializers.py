from rest_framework import serializers

from .models import Meeting, MeetingParticipant, MeetingAvailability, MeetingEvent


class MeetingParticipantSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    role = serializers.CharField(source="user.role", read_only=True)

    class Meta:
        model = MeetingParticipant
        fields = ["id", "user", "email", "role", "attendance_status", "joined_at"]
        read_only_fields = ["joined_at"]


class MeetingEventSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source="actor.email", read_only=True)

    class Meta:
        model = MeetingEvent
        fields = ["id", "actor", "actor_email", "action", "metadata", "created_at"]
        read_only_fields = ["actor", "created_at"]


class MeetingListSerializer(serializers.ModelSerializer):
    organizer_email = serializers.EmailField(source="organizer.email", read_only=True)
    investor_email = serializers.EmailField(source="investor.email", read_only=True)
    startup_name = serializers.CharField(source="startup.name", read_only=True, default=None)
    participant_count = serializers.SerializerMethodField()

    class Meta:
        model = Meeting
        fields = [
            "id", "title", "meeting_type", "status",
            "scheduled_start", "scheduled_end", "timezone",
            "organizer", "organizer_email",
            "investor", "investor_email",
            "startup", "startup_name",
            "meeting_link", "location",
            "participant_count", "created_at",
        ]

    def get_participant_count(self, obj):
        return getattr(obj, "_participant_count", None) or obj.participants.count()


class MeetingDetailSerializer(serializers.ModelSerializer):
    participants = MeetingParticipantSerializer(many=True, read_only=True)
    events = MeetingEventSerializer(many=True, read_only=True)
    organizer_email = serializers.EmailField(source="organizer.email", read_only=True)
    investor_email = serializers.EmailField(source="investor.email", read_only=True)
    startup_name = serializers.CharField(source="startup.name", read_only=True, default=None)

    class Meta:
        model = Meeting
        fields = [
            "id", "title", "description", "meeting_type", "status",
            "scheduled_start", "scheduled_end", "timezone",
            "organizer", "organizer_email",
            "investor", "investor_email",
            "startup", "startup_name",
            "meeting_link", "location", "notes",
            "participants", "events",
            "created_at", "updated_at",
        ]
        read_only_fields = ["organizer", "created_at", "updated_at"]


class CreateMeetingSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    meeting_type = serializers.ChoiceField(
        choices=Meeting.MeetingType.choices,
        default=Meeting.MeetingType.INTRO_CALL,
    )
    investor_id = serializers.IntegerField()
    startup = serializers.IntegerField(required=False, allow_null=True)
    scheduled_start = serializers.DateTimeField()
    scheduled_end = serializers.DateTimeField()
    timezone = serializers.CharField(max_length=50, default="UTC")
    location = serializers.CharField(required=False, allow_blank=True, default="")
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class UpdateMeetingSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    meeting_type = serializers.ChoiceField(
        choices=Meeting.MeetingType.choices, required=False,
    )
    scheduled_start = serializers.DateTimeField(required=False)
    scheduled_end = serializers.DateTimeField(required=False)
    timezone = serializers.CharField(max_length=50, required=False)
    meeting_link = serializers.URLField(required=False, allow_blank=True)
    location = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class RescheduleSerializer(serializers.Serializer):
    scheduled_start = serializers.DateTimeField()
    scheduled_end = serializers.DateTimeField()
    timezone = serializers.CharField(max_length=50, required=False)


class CancelSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_null=True)


class CompleteSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_null=True)


class AvailabilitySlotSerializer(serializers.Serializer):
    day_of_week = serializers.ChoiceField(choices=[0, 1, 2, 3, 4, 5, 6])
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    timezone = serializers.CharField(max_length=50, default="UTC")


class AvailabilitySerializer(serializers.ModelSerializer):
    day_name = serializers.SerializerMethodField()

    class Meta:
        model = MeetingAvailability
        fields = ["id", "day_of_week", "day_name", "start_time", "end_time", "timezone"]
        read_only_fields = ["id"]

    def get_day_name(self, obj):
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        return days[obj.day_of_week]


class CalendarMeetingSerializer(serializers.ModelSerializer):
    organizer_email = serializers.EmailField(source="organizer.email", read_only=True)
    startup_name = serializers.CharField(source="startup.name", read_only=True, default=None)

    class Meta:
        model = Meeting
        fields = [
            "id", "title", "meeting_type", "status",
            "scheduled_start", "scheduled_end", "timezone",
            "organizer_email", "startup_name",
        ]


class MeetingAnalyticsSerializer(serializers.Serializer):
    total_meetings = serializers.IntegerField()
    completed_meetings = serializers.IntegerField()
    cancelled_meetings = serializers.IntegerField()
    upcoming_meetings = serializers.IntegerField()
    completion_rate = serializers.FloatField()
