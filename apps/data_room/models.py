from django.conf import settings
from django.db import models


class DataRoom(models.Model):
    class Visibility(models.TextChoices):
        PRIVATE = "private", "Private"
        MATCHED_INVESTORS = "matched_investors", "Matched Investors"
        SELECTED_INVESTORS = "selected_investors", "Selected Investors"

    startup = models.ForeignKey(
        "startups.Startup",
        on_delete=models.CASCADE,
        related_name="data_rooms",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    visibility = models.CharField(
        max_length=25,
        choices=Visibility.choices,
        default=Visibility.MATCHED_INVESTORS,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_data_rooms",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "data_room_room"
        indexes = [
            models.Index(fields=["startup", "visibility"]),
            models.Index(fields=["created_by"]),
        ]
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.title} ({self.startup.name})"


class DataRoomDocument(models.Model):
    class DocumentType(models.TextChoices):
        PITCH_DECK = "pitch_deck", "Pitch Deck"
        FINANCIALS = "financials", "Financials"
        CAP_TABLE = "cap_table", "Cap Table"
        BUSINESS_PLAN = "business_plan", "Business Plan"
        LEGAL = "legal", "Legal"
        TRACTION_REPORT = "traction_report", "Traction Report"
        PRODUCT_DEMO = "product_demo", "Product Demo"
        MARKET_RESEARCH = "market_research", "Market Research"
        OTHER = "other", "Other"

    data_room = models.ForeignKey(
        DataRoom,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    file = models.FileField(upload_to="data_room/documents/")
    title = models.CharField(max_length=255)
    document_type = models.CharField(
        max_length=25,
        choices=DocumentType.choices,
        default=DocumentType.OTHER,
    )
    version = models.PositiveIntegerField(default=1)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="uploaded_documents",
    )
    file_size = models.PositiveBigIntegerField(default=0)
    mime_type = models.CharField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "data_room_document"
        indexes = [
            models.Index(fields=["data_room", "document_type"]),
            models.Index(fields=["data_room", "-created_at"]),
            models.Index(fields=["uploaded_by"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} v{self.version} ({self.document_type})"


class DocumentAccess(models.Model):
    document = models.ForeignKey(
        DataRoomDocument,
        on_delete=models.CASCADE,
        related_name="access_grants",
    )
    investor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="document_access_grants",
    )
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="granted_document_access",
    )
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "data_room_document_access"
        unique_together = [["document", "investor"]]
        indexes = [
            models.Index(fields=["investor", "document"]),
        ]

    def __str__(self):
        return f"{self.investor.email} can access {self.document.title}"


class DocumentViewEvent(models.Model):
    document = models.ForeignKey(
        DataRoomDocument,
        on_delete=models.CASCADE,
        related_name="view_events",
    )
    investor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="document_view_events",
    )
    viewed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = "data_room_document_view"
        indexes = [
            models.Index(fields=["document", "investor"]),
            models.Index(fields=["investor", "-viewed_at"]),
        ]
        ordering = ["-viewed_at"]

    def __str__(self):
        return f"{self.investor.email} viewed {self.document.title}"
