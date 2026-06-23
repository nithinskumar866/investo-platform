from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.exceptions import ApplicationError
from apps.common.permissions import IsEntrepreneur, IsInvestor

from .serializers import (
    StartOnboardingSerializer,
    OnboardingWizardSerializer,
    OnboardingProgressSerializer,
    FounderOnboardingSerializer,
    InvestorOnboardingSerializer,
)
from .services import OnboardingService


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def start_onboarding(request):
    serializer = StartOnboardingSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    wizard = OnboardingService.start_onboarding(
        request.user,
        serializer.validated_data["wizard_type"],
    )
    return Response(
        {"status": "success", "data": OnboardingWizardSerializer(wizard).data},
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def onboarding_progress(request):
    progress = OnboardingService.get_progress(request.user)
    if not progress:
        raise ApplicationError("No onboarding wizard found", "NO_WIZARD", 404)

    return Response({"status": "success", "data": progress})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def complete_step(request):
    step_key = request.data.get("step_key")
    data = request.data.get("data", {})

    if not step_key:
        raise ApplicationError("step_key is required", "MISSING_STEP_KEY")

    progress = OnboardingService.complete_step(request.user, step_key, data)
    if not progress:
        raise ApplicationError("Invalid step or no wizard found", "INVALID_STEP", 404)

    return Response({"status": "success", "data": progress})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def complete_onboarding(request):
    wizard = OnboardingService.complete_onboarding(request.user)
    if not wizard:
        raise ApplicationError("No onboarding wizard found", "NO_WIZARD", 404)

    return Response(
        {"status": "success", "data": OnboardingWizardSerializer(wizard).data},
    )


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsEntrepreneur])
def founder_onboarding_data(request):
    data = OnboardingService.get_founder_data(request.user)

    if request.method == "GET":
        return Response(
            {"status": "success", "data": FounderOnboardingSerializer(data).data},
        )

    serializer = FounderOnboardingSerializer(data, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(
        {"status": "success", "data": FounderOnboardingSerializer(data).data},
    )


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsInvestor])
def investor_onboarding_data(request):
    data = OnboardingService.get_investor_data(request.user)

    if request.method == "GET":
        return Response(
            {"status": "success", "data": InvestorOnboardingSerializer(data).data},
        )

    serializer = InvestorOnboardingSerializer(data, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(
        {"status": "success", "data": InvestorOnboardingSerializer(data).data},
    )
