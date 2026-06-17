from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
import logging

from .models import EntrepreneurProfile, InvestorProfile

logger = logging.getLogger(__name__)

User = get_user_model()


@receiver(post_save, sender=User)
def handle_new_user(sender, instance, created, **kwargs):
    """
    Auto-create profile based on user role on registration.
    """
    if created:
        if instance.role == User.Role.ENTREPRENEUR:
            EntrepreneurProfile.objects.create(user=instance)
            logger.info(f"Entrepreneur profile created for {instance.email}")
        elif instance.role == User.Role.INVESTOR:
            InvestorProfile.objects.create(user=instance)
            logger.info(f"Investor profile created for {instance.email}")

        logger.info(f"New {instance.role} user created: {instance.email}")
