import logging

from apps.common.exceptions import ApplicationError

from .repositories import SearchRepository

logger = logging.getLogger(__name__)


class SearchService:
    """Business logic for search operations."""

    SEARCH_DOMAINS = ["startups", "investors", "founders", "opportunities"]

    @staticmethod
    def search(domain, user, query="", filters=None, sort="-relevance", limit=20):
        if domain not in SearchService.SEARCH_DOMAINS:
            raise ApplicationError(
                f"Invalid search domain: {domain}",
                "INVALID_DOMAIN", 400,
            )

        results = SearchService._execute_search(
            domain, query, filters, sort, limit,
        )

        SearchRepository.record_history(
            user, query, domain, filters, len(results),
        )

        return results

    @staticmethod
    def _execute_search(domain, query, filters, sort, limit):
        mapping = {
            "startups": SearchRepository.search_startups,
            "investors": SearchRepository.search_investors,
            "founders": SearchRepository.search_founders,
            "opportunities": SearchRepository.search_opportunities,
        }
        return mapping[domain](query, filters, sort, limit)

    @staticmethod
    def autocomplete(query, domain="startups", limit=10):
        if len(query) < 1:
            return []
        return SearchRepository.autocomplete(query, domain, limit)

    @staticmethod
    def recommend(user, limit=20):
        return {
            "startups": SearchRepository.recommend_startups(user, limit),
            "investors": SearchRepository.recommend_investors(user, limit),
            "trending_startups": SearchRepository.trending_startups(limit=10),
            "recently_funded": SearchRepository.recently_funded(limit=10),
        }

    @staticmethod
    def record_click(user, result_type, result_id, query=""):
        return SearchRepository.record_click(user, result_type, result_id, query)

    # ── Saved Searches ────────────────────────────────────────────

    @staticmethod
    def save(user, name, search_type, filters):
        if not name:
            raise ApplicationError("Name is required", "MISSING_NAME", 400)
        if search_type not in SearchService.SEARCH_DOMAINS:
            raise ApplicationError("Invalid search type", "INVALID_TYPE", 400)
        return SearchRepository.save_search(user, name, search_type, filters)

    @staticmethod
    def get_saved(user, search_type=None):
        return SearchRepository.get_saved_searches(user, search_type)

    @staticmethod
    def delete_saved(search_id, user):
        return SearchRepository.delete_saved_search(search_id, user)

    # ── History ───────────────────────────────────────────────────

    @staticmethod
    def get_history(user, limit=20):
        return SearchRepository.get_search_history(user, limit)

    # ── Analytics ─────────────────────────────────────────────────

    @staticmethod
    def get_analytics():
        return SearchRepository.get_analytics()
