from django.contrib import admin

from .models import DataRoom, DataRoomDocument, DocumentAccess, DocumentViewEvent


@admin.register(DataRoom)
class DataRoomAdmin(admin.ModelAdmin):
    list_display = ["title", "startup", "visibility", "created_by", "updated_at"]
    list_filter = ["visibility"]
    search_fields = ["title", "startup__name"]
    raw_id_fields = ["startup", "created_by"]


@admin.register(DataRoomDocument)
class DataRoomDocumentAdmin(admin.ModelAdmin):
    list_display = ["title", "data_room", "document_type", "version", "file_size", "uploaded_by", "created_at"]
    list_filter = ["document_type"]
    search_fields = ["title", "data_room__title"]
    raw_id_fields = ["data_room", "uploaded_by"]


@admin.register(DocumentAccess)
class DocumentAccessAdmin(admin.ModelAdmin):
    list_display = ["document", "investor", "granted_by", "granted_at"]
    search_fields = ["document__title", "investor__email"]
    raw_id_fields = ["document", "investor", "granted_by"]


@admin.register(DocumentViewEvent)
class DocumentViewEventAdmin(admin.ModelAdmin):
    list_display = ["document", "investor", "viewed_at", "duration_seconds"]
    list_filter = ["viewed_at"]
    search_fields = ["document__title", "investor__email"]
    raw_id_fields = ["document", "investor"]
