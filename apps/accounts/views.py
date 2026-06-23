import logging
from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from apps.common.throttles import OTPRequestThrottle, ResendVerificationThrottle, LoginRateThrottle

from .serializers import (
    RegistrationSerializer,
    UserSerializer,
    UserUpdateSerializer,
    TokenObtainSerializer,
    EmailVerificationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    CompleteUserSerializer,
    EntrepreneurProfileSerializer,
    PublicEntrepreneurProfileSerializer,
    EntrepreneurProfileListSerializer,
    InvestorProfileSerializer,
    PublicInvestorProfileSerializer,
    InvestorProfileListSerializer,
)
from .services import AuthService, create_tokens_for_user, EntrepreneurProfileService, InvestorProfileService
from apps.common.exceptions import ApplicationError

User = get_user_model()
logger = logging.getLogger(__name__)


@extend_schema(
    tags=["Authentication"],
    request=RegistrationSerializer,
    responses={201: RegistrationSerializer},
    summary="Register a new user",
)
@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    """
    User registration endpoint.

    Why a function-based view (not ViewSet):
    Registration is a single action with custom response logic
    (returns JWT tokens alongside user data). A ViewSet would
    require overriding create() anyway — FBV is simpler here.

    Workflow:
    1. Validate input via RegistrationSerializer
    2. Create user
    3. Trigger async email verification (Celery)
    4. Generate JWT tokens so user is immediately authenticated
    5. Return user data + tokens
    """
    serializer = RegistrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()

    AuthService.send_verification_email(user)
    AuthService.send_welcome_email(user)

    tokens = create_tokens_for_user(user)

    logger.info(f"New user registered: {user.email} (role={user.role})")

    return Response(
        {
            "status": "success",
            "data": {
                "user": UserSerializer(user).data,
                "tokens": tokens,
            },
        },
        status=status.HTTP_201_CREATED,
    )


