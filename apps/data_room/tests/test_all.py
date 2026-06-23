import pytest
import io
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from unittest.mock import patch

from apps.accounts.models import User
from apps.startups.models import Startup
from apps.data_room.models import DataRoom, DataRoomDocument, DocumentAccess, DocumentViewEvent
from apps.data_room.services import DataRoomService, MAX_FILE_SIZE
from apps.common.exceptions import ApplicationError


# ── User fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="user@example.com", password="testpass123", role="entrepreneur",
    )


@pytest.fixture
def founder(db):
    u = User.objects.create_user(
        email="founder@example.com", password="testpass123", role="entrepreneur",
    )
    Startup.objects.create(
        owner=u, name="Founder Startup", slug="founder-startup",
        industry="ai_ml", stage="seed", business_model="b2b",
        status=Startup.Status.ACTIVE,
    )
    return u


@pytest.fixture
def investor(db):
    return User.objects.create_user(
        email="investor@example.com", password="testpass123", role="investor",
    )


@pytest.fixture
def investor2(db):
    return User.objects.create_user(
        email="investor2@example.com", password="testpass123", role="investor",
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email="admin@example.com", password="testpass123",
    )


@pytest.fixture
def startup(db, founder):
    return Startup.objects.filter(owner=founder).first()


@pytest.fixture
def data_room(db, startup, founder):
    return DataRoom.objects.create(
        startup=startup,
        title="Test Data Room",
        description="A test data room",
        visibility=DataRoom.Visibility.MATCHED_INVESTORS,
        created_by=founder,
    )


@pytest.fixture
def document(db, data_room, founder):
    return DataRoomDocument.objects.create(
        data_room=data_room,
        file=SimpleUploadedFile("test.pdf", b"%PDF-1.4 test content"),
        title="Test Document",
        document_type=DataRoomDocument.DocumentType.PITCH_DECK,
        uploaded_by=founder,
        file_size=1024,
        mime_type="application/pdf",
    )


@pytest.fixture
def document_access(db, document, investor, founder):
    return DocumentAccess.objects.create(
        document=document,
        investor=investor,
        granted_by=founder,
    )


# ── Model tests ──────────────────────────────────────────────────────────

class TestDataRoomModel:
    def test_create_data_room(self, data_room):
        assert data_room.pk is not None
        assert str(data_room) == "Test Data Room (Founder Startup)"

    def test_visibility_choices(self):
        assert DataRoom.Visibility.PRIVATE == "private"
        assert DataRoom.Visibility.MATCHED_INVESTORS == "matched_investors"
        assert DataRoom.Visibility.SELECTED_INVESTORS == "selected_investors"


class TestDataRoomDocumentModel:
    def test_create_document(self, document):
        assert document.pk is not None
        assert str(document) == "Test Document v1 (pitch_deck)"

    def test_document_type_choices(self):
        assert DataRoomDocument.DocumentType.PITCH_DECK == "pitch_deck"
        assert DataRoomDocument.DocumentType.FINANCIALS == "financials"


class TestDocumentAccessModel:
    def test_create_access(self, document_access):
        assert document_access.pk is not None
        assert document_access.investor.email in str(document_access)


class TestDocumentViewEventModel:
    def test_create_view_event(self, document, investor):
        event = DocumentViewEvent.objects.create(
            document=document,
            investor=investor,
            duration_seconds=120,
        )
        assert event.pk is not None
        assert event.duration_seconds == 120


# ── Service tests ────────────────────────────────────────────────────────

class TestDataRoomService:
    def test_create_room(self, startup, founder):
        room = DataRoomService.create_room(
            startup, founder,
            {"title": "New Room", "description": "Desc", "visibility": "private"},
        )
        assert room.title == "New Room"
        assert room.startup == startup

    def test_get_room_not_found(self, founder):
        with pytest.raises(ApplicationError, match="not found"):
            DataRoomService.get_room(9999, founder)

    def test_list_rooms(self, startup, founder, data_room):
        rooms = DataRoomService.list_rooms(startup, founder)
        assert data_room in rooms

    def test_list_rooms_forbidden(self, startup, investor):
        with pytest.raises(ApplicationError, match="startup owner"):
            DataRoomService.list_rooms(startup, investor)

    def test_update_room(self, data_room, founder):
        updated = DataRoomService.update_room(
            data_room.id, founder,
            {"title": "Updated Room"},
        )
        assert updated.title == "Updated Room"

    def test_upload_document(self, data_room, founder):
        file = SimpleUploadedFile("doc.pdf", b"%PDF-1.4 test")
        with patch.multiple(
            "apps.data_room.services",
            NotificationService=lambda **kw: None,
            ActivityFeedService=lambda **kw: None,
        ):
            doc = DataRoomService.upload_document(
                data_room.id, founder,
                {"title": "New Doc", "document_type": "financials"},
                file,
            )
        assert doc.title == "New Doc"
        assert doc.document_type == "financials"

    def test_upload_document_invalid_extension(self, data_room, founder):
        file = SimpleUploadedFile("doc.exe", b"fake")
        with pytest.raises(ApplicationError, match="not allowed"):
            DataRoomService.upload_document(
                data_room.id, founder, {"title": "Bad"}, file,
            )

    def test_upload_document_too_large(self, data_room, founder):
        file = SimpleUploadedFile("doc.pdf", b"x" * (MAX_FILE_SIZE + 1))
        with pytest.raises(ApplicationError, match="exceeds"):
            DataRoomService.upload_document(
                data_room.id, founder, {"title": "Big"}, file,
            )

    def test_grant_document_access(self, document, founder, investor):
        access, created = DataRoomService.grant_document_access(
            document.id, founder, investor.id,
        )
        assert created

    def test_grant_document_access_duplicate(self, document_access, founder, investor):
        with patch("apps.data_room.services.NotificationService"):
            access, created = DataRoomService.grant_document_access(
                document_access.document_id, founder, investor.id,
            )
        assert not created

    def test_revoke_document_access(self, document_access, founder, investor):
        result = DataRoomService.revoke_document_access(
            document_access.document_id, founder, investor.id,
        )
        assert result is True

    def test_list_shared_documents(self, document_access, investor):
        docs = DataRoomService.list_shared_documents(investor)
        assert document_access.document in docs

    def test_get_document_for_investor(self, document_access, investor):
        doc = DataRoomService.get_document_for_investor(
            document_access.document_id, investor,
        )
        assert doc == document_access.document

    def test_get_document_for_investor_forbidden(self, document, investor):
        with pytest.raises(ApplicationError, match="do not have access"):
            DataRoomService.get_document_for_investor(document.id, investor)

    def test_record_document_view(self, document_access, investor):
        with patch("apps.data_room.services.NotificationService"):
            event = DataRoomService.record_document_view(
                document_access.document_id, investor, duration=60,
            )
        assert event is not None


