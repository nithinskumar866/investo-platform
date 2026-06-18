from django.db import transaction
from django.db.models import Count, Q, Avg, Sum, Prefetch

from .models import DataRoom, DataRoomDocument, DocumentAccess, DocumentViewEvent


class DataRoomRepository:
    """Data access layer for data room operations."""

    # ── Data Room queries ─────────────────────────────────────────

    @staticmethod
    def create_room(startup, created_by, data):
        return DataRoom.objects.create(
            startup=startup,
            created_by=created_by,
            title=data.get("title"),
            description=data.get("description", ""),
            visibility=data.get("visibility", DataRoom.Visibility.MATCHED_INVESTORS),
        )

    @staticmethod
    def get_room(room_id):
        return DataRoom.objects.select_related(
            "startup", "created_by",
        ).prefetch_related(
            Prefetch(
                "documents",
                queryset=DataRoomDocument.objects.select_related("uploaded_by"),
            ),
        ).filter(id=room_id).first()

    @staticmethod
    def get_startup_rooms(startup):
        return DataRoom.objects.filter(
            startup=startup,
        ).select_related("created_by").annotate(
            document_count=Count("documents"),
        ).order_by("-updated_at")

    @staticmethod
    def update_room(room, data):
        for field, value in data.items():
            setattr(room, field, value)
        room.save()
        return room

    @staticmethod
    def delete_room(room):
        room.delete()

    # ── Document queries ──────────────────────────────────────────

    @staticmethod
    def get_room_documents(room):
        return DataRoomDocument.objects.filter(
            data_room=room,
        ).select_related("uploaded_by").order_by("-created_at")

    @staticmethod
    def get_document(document_id):
        return DataRoomDocument.objects.select_related(
            "data_room", "data_room__startup", "uploaded_by",
        ).prefetch_related(
            "access_grants",
        ).filter(id=document_id).first()

    @staticmethod
    def get_document_queryset():
        return DataRoomDocument.objects.select_related(
            "data_room", "data_room__startup", "uploaded_by",
        )

    @staticmethod
    @transaction.atomic
    def create_document(data_room, uploaded_by, data, file_obj):
        doc = DataRoomDocument.objects.create(
            data_room=data_room,
            file=file_obj,
            title=data.get("title", file_obj.name),
            document_type=data.get("document_type", DataRoomDocument.DocumentType.OTHER),
            version=1,
            uploaded_by=uploaded_by,
            file_size=file_obj.size,
            mime_type=file_obj.content_type or "",
        )
        return doc

    @staticmethod
    @transaction.atomic
    def create_new_version(document, data, file_obj, uploaded_by):
        document.file = file_obj
        document.version += 1
        document.file_size = file_obj.size
        document.mime_type = file_obj.content_type or ""
        document.uploaded_by = uploaded_by
        if "title" in data:
            document.title = data["title"]
        if "document_type" in data:
            document.document_type = data["document_type"]
        document.save()
        return document

    @staticmethod
    def update_document(document, data):
        for field, value in data.items():
            if field in ("title", "document_type"):
                setattr(document, field, value)
        document.save()
        return document

    @staticmethod
    def delete_document(document):
        document.file.delete()
        document.delete()

    # ── Access control ────────────────────────────────────────────

    @staticmethod
    def get_accessible_documents(investor):
        return DataRoomDocument.objects.filter(
            Q(data_room__visibility=DataRoom.Visibility.MATCHED_INVESTORS,
              data_room__startup__investment_opportunities__investor=investor)
            | Q(access_grants__investor=investor),
        ).select_related(
            "data_room", "data_room__startup", "uploaded_by",
        ).distinct().order_by("-created_at")

    @staticmethod
    def get_shared_documents(investor):
        """Documents explicitly shared via DocumentAccess."""
        return DataRoomDocument.objects.filter(
            access_grants__investor=investor,
        ).select_related(
            "data_room", "data_room__startup", "uploaded_by",
        ).order_by("-created_at")

    @staticmethod
    def grant_access(document, investor, granted_by):
        access, created = DocumentAccess.objects.get_or_create(
            document=document,
            investor=investor,
            defaults={"granted_by": granted_by},
        )
        return access, created

    @staticmethod
    def revoke_access(document, investor):
        deleted, _ = DocumentAccess.objects.filter(
            document=document, investor=investor,
        ).delete()
        return deleted > 0

    @staticmethod
    def has_access(document, investor) -> bool:
        if DocumentAccess.objects.filter(
            document=document, investor=investor,
        ).exists():
            return True
        if document.data_room.visibility == DataRoom.Visibility.MATCHED_INVESTORS:
            from apps.matching.models import MatchScore
            return MatchScore.objects.filter(
                investor=investor,
                startup=document.data_room.startup,
            ).exists()
        return False

    @staticmethod
    def get_investors_with_access(document):
        return DocumentAccess.objects.filter(
            document=document,
        ).select_related("investor", "granted_by")

    # ── View tracking ─────────────────────────────────────────────

    @staticmethod
    def record_view(document, investor, duration=None):
        return DocumentViewEvent.objects.create(
            document=document,
            investor=investor,
            duration_seconds=duration,
        )

    @staticmethod
    def get_view_events(document):
        return DocumentViewEvent.objects.filter(
            document=document,
        ).select_related("investor").order_by("-viewed_at")

    # ── Analytics ──────────────────────────────────────────────────

    @staticmethod
    def get_startup_analytics(startup):
        docs = DataRoomDocument.objects.filter(data_room__startup=startup)
        view_events = DocumentViewEvent.objects.filter(document__data_room__startup=startup)
        total_docs = docs.count()
        total_views = view_events.count()
        unique_viewers = view_events.values("investor").distinct().count()

        most_viewed = docs.annotate(
            view_count=Count("view_events"),
        ).order_by("-view_count").values("id", "title", "view_count")[:5]

        return {
            "total_documents": total_docs,
            "total_views": total_views,
            "unique_investors": unique_viewers,
            "avg_view_duration": view_events.aggregate(
                avg=Avg("duration_seconds"),
            )["avg"],
            "most_viewed_documents": list(most_viewed),
            "engagement_score": round(
                (total_views / total_docs * 10) if total_docs else 0, 1,
            ),
        }

    @staticmethod
    def get_investor_analytics(investor):
        view_events = DocumentViewEvent.objects.filter(investor=investor)
        total_viewed = view_events.values("document").distinct().count()
        total_accessible = DataRoomRepository.get_accessible_documents(investor).count()

        return {
            "viewed_documents": total_viewed,
            "unread_documents": max(0, total_accessible - total_viewed),
            "total_views": view_events.count(),
            "recently_viewed": list(
                view_events.select_related(
                    "document", "document__data_room__startup",
                ).order_by("-viewed_at")[:10].values(
                    "document__id", "document__title",
                    "document__data_room__startup__name",
                    "viewed_at", "duration_seconds",
                ),
            ),
        }

    @staticmethod
    def get_data_room_analytics(user, startup):
        """Combined analytics for the startup owner's dashboard."""
        startup_analytics = DataRoomRepository.get_startup_analytics(startup)
        rooms = DataRoomRepository.get_startup_rooms(startup)
        startup_analytics["rooms"] = [
            {
                "id": r.id,
                "title": r.title,
                "visibility": r.visibility,
                "document_count": getattr(r, "document_count", 0),
            }
            for r in rooms
        ]
        return startup_analytics
