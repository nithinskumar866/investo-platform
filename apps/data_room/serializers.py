from rest_framework import serializers

from .models import DataRoom, DataRoomDocument, DocumentAccess, DocumentViewEvent
from .repositories import DataRoomRepository


class DataRoomListSerializer(serializers.ModelSerializer):
    document_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = DataRoom
        fields = [
            "id", "title", "description", "visibility",
            "document_count", "updated_at", "created_at",
        ]


class DataRoomDetailSerializer(serializers.ModelSerializer):
    documents = serializers.SerializerMethodField()
    created_by_email = serializers.EmailField(
        source="created_by.email", read_only=True,
    )

    class Meta:
        model = DataRoom
        fields = [
            "id", "startup", "title", "description", "visibility",
            "created_by", "created_by_email",
            "documents", "updated_at", "created_at",
        ]
        read_only_fields = ["startup", "created_by"]

    def get_documents(self, obj):
        docs = getattr(obj, "_documents", None) or DataRoomRepository.get_room_documents(obj)
        return DataRoomDocumentListSerializer(docs, many=True).data


class DataRoomCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    visibility = serializers.ChoiceField(
        choices=DataRoom.Visibility.choices,
        default=DataRoom.Visibility.MATCHED_INVESTORS,
    )


class DataRoomUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    visibility = serializers.ChoiceField(
        choices=DataRoom.Visibility.choices, required=False,
    )


class DataRoomDocumentListSerializer(serializers.ModelSerializer):
    uploaded_by_email = serializers.EmailField(
        source="uploaded_by.email", read_only=True,
    )
    signed_url = serializers.SerializerMethodField()

    class Meta:
        model = DataRoomDocument
        fields = [
            "id", "data_room", "title", "document_type",
            "version", "file_size", "mime_type",
            "uploaded_by", "uploaded_by_email",
            "signed_url", "created_at",
        ]
        read_only_fields = ["data_room", "uploaded_by", "version", "file_size", "mime_type"]

    def get_signed_url(self, obj):
        try:
            return obj.file.url
        except Exception:
            return None


class DataRoomDocumentDetailSerializer(serializers.ModelSerializer):
    uploaded_by_email = serializers.EmailField(
        source="uploaded_by.email", read_only=True,
    )
    signed_url = serializers.SerializerMethodField()
    access_list = serializers.SerializerMethodField()

    class Meta:
        model = DataRoomDocument
        fields = [
            "id", "data_room", "title", "document_type",
            "version", "file_size", "mime_type",
            "uploaded_by", "uploaded_by_email",
            "signed_url", "access_list", "created_at",
        ]

    def get_signed_url(self, obj):
        try:
            return obj.file.url
        except Exception:
            return None

    def get_access_list(self, obj):
        from apps.accounts.serializers import UserSerializer
        grants = DocumentAccess.objects.filter(document=obj).select_related("investor")
        return [
            {
                "investor_id": g.investor_id,
                "investor_email": g.investor.email,
                "granted_at": g.granted_at,
            }
            for g in grants
        ]


class DocumentUploadSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=False)
    document_type = serializers.ChoiceField(
        choices=DataRoomDocument.DocumentType.choices,
        default=DataRoomDocument.DocumentType.OTHER,
    )
    file = serializers.FileField()


class DocumentAccessSerializer(serializers.Serializer):
    investor_id = serializers.IntegerField()


class DocumentViewSerializer(serializers.Serializer):
    duration_seconds = serializers.IntegerField(
        required=False, allow_null=True, min_value=0,
    )


class DocumentAccessGrantSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentAccess
        fields = ["id", "document", "investor", "granted_by", "granted_at"]
        read_only_fields = ["document", "granted_by", "granted_at"]


class DocumentViewAnalyticsSerializer(serializers.ModelSerializer):
    investor_email = serializers.EmailField(source="investor.email", read_only=True)

    class Meta:
        model = DocumentViewEvent
        fields = ["id", "investor", "investor_email", "viewed_at", "duration_seconds"]
        read_only_fields = ["investor", "viewed_at"]
