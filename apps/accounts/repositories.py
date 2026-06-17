from django.contrib.auth import get_user_model

User = get_user_model()


class UserRepository:
    """
    Data access layer for User operations.

    Why a separate repository:
    Queries are abstracted behind methods. If we later add caching
    (Redis for frequent user lookups), we change the repository
    implementation, not the services that call it.

    Methods are deliberately thin now. They become richer as we add
    features like user feed filtering, admin user search, etc.
    """

    @staticmethod
    def get_by_email(email: str):
        return User.objects.filter(email=email.lower().strip()).first()

    @staticmethod
    def get_by_id(user_id: int):
        return User.objects.filter(id=user_id).first()

    @staticmethod
    def email_exists(email: str) -> bool:
        return User.objects.filter(email=email.lower().strip()).exists()

    @staticmethod
    def get_active_users():
        return User.objects.filter(is_active=True)

    @staticmethod
    def get_users_by_role(role: str):
        return User.objects.filter(role=role, is_active=True)
