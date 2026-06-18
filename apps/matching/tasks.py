import logging

from celery import shared_task
from django.core.cache import cache

logger = logging.getLogger(__name__)

MATCH_CACHE_PREFIX = "matches:"
MATCH_CACHE_TTL = 300  # 5 minutes


@shared_task
def generate_investor_matches_task(investor_id: int, limit: int = 50):
    """
    Async task to generate/re-rank matches for an investor.
    Runs in the background and caches results in Redis.
    """
    from django.contrib.auth import get_user_model
    from .services import MatchingService

    User = get_user_model()
    investor = User.objects.filter(id=investor_id).first()
    if not investor:
        logger.warning(f"Investor {investor_id} not found for match generation")
        return

    matches = MatchingService.generate_matches_for_investor(investor, limit=limit)
    match_ids = [m.id for m in matches]

    cache_key = f"{MATCH_CACHE_PREFIX}investor:{investor_id}"
    cache.set(cache_key, match_ids, timeout=MATCH_CACHE_TTL)
    logger.info(f"Generated {len(match_ids)} matches for investor {investor_id}")
    return match_ids


@shared_task
def generate_startup_matches_task(startup_id: int, limit: int = 50):
    """
    Async task to generate/re-rank matches for a startup.
    """
    from apps.startups.models import Startup
    from .services import MatchingService

    startup = Startup.objects.filter(id=startup_id).first()
    if not startup:
        logger.warning(f"Startup {startup_id} not found for match generation")
        return

    matches = MatchingService.generate_matches_for_startup(startup, limit=limit)
    match_ids = [m.id for m in matches]

    cache_key = f"{MATCH_CACHE_PREFIX}startup:{startup_id}"
    cache.set(cache_key, match_ids, timeout=MATCH_CACHE_TTL)
    logger.info(f"Generated {len(match_ids)} matches for startup {startup_id}")
    return match_ids


@shared_task
def refresh_all_matches_task():
    """
    Periodic task to refresh all active investor matches.
    Scheduled via Celery Beat (e.g., every 6 hours).
    """
    from django.contrib.auth import get_user_model
    from .models import InvestorPreference

    User = get_user_model()
    active_prefs = InvestorPreference.objects.filter(
        is_active=True,
        user__is_active=True,
        user__role="investor",
    ).values_list("user_id", flat=True)

    for investor_id in active_prefs:
        generate_investor_matches_task.delay(investor_id)

    logger.info(f"Queued match refresh for {len(active_prefs)} investors")
