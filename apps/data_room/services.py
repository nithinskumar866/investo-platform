import logging
import mimetypes

from django.db import transaction

from apps.common.exceptions import ApplicationError

from .models import DataRoom, DataRoomDocument
from .repositories import DataRoomRepository

logger = logging.getLogger(__name__)


# File signature (magic bytes) validation
FILE_SIGNATURES = {
    b"%PDF": "application/pdf",
    b"\xd0\xcf\x11\xe0": "application/msword",
    b"PK\x03\x04": "application/vnd.openxmlformats-officedocument",
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
    b"Rar!\x1a\x07": "application/vnd.rar",
    b"\x1f\x8b\x08": "application/gzip",
    b"\x42\x5a\x68": "application/x-bzip2",
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB for data room documents

ALLOWED_EXTENSIONS = {
    "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
    "txt", "csv", "md", "jpg", "jpeg", "png", "gif",
    "mp4", "mov", "avi", "key", "numbers", "pages",
}


def _check_file_signature(file_bytes: bytes) -> str | None:
    for signature, mime_type in FILE_SIGNATURES.items():
        if file_bytes.startswith(signature):
            return mime_type
    return None


class DataRoomService:
    """Business logic for data room operations."""

    @staticmethod
    def _validate_startup_owner(startup, user):
        if startup.owner_id != user.id:
            raise ApplicationError(
                "Only the startup owner can manage data rooms",
                "FORBIDDEN", 403,
            )

    @staticmethod
    def _validate_document_access(document, user):
        if not DataRoomRepository.has_access(document, user):
            raise ApplicationError(
                "You do not have access to this document",
                "FORBIDDEN", 403,
            )

    @staticmethod
    def _validate_file(file_obj):
        if file_obj.size > MAX_FILE_SIZE:
            raise ApplicationError(
                f"File size exceeds {MAX_FILE_SIZE // (1024*1024)}MB limit",
                "FILE_TOO_LARGE", 400,
            )
        ext = file_obj.name.lower().rsplit(".", 1)[-1] if "." in file_obj.name else ""
        if ext not in ALLOWED_EXTENSIONS:
            raise ApplicationError(
                f"File extension '.{ext}' is not allowed",
                "INVALID_EXTENSION", 400,
            )
        header = file_obj.read(32)
        file_obj.seek(0)
        detected = _check_file_signature(header)
        if detected is None and ext not in ("txt", "csv", "md", "key", "numbers", "pages"):
            raise ApplicationError(
                "File content does not match a recognized format",
                "INVALID_FILE", 400,
            )

    # ── Data Room CRUD ────────────────────────────────────────────

    @staticmethod
    def create_room(startup, user, data):
        DataRoomService._validate_startup_owner(startup, user)
        room = DataRoomRepository.create_room(startup, user, data)
        logger.info(f"Data room created: {room.title} for {startup.name}")
        return room

    @staticmethod
    def get_room(room_id, user):
        room = DataRoomRepository.get_room(room_id)
        if not room:
            raise ApplicationError("Data room not found", "NOT_FOUND", 404)
        return room

    @staticmethod
    def list_rooms(startup, user):
        DataRoomService._validate_startup_owner(startup, user)
        return DataRoomRepository.get_startup_rooms(startup)

    @staticmethod
    def update_room(room_id, user, data):
        room = DataRoomService.get_room(room_id, user)
        DataRoomService._validate_startup_owner(room.startup, user)
        return DataRoomRepository.update_room(room, data)

    # ── Document management ───────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def upload_document(room_id, user, data, file_obj):
        room = DataRoomService.get_room(room_id, user)
        DataRoomService._validate_startup_owner(room.startup, user)
        DataRoomService._validate_file(file_obj)

        doc = DataRoomRepository.create_document(room, user, data, file_obj)

        # Auto-grant access to matched investors based on room visibility
        if room.visibility == DataRoom.Visibility.MATCHED_INVESTORS:
            from apps.matching.models import MatchScore
            matched_investors = MatchScore.objects.filter(
                startup=room.startup,
                status__in=["recommended", "saved", "contacted"],
            ).values_list("investor", flat=True).distinct()

            for investor_id in matched_investors:
                from django.contrib.auth import get_user_model
                try:
                    investor = get_user_model().objects.get(id=investor_id)
                    DataRoomRepository.grant_access(doc, investor, user)
                except Exception:
                    continue

        from apps.notifications.services import NotificationService
        NotificationService.notify(
            recipient=room.startup.owner,
            notification_type="document_uploaded",
            title=f"Document Uploaded: {doc.title}",
            message=f"Version {doc.version} uploaded to {room.title}",
            actor=user,
            data={
                "document_id": doc.id,
                "room_id": room.id,
                "document_type": doc.document_type,
                "version": doc.version,
            },
        )

        from apps.activity_feed.services import ActivityFeedService
        ActivityFeedService.publish_activity(
            actor=user,
            activity_type="document_uploaded",
            title=f"{user.email} uploaded {doc.title} to {room.title}",
            startup=room.startup,
            target_object_id=doc.id,
            target_object_type="data_room_document",
            metadata={
                "document_type": doc.document_type,
                "version": doc.version,
                "room_id": room.id,
            },
        )

        logger.info(
            f"Document uploaded: {doc.title} v{doc.version} to room {room.title}",
        )
        return doc

    @staticmethod
    @transaction.atomic
    def upload_new_version(document_id, user, data, file_obj):
        document = DataRoomRepository.get_document(document_id)
        if not document:
            raise ApplicationError("Document not found", "NOT_FOUND", 404)
        DataRoomService._validate_startup_owner(document.data_room.startup, user)
        DataRoomService._validate_file(file_obj)

        doc = DataRoomRepository.create_new_version(document, data, file_obj, user)

        logger.info(
            f"Document updated: {doc.title} v{doc.version}",
        )
        return doc

    @staticmethod
    def update_document(document_id, user, data):
        document = DataRoomRepository.get_document(document_id)
        if not document:
            raise ApplicationError("Document not found", "NOT_FOUND", 404)
        DataRoomService._validate_startup_owner(document.data_room.startup, user)
        return DataRoomRepository.update_document(document, data)

    @staticmethod
    def delete_document(document_id, user):
        document = DataRoomRepository.get_document(document_id)
        if not document:
            raise ApplicationError("Document not found", "NOT_FOUND", 404)
        DataRoomService._validate_startup_owner(document.data_room.startup, user)
        DataRoomRepository.delete_document(document)

    # ── Access control ────────────────────────────────────────────

    @staticmethod
    def grant_document_access(document_id, user, investor_id):
        document = DataRoomRepository.get_document(document_id)
        if not document:
            raise ApplicationError("Document not found", "NOT_FOUND", 404)
        DataRoomService._validate_startup_owner(document.data_room.startup, user)

        from django.contrib.auth import get_user_model
        try:
            investor = get_user_model().objects.get(id=investor_id, role="investor")
        except Exception:
            raise ApplicationError("Investor not found", "NOT_FOUND", 404)

        access, created = DataRoomRepository.grant_access(document, investor, user)
        if created:
            from apps.notifications.services import NotificationService
            NotificationService.notify(
                recipient=investor,
                notification_type="access_granted",
                title="Document Access Granted",
                message=f"You can now view '{document.title}' from {document.data_room.startup.name}",
                actor=user,
                data={
                    "document_id": document.id,
                    "room_id": document.data_room_id,
                    "startup_name": document.data_room.startup.name,
                },
            )
            logger.info(
                f"Access granted: {investor.email} can view {document.title}",
            )
        return access, created

    @staticmethod
    def revoke_document_access(document_id, user, investor_id):
        document = DataRoomRepository.get_document(document_id)
        if not document:
            raise ApplicationError("Document not found", "NOT_FOUND", 404)
        DataRoomService._validate_startup_owner(document.data_room.startup, user)

        from django.contrib.auth import get_user_model
        try:
            investor = get_user_model().objects.get(id=investor_id)
        except Exception:
            raise ApplicationError("Investor not found", "NOT_FOUND", 404)

        DataRoomRepository.revoke_access(document, investor)
        logger.info(
            f"Access revoked: {investor.email} removed from {document.title}",
        )
        return True

    # ── Investor document access ──────────────────────────────────

    @staticmethod
    def list_shared_documents(investor):
        return DataRoomRepository.get_accessible_documents(investor)

    @staticmethod
    def get_document_for_investor(document_id, investor):
        document = DataRoomRepository.get_document(document_id)
        if not document:
            raise ApplicationError("Document not found", "NOT_FOUND", 404)
        DataRoomService._validate_document_access(document, investor)
        return document

    @staticmethod
    def record_document_view(document_id, investor, duration=None):
        document = DataRoomService.get_document_for_investor(document_id, investor)
        event = DataRoomRepository.record_view(document, investor, duration)

        from apps.notifications.services import NotificationService
        NotificationService.notify(
            recipient=document.data_room.startup.owner,
            notification_type="document_viewed",
            title=f"Document Viewed: {document.title}",
            message=f"{investor.email} viewed your document",
            actor=investor,
            data={
                "document_id": document.id,
                "investor_id": investor.id,
                "duration_seconds": duration,
            },
        )

        logger.info(
            f"Document viewed: {document.title} by {investor.email}",
        )
        return event

    # ── Analytics ─────────────────────────────────────────────────

    @staticmethod
    def get_startup_analytics(startup, user):
        DataRoomService._validate_startup_owner(startup, user)
        return DataRoomRepository.get_startup_analytics(startup)

    @staticmethod
    def get_investor_analytics(investor):
        return DataRoomRepository.get_investor_analytics(investor)

    @staticmethod
    def get_data_room_analytics(startup, user):
        DataRoomService._validate_startup_owner(startup, user)
        return DataRoomRepository.get_data_room_analytics(user, startup)
