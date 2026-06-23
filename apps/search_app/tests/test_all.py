import pytest
from unittest.mock import Mock, patch, PropertyMock

from apps.accounts.models import User
from apps.search_app.models import SavedSearch, SearchHistory, SearchClickEvent
from apps.search_app.services import SearchService
from apps.common.exceptions import ApplicationError


# ── User fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="user@example.com", password="testpass123", role="entrepreneur",
    )


@pytest.fixture
def founder(db):
    return User.objects.create_user(
        email="founder@example.com", password="testpass123", role="entrepreneur",
    )


@pytest.fixture
def investor(db):
    return User.objects.create_user(
        email="investor@example.com", password="testpass123", role="investor",
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email="admin@example.com", password="testpass123",
    )


@pytest.fixture
def saved_search(db, user):
    return SavedSearch.objects.create(
        user=user,
        name="AI Startups",
        search_type="startups",
        filters={"industry": "ai_ml", "stage": "seed"},
    )


@pytest.fixture
def search_history(db, user):
    return SearchHistory.objects.create(
        user=user,
        query="machine learning",
        search_type="startups",
        filters={},
        results_count=42,
    )


@pytest.fixture
def click_event(db, user):
    return SearchClickEvent.objects.create(
        user=user,
        result_type="startup",
        result_id=1,
        query="ai startup",
    )


# ── Model tests ──────────────────────────────────────────────────────────

class TestSavedSearchModel:
    def test_create_saved_search(self, saved_search):
        assert saved_search.pk is not None
        assert saved_search.name == "AI Startups"
        assert str(saved_search) == "AI Startups (startups)"

    def test_search_type_choices(self):
        assert SavedSearch.SearchType.STARTUPS == "startups"
        assert SavedSearch.SearchType.INVESTORS == "investors"


class TestSearchHistoryModel:
    def test_create_history(self, search_history):
        assert search_history.pk is not None
        assert search_history.query == "machine learning"
        assert str(search_history).startswith("user@example.com searched")

    def test_history_ordering(self, user):
        h1 = SearchHistory.objects.create(
            user=user, query="first", search_type="startups", results_count=1,
        )
        h2 = SearchHistory.objects.create(
            user=user, query="second", search_type="startups", results_count=2,
        )
        qs = SearchHistory.objects.all()
        assert qs.first() == h2


class TestSearchClickEventModel:
    def test_create_click(self, click_event):
        assert click_event.pk is not None
        assert click_event.result_type == "startup"
        assert str(click_event).startswith("user@example.com clicked")


# ── Service tests ────────────────────────────────────────────────────────

class TestSearchService:
    def test_search_invalid_domain(self, user):
        with pytest.raises(ApplicationError, match="Invalid search domain"):
            SearchService.search("invalid", user, "query")

    def test_search_startups(self, user):
        with patch(
            "apps.search_app.services.SearchRepository.search_startups",
            return_value=[{"id": 1, "name": "Test Startup"}],
        ):
            with patch(
                "apps.search_app.services.SearchRepository.record_history",
                return_value=None,
            ):
                results = SearchService.search("startups", user, "test")
        assert len(results) == 1

    def test_search_investors(self, user):
        with patch(
            "apps.search_app.services.SearchRepository.search_investors",
            return_value=[],
        ):
            with patch(
                "apps.search_app.services.SearchRepository.record_history",
                return_value=None,
            ):
                results = SearchService.search("investors", user, "test")
        assert results == []

    def test_search_founders(self, user):
        with patch(
            "apps.search_app.services.SearchRepository.search_founders",
            return_value=[],
        ):
            with patch(
                "apps.search_app.services.SearchRepository.record_history",
                return_value=None,
            ):
                results = SearchService.search("founders", user, "test")
        assert results == []

    def test_search_opportunities(self, user):
        with patch(
            "apps.search_app.services.SearchRepository.search_opportunities",
            return_value=[],
        ):
            with patch(
                "apps.search_app.services.SearchRepository.record_history",
                return_value=None,
            ):
                results = SearchService.search("opportunities", user, "test")
        assert results == []

    def test_autocomplete_short_query(self):
        results = SearchService.autocomplete("")
        assert results == []

    def test_autocomplete(self):
        with patch(
            "apps.search_app.services.SearchRepository.autocomplete",
            return_value=[],
        ):
            results = SearchService.autocomplete("ai", "startups", 5)
        assert results == []

    def test_recommend(self, user):
        with patch.multiple(
            "apps.search_app.services.SearchRepository",
            recommend_startups=Mock(return_value=[]),
            recommend_investors=Mock(return_value=[]),
            trending_startups=Mock(return_value=[]),
            recently_funded=Mock(return_value=[]),
        ):
            data = SearchService.recommend(user)
        assert "startups" in data
        assert "investors" in data
        assert "trending_startups" in data
        assert "recently_funded" in data

    def test_save(self, user):
        with patch(
            "apps.search_app.services.SearchRepository.save_search",
            return_value=Mock(id=1, name="Saved", search_type="startups"),
        ):
            saved = SearchService.save(user, "My Search", "startups", {"industry": "fintech"})
        assert saved is not None

    def test_save_missing_name(self, user):
        with pytest.raises(ApplicationError, match="Name is required"):
            SearchService.save(user, "", "startups", {})

    def test_save_invalid_type(self, user):
        with pytest.raises(ApplicationError, match="Invalid search type"):
            SearchService.save(user, "Test", "invalid", {})

    def test_get_saved(self, saved_search, user):
        results = SearchService.get_saved(user)
        assert saved_search in results

    def test_get_saved_filtered(self, saved_search, user):
        results = SearchService.get_saved(user, search_type="startups")
        assert saved_search in results
        results = SearchService.get_saved(user, search_type="investors")
        assert saved_search not in results

    def test_delete_saved(self, saved_search, user):
        result = SearchService.delete_saved(saved_search.id, user)
        assert result is True
        assert SavedSearch.objects.filter(id=saved_search.id).count() == 0

    def test_delete_saved_not_found(self, user):
        result = SearchService.delete_saved(9999, user)
        assert result is False

    def test_get_history(self, search_history, user):
        history = SearchService.get_history(user, limit=10)
        assert search_history in history

    def test_get_analytics(self):
        with patch(
            "apps.search_app.services.SearchRepository.get_analytics",
            return_value={"total_searches": 100, "total_clicks": 50, "ctr": 0.5},
        ):
            analytics = SearchService.get_analytics()
        assert analytics["total_searches"] == 100

    def test_record_click(self, user):
        with patch(
            "apps.search_app.services.SearchRepository.record_click",
            return_value=None,
        ):
            SearchService.record_click(user, "startup", 1, "query")


