import logging
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


class EmailService:
    TEMPLATE_PREFIX = "emails/"

    @classmethod
    def _send(cls, subject, recipient, template, context, from_email=None):
        from_email = from_email or settings.DEFAULT_FROM_EMAIL
        html_message = render_to_string(f"{cls.TEMPLATE_PREFIX}{template}", context)
        plain_message = strip_tags(html_message)

        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=from_email,
                recipient_list=[recipient],
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"Email sent: {subject} to {recipient}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {recipient}: {e}")
            return False

    @classmethod
    def send_verification(cls, recipient_email, recipient_name, otp):
        return cls._send(
            subject="Verify your Investo account",
            recipient=recipient_email,
            template="verify_email.html",
            context={"name": recipient_name, "otp": otp},
        )

    @classmethod
    def send_password_reset(cls, recipient_email, otp):
        return cls._send(
            subject="Reset your Investo password",
            recipient=recipient_email,
            template="password_reset.html",
            context={"otp": otp},
        )

    @classmethod
    def send_welcome(cls, recipient_email, recipient_name, dashboard_url):
        return cls._send(
            subject="Welcome to Investo!",
            recipient=recipient_email,
            template="welcome.html",
            context={"name": recipient_name, "dashboard_url": dashboard_url},
        )

    @classmethod
    def send_match_notification(cls, recipient_email, recipient_name, match_type, context):
        return cls._send(
            subject="New Match on Investo",
            recipient=recipient_email,
            template="new_match.html",
            context={"name": recipient_name, "match_type": match_type, **context},
        )

    @classmethod
    def send_meeting_reminder(cls, recipient_email, recipient_name, meeting_context):
        return cls._send(
            subject="Meeting Reminder",
            recipient=recipient_email,
            template="meeting_reminder.html",
            context={"name": recipient_name, **meeting_context},
        )

    @classmethod
    def send_generic(cls, subject, recipient_email, template, context):
        return cls._send(subject=subject, recipient=recipient_email, template=template, context=context)
