from celery import shared_task
import logging
from .services import AuthService

logger = logging.getLogger(__name__)


@shared_task
def send_verification_email_task(user_id: int):
    """
    Async task to send verification email.

    Why Celery instead of sync:
    Sending email requires an SMTP connection which can take seconds.
    Doing this synchronously in the registration view would make the
    API response slow. Celery runs this in the background, and the
    user gets an immediate 201 response.

    Why user_id instead of serializing the user object:
    Celery serializes task arguments via JSON. User objects are not
    JSON-serializable. Passing the ID lets the task fetch the user
    from the database, ensuring it always has fresh data.
    """
    from django.contrib.auth import get_user_model
    from .services import AuthService

    User = get_user_model()
    user = User.objects.filter(id=user_id).first()
    if user:
        AuthService.send_verification_email(user)
        logger.info(f"Verification email task completed for user {user_id}")
    else:
        logger.warning(f"Verification email task failed: user {user_id} not found")


@shared_task
def send_password_reset_task(email: str):
    """
    Async task to send password reset email.
    """
    from .services import AuthService

    AuthService.send_password_reset_otp(email)
    logger.info(f"Password reset email task completed for {email}")
