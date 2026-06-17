from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


def validate_registration(data: dict):
    """
    Registration-specific validations beyond what serializers handle.

    Checks for duplicate emails, acceptable role values, etc.
    Separated from the serializer to keep validators reusable
    (e.g., for admin bulk imports or management commands).
    """
    email = data.get("email", "").lower().strip()

    if User.objects.filter(email=email).exists():
        raise ValidationError({"email": "A user with this email already exists"})

    role = data.get("role")
    valid_roles = [r[0] for r in User.Role.choices if r[0] != "admin"]
    if role and role not in valid_roles:
        raise ValidationError({"role": f"Invalid role. Must be one of: {', '.join(valid_roles)}"})
