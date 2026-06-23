import uuid
import re
from django.utils.text import slugify

from .validators import validate_file_extension, truncate_text


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
