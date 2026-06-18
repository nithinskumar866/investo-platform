from django.contrib import admin

from .models import Meeting, MeetingParticipant, MeetingAvailability, MeetingEvent


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ["title", "organizer_email", "investor_email", "meeting_type", "status", "scheduled_start"]
    list_filter = ["status", "meeting_type", "scheduled_start"]
    search_fields = ["title", "organizer__email", "investor__email"]
    raw_id_fields = ["organizer", "investor", "startup"]
    readonly_fields = ["created_at", "updated_at"]

    def organizer_email(self, obj):
        return obj.organizer.email
    organizer_email.short_description = "Organizer"

    def investor_email(self, obj):
        return obj.investor.email
    investor_email.short_description = "Investor"


@admin.register(MeetingParticipant)
class MeetingParticipantAdmin(admin.ModelAdmin):
    list_display = ["user_email", "meeting", "attendance_status", "joined_at"]
    list_filter = ["attendance_status"]
    search_fields = ["user__email", "meeting__title"]
    raw_id_fields = ["meeting", "user"]

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "User"


@admin.register(MeetingAvailability)
class MeetingAvailabilityAdmin(admin.ModelAdmin):
    list_display = ["user_email", "day_of_week", "start_time", "end_time"]
    list_filter = ["day_of_week"]
    search_fields = ["user__email"]
    raw_id_fields = ["user"]

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "User"


@admin.register(MeetingEvent)
class MeetingEventAdmin(admin.ModelAdmin):
    list_display = ["meeting", "actor_email", "action", "created_at"]
    list_filter = ["action", "created_at"]
    search_fields = ["meeting__title", "actor__email"]
    raw_id_fields = ["meeting", "actor"]

    def actor_email(self, obj):
        return obj.actor.email if obj.actor else "system"
    actor_email.short_description = "Actor"
