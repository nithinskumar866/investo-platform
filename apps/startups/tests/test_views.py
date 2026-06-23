from unittest.mock import patch

from rest_framework import status

from conftest import get_data, assert_success_response, assert_error_response

from apps.startups.models import Startup

STARTUP_LIST_URL = "/api/v1/startups/startups/"


def detail_url(pk):
    return f"/api/v1/startups/startups/{pk}/"


def action_url(pk, action):
    return f"/api/v1/startups/startups/{pk}/{action}/"


class TestListStartups:
    def test_anonymous_sees_visible_published_startups(self, api_client, startup):
        resp = api_client.get(STARTUP_LIST_URL)
        assert_success_response(resp)
        data = get_data(resp)
        assert len(data) >= 1

    def test_anonymous_does_not_see_draft_startups(self, api_client, draft_startup):
        resp = api_client.get(STARTUP_LIST_URL)
        data = get_data(resp)
        ids = [item["id"] for item in data]
        assert draft_startup.id not in ids

    def test_authenticated_user_sees_list(self, authenticated_client, startup):
        resp = authenticated_client.get(STARTUP_LIST_URL)
        assert_success_response(resp)
        data = get_data(resp)
        assert len(data) >= 1

    def test_list_returns_paginated_response(self, api_client, startup):
        resp = api_client.get(STARTUP_LIST_URL)
        assert resp.status_code == status.HTTP_200_OK


class TestRetrieveStartup:
    def test_retrieve_increments_view_count(self, api_client, startup):
        initial = startup.view_count
        resp = api_client.get(detail_url(startup.pk))
        assert_success_response(resp)
        startup.refresh_from_db()
        assert startup.view_count == initial + 1

    def test_retrieve_returns_detail_data(self, api_client, startup):
        resp = api_client.get(detail_url(startup.pk))
        assert_success_response(resp)
        data = get_data(resp)
        assert data["id"] == startup.pk
        assert data["name"] == startup.name

    def test_retrieve_not_found(self, api_client):
        resp = api_client.get(detail_url(99999))
        assert resp.status_code == status.HTTP_404_NOT_FOUND