# ── View tests ──────────────────────────────────────────────────────────

class TestSearchViewSet:
    def test_search_startups(self, authenticated_client):
        with patch(
            "apps.search_app.services.SearchRepository.search_startups",
            return_value=[],
        ):
            with patch(
                "apps.search_app.services.SearchRepository.record_history",
                return_value=None,
            ):
                resp = authenticated_client.get(
                    "/api/v1/search/startups/?q=ai",
                )
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data

    def test_search_investors(self, authenticated_client):
        with patch(
            "apps.search_app.services.SearchRepository.search_investors",
            return_value=[],
        ):
            with patch(
                "apps.search_app.services.SearchRepository.record_history",
                return_value=None,
            ):
                resp = authenticated_client.get(
                    "/api/v1/search/investors/?q=investor",
                )
        assert resp.status_code == 200

    def test_search_founders(self, authenticated_client):
        with patch(
            "apps.search_app.services.SearchRepository.search_founders",
            return_value=[],
        ):
            with patch(
                "apps.search_app.services.SearchRepository.record_history",
                return_value=None,
            ):
                resp = authenticated_client.get(
                    "/api/v1/search/founders/?q=founder",
                )
        assert resp.status_code == 200

    def test_search_opportunities(self, authenticated_client):
        with patch(
            "apps.search_app.services.SearchRepository.search_opportunities",
            return_value=[],
        ):
            with patch(
                "apps.search_app.services.SearchRepository.record_history",
                return_value=None,
            ):
                resp = authenticated_client.get(
                    "/api/v1/search/opportunities/?q=deal",
                )
        assert resp.status_code == 200

    def test_search_with_filters(self, authenticated_client):
        with patch(
            "apps.search_app.services.SearchRepository.search_startups",
            return_value=[],
        ):
            with patch(
                "apps.search_app.services.SearchRepository.record_history",
                return_value=None,
            ):
                resp = authenticated_client.get(
                    "/api/v1/search/startups/?q=ai&industry=ai_ml&stage=seed",
                )
        assert resp.status_code == 200

    def test_autocomplete(self, authenticated_client):
        with patch(
            "apps.search_app.services.SearchRepository.autocomplete",
            return_value=[],
        ):
            resp = authenticated_client.get(
                "/api/v1/search/autocomplete/?q=ai&domain=startups",
            )
        assert resp.status_code == 200

    def test_recommended(self, authenticated_client):
        with patch.multiple(
            "apps.search_app.services.SearchRepository",
            recommend_startups=Mock(return_value=[]),
            recommend_investors=Mock(return_value=[]),
            trending_startups=Mock(return_value=[]),
            recently_funded=Mock(return_value=[]),
        ):
            resp = authenticated_client.get("/api/v1/search/recommended/")
        assert resp.status_code == 200

    def test_save(self, authenticated_client):
        with patch(
            "apps.search_app.services.SearchRepository.save_search",
            return_value=Mock(id=1, name="Saved", search_type="startups", filters={}),
        ):
            resp = authenticated_client.post(
                "/api/v1/search/save/",
                {"name": "My Search", "search_type": "startups", "filters": {"industry": "ai_ml"}},
                format="json",
            )
        assert resp.status_code == 201

    def test_saved_list(self, authenticated_client, saved_search):
        resp = authenticated_client.get("/api/v1/search/saved/")
        assert resp.status_code == 200

    def test_saved_list_filtered(self, authenticated_client, saved_search):
        resp = authenticated_client.get("/api/v1/search/saved/?type=startups")
        assert resp.status_code == 200

    def test_delete_saved(self, authenticated_client, saved_search):
        resp = authenticated_client.delete(
            f"/api/v1/search/{saved_search.id}/saved/",
        )
        assert resp.status_code == 204

    def test_history(self, authenticated_client, search_history):
        resp = authenticated_client.get("/api/v1/search/history/")
        assert resp.status_code == 200

    def test_analytics(self, authenticated_client):
        with patch(
            "apps.search_app.services.SearchRepository.get_analytics",
            return_value={"total_searches": 100, "total_clicks": 50, "ctr": 0.5},
        ):
            resp = authenticated_client.get("/api/v1/search/analytics/")
        assert resp.status_code == 200

    def test_search_requires_auth(self, api_client):
        resp = api_client.get("/api/v1/search/startups/?q=ai")
        assert resp.status_code == 401
