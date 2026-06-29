from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _


ALLOWED_DOCUMENT_TYPES = ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "csv", "md"]
ALLOWED_IMAGE_TYPES = ["jpg", "jpeg", "png", "gif", "webp", "svg"]
ALLOWED_ATTACHMENT_TYPES = ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "csv", "md", "jpg", "jpeg", "png", "gif", "zip", "rar"]


from django.utils.deconstruct import deconstructible


@deconstructible
class ValidateFileSize:
    def __init__(self, max_mb=50):
        self.max_mb = max_mb

    def __call__(self, value):
        limit = self.max_mb * 1024 * 1024
        if value.size > limit:
            raise ValidationError(
                _("File size must not exceed %(max_mb)s MB."),
                params={"max_mb": self.max_mb},
            )

    def __eq__(self, other):
        return isinstance(other, ValidateFileSize) and self.max_mb == other.max_mb


validate_file_size = ValidateFileSize(max_mb=50)
validate_image_size = ValidateFileSize(max_mb=5)

validate_document_extension = FileExtensionValidator(allowed_extensions=ALLOWED_DOCUMENT_TYPES)
validate_image_extension = FileExtensionValidator(allowed_extensions=ALLOWED_IMAGE_TYPES)
validate_attachment_extension = FileExtensionValidator(allowed_extensions=ALLOWED_ATTACHMENT_TYPES)


def validate_file_extension(value, allowed_extensions=None):
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_DOCUMENT_TYPES
    ext = value.name.rsplit(".", 1)[-1].lower()
    return ext in allowed_extensions


def truncate_text(text, max_length=200):
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(" ", 1)[0] + "..."
