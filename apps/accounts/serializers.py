from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .validators import validate_registration
from .models import EntrepreneurProfile, InvestorProfile

User = get_user_model()


class RegistrationSerializer(serializers.ModelSerializer):
    """
    Handles user registration with validation.

    Why not a ModelForm:
    We use DRF serializers to maintain consistency with the API-first
    architecture. This serializer is used by the API view and can also
    be used by templates — same code path.

    Design decisions:
    - password is write_only: never returned in responses
    - password uses PasswordInput-equivalent via style
    - role is required: every user must choose their role at signup
    - email is lowercased: prevents duplicate accounts with case variants
    """

    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        min_length=8,
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "confirm_password",
            "first_name",
            "last_name",
            "role",
            "phone",
        ]

    def validate_email(self, value):
        return value.lower().strip()

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("confirm_password"):
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match"}
            )
        validate_registration(attrs)
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    """
    Public-facing user profile serializer.

    password is never exposed. Role is read-only after creation
    (users can't change their own role — that requires admin).
    """

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "avatar",
            "phone",
            "is_verified",
            "date_joined",
        ]
        read_only_fields = [
            "id",
            "email",
            "role",
            "is_verified",
            "date_joined",
        ]


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Allows users to update their own profile.
    Role changes are not allowed here — must go through admin.
    """

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "avatar",
            "phone",
        ]


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extends the default JWT token to include user role in payload.

    Why custom token payload:
    The frontend needs to know the user's role on every authenticated
    request to render the correct dashboard and navigation. Including
    it in the JWT avoids a separate /me/ API call on every page load.

    What else could go in here:
    - is_verified (so frontend can show verification prompts)
    - first_name/last_name (for personalized navigation)
    But we keep it minimal — JWT should only carry authorization data,
    not profile data. Profile data comes from /me/.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["email"] = user.email
        return token


class TokenObtainSerializer(CustomTokenObtainPairSerializer):
    """
    Custom JWT token serializer that accepts email as username.

    Why custom:
    DRF simplejwt's default serializer expects a 'username' field.
    Our User model uses email as USERNAME_FIELD, but we want the
    API to be explicit about accepting 'email' not 'username'.
    """

    username_field = User.EMAIL_FIELD

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[self.username_field] = serializers.EmailField()
        self.fields.pop("username", None)


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )
    confirm_password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match"}
            )
        return attrs


class EmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)


class EntrepreneurProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntrepreneurProfile
        fields = [
            "id",
            "company_name",
            "company_description",
            "website",
            "industry",
            "funding_stage",
            "pitch_deck",
            "linkedin_url",
            "team_size",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class InvestorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvestorProfile
        fields = [
            "id",
            "investor_type",
            "investment_focus",
            "preferred_stage",
            "ticket_size_min",
            "ticket_size_max",
            "industries_of_interest",
            "portfolio_count",
            "linkedin_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CompleteUserSerializer(serializers.ModelSerializer):
    entrepreneur_profile = EntrepreneurProfileSerializer(read_only=True)
    investor_profile = InvestorProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "role",
            "first_name",
            "last_name",
            "avatar",
            "phone",
            "is_verified",
            "date_joined",
            "entrepreneur_profile",
            "investor_profile",
        ]
        read_only_fields = ["id", "email", "role", "is_verified", "date_joined"]