# ── View tests ──────────────────────────────────────────────────────────

class TestDataRoomViewSet:
    def test_list_rooms(self, founder_client, data_room):
        resp = founder_client.get("/api/v1/data-room/rooms/")
        assert resp.status_code == 200

    def test_create_room(self, founder_client):
        resp = founder_client.post(
            "/api/v1/data-room/rooms/",
            {"title": "New Room", "description": "Desc", "visibility": "private"},
            format="json",
        )
        assert resp.status_code == 201

    def test_retrieve_room(self, founder_client, data_room):
        resp = founder_client.get(f"/api/v1/data-room/rooms/{data_room.id}/")
        assert resp.status_code == 200

    def test_update_room(self, founder_client, data_room):
        resp = founder_client.patch(
            f"/api/v1/data-room/rooms/{data_room.id}/",
            {"title": "Updated"},
            format="json",
        )
        assert resp.status_code == 200

    def test_destroy_room(self, founder_client, data_room):
        resp = founder_client.delete(
            f"/api/v1/data-room/rooms/{data_room.id}/",
        )
        assert resp.status_code == 204

    def test_upload_document(self, founder_client, data_room):
        with patch.multiple(
            "apps.data_room.services",
            NotificationService=lambda **kw: None,
            ActivityFeedService=lambda **kw: None,
        ):
            resp = founder_client.post(
                f"/api/v1/data-room/rooms/{data_room.id}/upload/",
                {"title": "Uploaded Doc", "document_type": "financials"},
                format="multipart",
            )
        assert resp.status_code == 201

    def test_analytics(self, founder_client):
        resp = founder_client.get("/api/v1/data-room/rooms/analytics/")
        assert resp.status_code == 200

    def test_permission_entrepreneur_only(self, investor_client):
        resp = investor_client.get("/api/v1/data-room/rooms/")
        assert resp.status_code == 403


class TestDataRoomDocumentViewSet:
    def test_list_documents(self, founder_client, document):
        resp = founder_client.get("/api/v1/data-room/documents/")
        assert resp.status_code == 200

    def test_retrieve_document(self, founder_client, document):
        resp = founder_client.get(
            f"/api/v1/data-room/documents/{document.id}/",
        )
        assert resp.status_code == 200

    def test_destroy_document(self, founder_client, document):
        resp = founder_client.delete(
            f"/api/v1/data-room/documents/{document.id}/",
        )
        assert resp.status_code == 204

    def test_grant_access(self, founder_client, document, investor):
        resp = founder_client.post(
            f"/api/v1/data-room/documents/{document.id}/grant/",
            {"investor_id": investor.id},
            format="json",
        )
        assert resp.status_code == 201

    def test_revoke_access(self, founder_client, document_access):
        resp = founder_client.post(
            f"/api/v1/data-room/documents/{document_access.document_id}/revoke/",
            {"investor_id": document_access.investor_id},
            format="json",
        )
        assert resp.status_code == 200

    def test_views(self, founder_client, document):
        resp = founder_client.get(
            f"/api/v1/data-room/documents/{document.id}/views/",
        )
        assert resp.status_code == 200

    def test_access_list(self, founder_client, document_access):
        resp = founder_client.get(
            f"/api/v1/data-room/documents/{document_access.document_id}/access_list/",
        )
        assert resp.status_code == 200


class TestInvestorDocumentViewSet:
    def test_list_documents(self, investor_client, document_access):
        resp = investor_client.get("/api/v1/data-room/investor/documents/")
        assert resp.status_code == 200

    def test_retrieve_document(self, investor_client, document_access):
        resp = investor_client.get(
            f"/api/v1/data-room/investor/documents/{document_access.document_id}/",
        )
        assert resp.status_code == 200

    def test_view_document(self, investor_client, document_access):
        resp = investor_client.post(
            f"/api/v1/data-room/investor/documents/{document_access.document_id}/view/",
            {"duration_seconds": 120},
            format="json",
        )
        assert resp.status_code == 200

    def test_permission_investor_only(self, founder_client):
        resp = founder_client.get("/api/v1/data-room/investor/documents/")
        assert resp.status_code == 403
