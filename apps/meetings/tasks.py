import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def meeting_reminder_24h():
    """Send reminders for meetings starting in ~24 hours."""
    from django.contrib.auth import get_user_model
    from .models import Meeting
    from apps.notifications.services import NotificationService

    now = timezone.now()
    window_start = now + timezone.timedelta(hours=23)
    window_end = now + timezone.timedelta(hours=25)

    meetings = Meeting.objects.filter(
        scheduled_start__gte=window_start,
        scheduled_start__lte=window_end,
        status__in=[Meeting.Status.SCHEDULED, Meeting.Status.CONFIRMED],
    ).select_related("organizer", "investor")

    count = 0
    for meeting in meetings:
        for user in [meeting.organizer, meeting.investor]:
            NotificationService.notify(
                recipient=user,
                notification_type="system",
                title="Meeting Tomorrow",
                message=f"Reminder: '{meeting.title}' starts at {meeting.scheduled_start.strftime('%H:%M %Z')}",
                data={
                    "meeting_id": meeting.id,
                    "scheduled_start": meeting.scheduled_start.isoformat(),
                    "type": "reminder_24h",
                },
            )
            count += 1

    logger.info(f"Sent {count} 24h meeting reminders")
    return count


@shared_task
def meeting_reminder_1h():
    """Send reminders for meetings starting in ~1 hour."""
    from .models import Meeting
    from apps.notifications.services import NotificationService

    now = timezone.now()
    window_start = now + timezone.timedelta(minutes=55)
    window_end = now + timezone.timedelta(minutes=65)

    meetings = Meeting.objects.filter(
        scheduled_start__gte=window_start,
        scheduled_start__lte=window_end,
        status__in=[Meeting.Status.SCHEDULED, Meeting.Status.CONFIRMED],
    ).select_related("organizer", "investor")

    count = 0
    for meeting in meetings:
        for user in [meeting.organizer, meeting.investor]:
            NotificationService.notify(
                recipient=user,
                notification_type="system",
                title="Meeting in 1 Hour",
                message=f"'{meeting.title}' starts soon",
                data={
                    "meeting_id": meeting.id,
                    "scheduled_start": meeting.scheduled_start.isoformat(),
                    "type": "reminder_1h",
                },
            )
            count += 1

    logger.info(f"Sent {count} 1h meeting reminders")
    return count


@shared_task
def missed_meeting_followup():
    """Follow up on meetings that ended recently but weren't marked completed."""
    from .models import Meeting
    from apps.notifications.services import NotificationService

    now = timezone.now()
    window_start = now - timezone.timedelta(hours=3)
    window_end = now - timezone.timedelta(minutes=30)

    meetings = Meeting.objects.filter(
        scheduled_end__gte=window_start,
        scheduled_end__lte=window_end,
        status__in=[Meeting.Status.SCHEDULED, Meeting.Status.CONFIRMED],
    ).select_related("organizer", "investor")

    count = 0
    for meeting in meetings:
        for user in [meeting.organizer, meeting.investor]:
            NotificationService.notify(
                recipient=user,
                notification_type="system",
                title="Meeting Follow-Up",
                message=f"Did '{meeting.title}' happen? Mark it as completed or reschedule.",
                data={
                    "meeting_id": meeting.id,
                    "type": "missed_followup",
                },
            )
            count += 1

    logger.info(f"Sent {count} missed meeting follow-ups")
    return count


@shared_task
def daily_agenda_email():
    """Send daily agenda with today's meetings to users who have meetings."""
    from django.contrib.auth import get_user_model
    from .models import Meeting
    from apps.notifications.services import NotificationService

    now = timezone.now()
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timezone.timedelta(days=1)

    meetings = Meeting.objects.filter(
        scheduled_start__gte=day_start,
        scheduled_start__lte=day_end,
        status__in=[Meeting.Status.SCHEDULED, Meeting.Status.CONFIRMED],
    ).select_related("organizer", "investor")

    user_meetings = {}
    for meeting in meetings:
        for user in [meeting.organizer, meeting.investor]:
            user_meetings.setdefault(user.id, []).append(meeting)

    User = get_user_model()
    count = 0
    for user_id, user_meeting_list in user_meetings.items():
        try:
            user = User.objects.get(id=user_id)
            NotificationService.notify(
                recipient=user,
                notification_type="system",
                title="Today's Meeting Agenda",
                message=f"You have {len(user_meeting_list)} meeting(s) scheduled today",
                data={
                    "meeting_count": len(user_meeting_list),
                    "meetings": [
                        {
                            "id": m.id,
                            "title": m.title,
                            "start": m.scheduled_start.isoformat(),
                        }
                        for m in user_meeting_list
                    ],
                    "type": "daily_agenda",
                },
            )
            count += 1
        except Exception:
            continue

    logger.info(f"Sent {count} daily agenda notifications")
    return count