@extend_schema(
    tags=["Authentication"],
    request=TokenObtainSerializer,
    summary="Login with email and password",
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def login(request):
    """
    Custom login that returns JWT tokens.

    Why custom instead of simplejwt's built-in TokenObtainPairView:
    We want:
    - Custom response format (wrapped in status/data envelope)
    - Logging of successful/failed login attempts
    - Update last_login_at and last_login_ip
    - Return user data alongside tokens (saves a separate /me call)

    Why username=email in kwargs:
    Our User model uses email as USERNAME_FIELD, but authenticate()
    still expects the 'username' kwarg regardless of the field name.
    """
    serializer = TokenObtainSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = request.data.get("email")
    password = request.data.get("password")

    user = authenticate(username=email, password=password)
    if user is None:
        try:
            user_obj = User.objects.get(email__iexact=email)
            if user_obj.check_password(password) and not user_obj.is_active:
                return Response(
                    {"status": "error", "error": {"code": "ACCOUNT_DISABLED", "message": "Account is disabled"}},
                    status=status.HTTP_403_FORBIDDEN,
                )
        except User.DoesNotExist:
            pass

        logger.warning(f"Failed login attempt for {email}")
        return Response(
            {"status": "error", "error": {"code": "INVALID_CREDENTIALS", "message": "Invalid email or password"}},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_active:
        return Response(
            {"status": "error", "error": {"code": "ACCOUNT_DISABLED", "message": "Account is disabled"}},
            status=status.HTTP_403_FORBIDDEN,
        )

    tokens = create_tokens_for_user(user)

    user.last_login = timezone.now()
    ip_address = request.META.get("REMOTE_ADDR", "")
    if ip_address:
        user.last_login_ip = ip_address
    user.save(update_fields=["last_login", "last_login_ip"])

    logger.info(f"User logged in: {user.email}")

    return Response(
        {
            "status": "success",
            "data": {
                "user": UserSerializer(user).data,
                "tokens": tokens,
            },
        },
    )


@extend_schema(
    tags=["Authentication"],
    request={"application/json": {"type": "object", "properties": {"refresh": {"type": "string"}}}},
    summary="Logout and blacklist refresh token",
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Invalidate refresh token.

    Blacklists the refresh token so it cannot be used again.
    The access token remains valid until its 15-minute expiry.
    This is a deliberate trade-off — short-lived access tokens
    minimize the damage from not being able to instantly revoke them.
    """
    try:
        refresh_token = request.data.get("refresh")
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"status": "success", "data": {"message": "Logged out successfully"}})
    except Exception as e:
        logger.error(f"Logout error: {e}")

    return Response(
        {"status": "success", "data": {"message": "Logged out"}},
    )


@extend_schema(
    tags=["Profile"],
    summary="Get or update current user profile",
)
@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def me(request):
    if request.method == "GET":
        return Response(
            {"status": "success", "data": CompleteUserSerializer(request.user).data},
        )

    serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(
        {"status": "success", "data": CompleteUserSerializer(request.user).data},
    )


@extend_schema(
    tags=["Authentication"],
    request=EmailVerificationSerializer,
    summary="Verify email with OTP",
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([OTPRequestThrottle])
def verify_email(request):
    serializer = EmailVerificationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    success = AuthService.verify_email(
        email=serializer.validated_data["email"],
        otp=serializer.validated_data["otp"],
    )

    if not success:
        return Response(
            {"status": "error", "error": {"code": "INVALID_OTP", "message": "Invalid or expired verification code"}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Get user to generate tokens for auto-login
    user = User.objects.get(email=serializer.validated_data["email"])
    tokens = create_tokens_for_user(user)

    user.last_login = timezone.now()
    ip_address = request.META.get("REMOTE_ADDR", "")
    if ip_address:
        user.last_login_ip = ip_address
    user.save(update_fields=["last_login", "last_login_ip"])

    return Response(
        {
            "status": "success",
            "data": {
                "message": "Email verified successfully",
                "user": UserSerializer(user).data,
                "tokens": tokens,
            },
        },
    )


@extend_schema(
    tags=["Authentication"],
    summary="Resend verification email",
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([ResendVerificationThrottle])
def resend_verification(request):
    email = request.data.get("email", "").lower().strip()
    user = User.objects.filter(email=email).first()

    if user and not user.is_verified:
        AuthService.send_verification_email(user)
        return Response(
            {"status": "success", "data": {"message": "Verification email resent"}},
        )

    return Response(
        {"status": "success", "data": {"message": "If the account exists, a verification email has been sent"}},
    )


@extend_schema(
    tags=["Authentication"],
    request=PasswordResetRequestSerializer,
    summary="Request password reset OTP",
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([OTPRequestThrottle])
def forgot_password(request):
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    AuthService.send_password_reset_otp(serializer.validated_data["email"])

    return Response(
        {"status": "success", "data": {"message": "If the account exists, a reset code has been sent"}},
    )


@extend_schema(
    tags=["Authentication"],
    request=PasswordResetConfirmSerializer,
    summary="Reset password with OTP",
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([OTPRequestThrottle])
def reset_password(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    success = AuthService.reset_password(
        email=serializer.validated_data["email"],
        otp=serializer.validated_data["otp"],
        new_password=serializer.validated_data["password"],
    )

    if not success:
        return Response(
            {"status": "error", "error": {"code": "INVALID_OTP", "message": "Invalid or expired reset code"}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        {"status": "success", "data": {"message": "Password reset successfully"}},
    )


@extend_schema(
    tags=["Profile"],
    summary="Get or update entrepreneur profile",
)
@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def entrepreneur_profile(request):
    if request.user.role != "entrepreneur":
        raise ApplicationError("User is not an entrepreneur", "WRONG_ROLE", 403)

    profile = EntrepreneurProfileService.get_or_create_profile(request.user)

    if request.method == "GET":
        return Response(
            {"status": "success", "data": EntrepreneurProfileSerializer(profile).data},
        )

    serializer = EntrepreneurProfileSerializer(profile, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(
        {"status": "success", "data": EntrepreneurProfileSerializer(profile).data},
    )


@extend_schema(
    tags=["Profile"],
    summary="Get or update investor profile",
)
@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def investor_profile(request):
    if request.user.role != "investor":
        raise ApplicationError("User is not an investor", "WRONG_ROLE", 403)

    profile = InvestorProfileService.get_or_create_profile(request.user)

    if request.method == "GET":
        return Response(
            {"status": "success", "data": InvestorProfileSerializer(profile).data},
        )

    serializer = InvestorProfileSerializer(profile, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(
        {"status": "success", "data": InvestorProfileSerializer(profile).data},
    )


# ── Public Entrepreneur Profiles ─────────────────────────────────


@extend_schema(
    tags=["Profiles"],
    summary="List public entrepreneur profiles",
    parameters=[
        OpenApiParameter("industry", str, description="Filter by industry"),
        OpenApiParameter("search", str, description="Search by name, tagline, description"),
    ],
)
@api_view(["GET"])
@permission_classes([AllowAny])
def public_entrepreneur_profiles(request):
    industry = request.GET.get("industry")
    search = request.GET.get("search")
    profiles = EntrepreneurProfileService.list_public_profiles(
        industry=industry, search=search,
    )
    serializer = EntrepreneurProfileListSerializer(profiles, many=True)
    return Response({"status": "success", "data": serializer.data})


@extend_schema(
    tags=["Profiles"],
    summary="Get a public entrepreneur profile by ID",
)
@api_view(["GET"])
@permission_classes([AllowAny])
def public_entrepreneur_profile_detail(request, profile_id):
    profile = EntrepreneurProfileService.get_public_profile_by_id(profile_id)
    if not profile:
        raise ApplicationError("Profile not found", "NOT_FOUND", 404)
    serializer = PublicEntrepreneurProfileSerializer(profile)
    return Response({"status": "success", "data": serializer.data})


@extend_schema(
    tags=["Profile"],
    summary="Get entrepreneur profile completeness",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def entrepreneur_profile_completeness(request):
    if request.user.role != "entrepreneur":
        raise ApplicationError("User is not an entrepreneur", "WRONG_ROLE", 403)
    completeness = EntrepreneurProfileService.get_profile_completeness(request.user)
    return Response({"status": "success", "data": completeness})


@extend_schema(
    tags=["Profile"],
    summary="Get startups for the current entrepreneur profile",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def entrepreneur_profile_startups(request):
    if request.user.role != "entrepreneur":
        raise ApplicationError("User is not an entrepreneur", "WRONG_ROLE", 403)
    startups = EntrepreneurProfileService.get_profile_startups(request.user)
    from apps.startups.serializers import StartupListSerializer
    serializer = StartupListSerializer(startups, many=True)
    return Response({"status": "success", "data": serializer.data})


# ── Public Investor Profiles ────────────────────────────────────


@extend_schema(
    tags=["Profiles"],
    summary="List public investor profiles",
    parameters=[
        OpenApiParameter("industry", str, description="Filter by preferred industry"),
        OpenApiParameter("geography", str, description="Filter by preferred geography"),
        OpenApiParameter("ticket_min", float, description="Minimum ticket size filter"),
        OpenApiParameter("ticket_max", float, description="Maximum ticket size filter"),
        OpenApiParameter("search", str, description="Search by name, tagline, focus"),
    ],
)
@api_view(["GET"])
@permission_classes([AllowAny])
def public_investor_profiles(request):
    from decimal import Decimal
    industry = request.GET.get("industry")
    geography = request.GET.get("geography")
    ticket_min = request.GET.get("ticket_min")
    ticket_max = request.GET.get("ticket_max")
    search = request.GET.get("search")
    try:
        ticket_min = Decimal(ticket_min) if ticket_min else None
    except (ValueError, TypeError):
        ticket_min = None
    try:
        ticket_max = Decimal(ticket_max) if ticket_max else None
    except (ValueError, TypeError):
        ticket_max = None
    profiles = InvestorProfileService.list_public_profiles(
        industry=industry, geography=geography,
        ticket_min=ticket_min, ticket_max=ticket_max,
        search=search,
    )
    serializer = InvestorProfileListSerializer(profiles, many=True)
    return Response({"status": "success", "data": serializer.data})


@extend_schema(
    tags=["Profiles"],
    summary="Get a public investor profile by ID",
)
@api_view(["GET"])
@permission_classes([AllowAny])
def public_investor_profile_detail(request, profile_id):
    profile = InvestorProfileService.get_public_profile_by_id(profile_id)
    if not profile:
        raise ApplicationError("Profile not found", "NOT_FOUND", 404)
    serializer = PublicInvestorProfileSerializer(profile)
    return Response({"status": "success", "data": serializer.data})


@extend_schema(
    tags=["Profile"],
    summary="Get investor profile completeness",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def investor_profile_completeness(request):
    if request.user.role != "investor":
        raise ApplicationError("User is not an investor", "WRONG_ROLE", 403)
    completeness = InvestorProfileService.get_profile_completeness(request.user)
    return Response({"status": "success", "data": completeness})


@extend_schema(
    tags=["Profile"],
    summary="Get investor profile statistics",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def investor_profile_statistics(request):
    if request.user.role != "investor":
        raise ApplicationError("User is not an investor", "WRONG_ROLE", 403)
    stats = InvestorProfileService.get_investor_statistics()
    return Response({"status": "success", "data": stats})
