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


@receiver(post_save, sender=InvestorProfile)
def sync_investor_preference(sender, instance, **kwargs):
    from apps.matching.models import InvestorPreference
    pref, _ = InvestorPreference.objects.get_or_create(user=instance.user)
    pref.preferred_industries = instance.preferred_industries
    pref.preferred_stages = instance.preferred_stages
    pref.is_active = True
    pref.save()