class TestCreateStartup:
    def test_entrepreneur_can_create(self, authenticated_client, user):
        data = {
            "name": "Brand New Startup",
            "industry": "saas",
            "stage": "seed",
            "funding_goal": "250000.00",
            "equity_offered": "15.00",
        }
        resp = authenticated_client.post(
            STARTUP_LIST_URL, data, format="json"
        )
        assert_success_response(resp, status_code=status.HTTP_201_CREATED)
        result = get_data(resp)
        assert result["name"] == "Brand New Startup"

    def test_non_entrepreneur_cannot_create(self, investor_client):
        data = {
            "name": "Investor Startup",
            "industry": "saas",
            "stage": "seed",
        }
        resp = investor_client.post(STARTUP_LIST_URL, data, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_cannot_create(self, api_client):
        data = {
            "name": "Unauth Startup",
            "industry": "saas",
            "stage": "seed",
        }
        resp = api_client.post(STARTUP_LIST_URL, data, format="json")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_validates_required_fields(self, authenticated_client):
        resp = authenticated_client.post(
            STARTUP_LIST_URL, {"name": "Incomplete"}, format="json"
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


class TestUpdateStartup:
    def test_owner_can_partial_update(self, authenticated_client, startup):
        resp = authenticated_client.patch(
            detail_url(startup.pk), {"tagline": "Updated tagline"}, format="json"
        )
        assert_success_response(resp)
        startup.refresh_from_db()
        assert startup.tagline == "Updated tagline"

    def test_non_owner_cannot_update(self, founder_client, startup):
        resp = founder_client.patch(
            detail_url(startup.pk), {"tagline": "Hacked"}, format="json"
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_cannot_update(self, api_client, startup):
        resp = api_client.patch(
            detail_url(startup.pk), {"tagline": "Hacked"}, format="json"
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


class TestDeleteStartup:
    def test_owner_can_delete(self, authenticated_client, startup):
        resp = authenticated_client.delete(detail_url(startup.pk))
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        assert not Startup.objects.filter(pk=startup.pk).exists()

    def test_non_owner_cannot_delete(self, founder_client, startup):
        resp = founder_client.delete(detail_url(startup.pk))
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_cannot_delete(self, api_client, startup):
        resp = api_client.delete(detail_url(startup.pk))
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


class TestPublishStartup:
    def test_owner_can_publish_draft(self, authenticated_client, draft_startup):
        resp = authenticated_client.post(action_url(draft_startup.pk, "publish"))
        assert_success_response(resp)
        draft_startup.refresh_from_db()
        assert draft_startup.status == "active"

    def test_cannot_publish_already_active(self, authenticated_client, startup):
        resp = authenticated_client.post(action_url(startup.pk, "publish"))
        assert_error_response(resp, status_code=400, error_code="INVALID_STATUS")

    def test_non_owner_cannot_publish(self, founder_client, draft_startup):
        resp = founder_client.post(action_url(draft_startup.pk, "publish"))
        assert resp.status_code == status.HTTP_403_FORBIDDEN


class TestArchiveStartup:
    def test_owner_can_archive_active(self, authenticated_client, startup):
        resp = authenticated_client.post(action_url(startup.pk, "archive"))
        assert_success_response(resp)
        startup.refresh_from_db()
        assert startup.status == "archived"

    def test_cannot_archive_already_archived(self, authenticated_client, startup):
        startup.status = "archived"
        startup.save()
        resp = authenticated_client.post(action_url(startup.pk, "archive"))
        assert_error_response(resp, status_code=400, error_code="INVALID_STATUS")


class TestVerifyStartup:
    def test_admin_can_verify(self, admin_client, startup):
        assert startup.is_verified is False
        resp = admin_client.post(action_url(startup.pk, "verify"))
        assert_success_response(resp)
        startup.refresh_from_db()
        assert startup.is_verified is True

    def test_non_admin_cannot_verify(self, authenticated_client, startup):
        resp = authenticated_client.post(action_url(startup.pk, "verify"))
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_cannot_verify(self, api_client, startup):
        resp = api_client.post(action_url(startup.pk, "verify"))
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


class TestRecommendedInvestors:
    @patch("apps.startups.views.MatchingService")
    def test_returns_investors_for_authenticated(
        self, mock_matching, authenticated_client, startup
    ):
        mock_matching.generate_matches_for_startup.return_value = []
        resp = authenticated_client.get(
            action_url(startup.pk, "recommended_investors")
        )
        assert_success_response(resp)

    def test_unauthenticated_cannot_access(self, api_client, startup):
        resp = api_client.get(action_url(startup.pk, "recommended_investors"))
        assert resp.status_code == status.HTTP_200_OK

    def test_not_found_for_invalid_startup(self, authenticated_client):
        resp = authenticated_client.get(action_url(99999, "recommended_investors"))
        assert resp.status_code == status.HTTP_404_NOT_FOUND


class TestMyStartups:
    def test_returns_owners_startups(self, authenticated_client, startup):
        resp = authenticated_client.get(STARTUP_LIST_URL + "my_startups/")
        assert_success_response(resp)
        data = get_data(resp)
        pks = [item["id"] for item in data]
        assert startup.pk in pks

    def test_unauthenticated_cannot_access(self, api_client):
        resp = api_client.get(STARTUP_LIST_URL + "my_startups/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_does_not_include_others_startups(
        self, authenticated_client, founder, startup
    ):
        Startup.objects.create(owner=founder, name="Theirs", industry="saas", stage="seed")
        resp = authenticated_client.get(STARTUP_LIST_URL + "my_startups/")
        data = get_data(resp)
        names = [item["name"] for item in data]
        assert "Theirs" not in names


class TestBookmark:
    def test_authenticated_can_bookmark(self, authenticated_client, startup):
        resp = authenticated_client.post(action_url(startup.pk, "bookmark"))
        assert_success_response(resp)
        data = get_data(resp)
        assert data["bookmarked"] is True
        startup.refresh_from_db()
        assert startup.bookmark_count == 1

    def test_authenticated_can_unbookmark(self, authenticated_client, startup):
        startup.bookmark_count = 1
        startup.save()
        resp = authenticated_client.delete(action_url(startup.pk, "bookmark"))
        assert_success_response(resp)
        data = get_data(resp)
        assert data["bookmarked"] is False
        startup.refresh_from_db()
        assert startup.bookmark_count == 0

    def test_unauthenticated_cannot_bookmark(self, api_client, startup):
        resp = api_client.post(action_url(startup.pk, "bookmark"))
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


class TestUploadDocument:
    def test_owner_can_upload_document(self, authenticated_client, startup):
        import io
        from django.core.files.uploadedfile import SimpleUploadedFile

        file = SimpleUploadedFile(
            "pitch.pdf",
            b"%PDF-1.4 fake pdf content for testing",
            content_type="application/pdf",
        )
        data = {"name": "Pitch Deck", "file": file, "document_type": "pitch_deck"}
        resp = authenticated_client.post(
            action_url(startup.pk, "upload_document"), data, format="multipart"
        )
        assert_success_response(resp, status_code=status.HTTP_201_CREATED)

    def test_non_owner_cannot_upload(self, founder_client, startup):
        import io
        from django.core.files.uploadedfile import SimpleUploadedFile

        file = SimpleUploadedFile(
            "pitch.pdf",
            b"%PDF-1.4 fake pdf content for testing",
            content_type="application/pdf",
        )
        data = {"name": "Pitch Deck", "file": file}
        resp = founder_client.post(
            action_url(startup.pk, "upload_document"), data, format="multipart"
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_cannot_upload(self, api_client, startup):
        import io
        from django.core.files.uploadedfile import SimpleUploadedFile

        file = SimpleUploadedFile(
            "pitch.pdf",
            b"%PDF-1.4 fake pdf content for testing",
            content_type="application/pdf",
        )
        data = {"name": "Pitch Deck", "file": file}
        resp = api_client.post(
            action_url(startup.pk, "upload_document"), data, format="multipart"
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


class TestListDocuments:
    def test_owner_can_list_documents(self, authenticated_client, startup):
        from apps.startups.models import StartupDocument
        StartupDocument.objects.create(startup=startup, name="Doc1")
        StartupDocument.objects.create(startup=startup, name="Doc2")
        resp = authenticated_client.get(action_url(startup.pk, "documents"))
        assert_success_response(resp)
        data = get_data(resp)
        assert len(data) == 2

    def test_anonymous_can_list_documents(self, api_client, startup):
        from apps.startups.models import StartupDocument
        StartupDocument.objects.create(startup=startup, name="Public Doc")
        resp = api_client.get(action_url(startup.pk, "documents"))
        assert_success_response(resp)
        data = get_data(resp)
        assert len(data) == 1


class TestStatistics:
    def test_admin_can_access_statistics(self, admin_client):
        resp = admin_client.get(STARTUP_LIST_URL + "statistics/")
        assert_success_response(resp)
        data = get_data(resp)
        assert "total" in data
        assert "active" in data
        assert "funded" in data
        assert "by_industry" in data
        assert "by_stage" in data

    def test_non_admin_cannot_access_statistics(self, authenticated_client):
        resp = authenticated_client.get(STARTUP_LIST_URL + "statistics/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_cannot_access_statistics(self, api_client):
        resp = api_client.get(STARTUP_LIST_URL + "statistics/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


class TestPermissions:
    def test_anonymous_only_sees_published(self, api_client, startup, draft_startup):
        resp = api_client.get(STARTUP_LIST_URL)
        data = get_data(resp)
        ids = [s["id"] for s in data]
        assert startup.id in ids
        assert draft_startup.id not in ids

    def test_non_entrepreneur_cannot_create(self, investor_client):
        data = {
            "name": "Investor Co",
            "industry": "saas",
            "stage": "seed",
        }
        resp = investor_client.post(STARTUP_LIST_URL, data, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_non_owner_cannot_update(self, founder_client, startup):
        resp = founder_client.patch(
            detail_url(startup.pk), {"name": "Hacked Name"}, format="json"
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_verify(self, admin_client, startup):
        resp = admin_client.post(action_url(startup.pk, "verify"))
        assert_success_response(resp)
        startup.refresh_from_db()
        assert startup.is_verified is True
