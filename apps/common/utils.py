import uuid
import re
from django.utils.text import slugify


def generate_unique_slug(base: str, model_class, slug_field: str = "slug") -> str:
    slug = slugify(base)
    if not slug:
        slug = str(uuid.uuid4())[:8]

    unique_slug = slug
    counter = 1
    while model_class.objects.filter(**{slug_field: unique_slug}).exists():
        unique_slug = f"{slug}-{counter}"
        counter += 1

    return unique_slug


def validate_file_extension(value, allowed_extensions: list[str]) -> bool:
    ext = value.name.rsplit(".", 1)[-1].lower()
    return ext in allowed_extensions


def truncate_text(text: str, max_length: int = 200) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(" ", 1)[0] + "..."
