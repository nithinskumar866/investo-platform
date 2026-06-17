from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """
    Custom manager that uses email as the unique identifier
    instead of username.

    Why: The existing codebase uses email for login. Making email the
    USERNAME_FIELD means we avoid requiring a username at registration,
    and users log in with their email address — more natural for a
    professional platform.

    Architecture:
    - create_user hashes the password via set_password
    - create_superuser creates an admin user with all permissions
    - Both validate that the email is provided
    """

    def create_user(self, email: str, password: str = None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")
        return self.create_user(email, password, **extra_fields)
