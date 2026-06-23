from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.exceptions import ApplicationError

from .serializers import (
    ApplyCouponSerializer,
    InvoiceSerializer,
    SubscribeSerializer,
    SubscriptionPlanSerializer,
    UserSubscriptionSerializer,
)
from .services import BillingService


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def plan_list(request):
    plans = BillingService.get_plans()
    serializer = SubscriptionPlanSerializer(plans, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def subscription_detail(request):
    sub = BillingService.get_subscription(request.user)
    if not sub:
        return Response(None)
    serializer = UserSubscriptionSerializer(sub)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def subscribe(request):
    serializer = SubscribeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    sub = BillingService.subscribe(
        request.user,
        serializer.validated_data["plan_slug"],
        billing_cycle=serializer.validated_data.get("billing_cycle", "monthly"),
        coupon_code=serializer.validated_data.get("coupon_code"),
    )
    out = UserSubscriptionSerializer(sub)
    return Response(out.data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cancel_subscription(request):
    sub = BillingService.cancel_subscription(request.user)
    serializer = UserSubscriptionSerializer(sub)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def renew_subscription(request):
    sub = BillingService.renew_subscription(request.user)
    serializer = UserSubscriptionSerializer(sub)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def apply_coupon(request):
    serializer = ApplyCouponSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    result = BillingService.apply_coupon(
        request.user,
        serializer.validated_data["coupon_code"],
    )
    return Response(result)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def invoice_list(request):
    invoices = BillingService.get_invoices(request.user)
    serializer = InvoiceSerializer(invoices, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def usage(request):
    data = BillingService.get_usage(request.user)
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def features(request):
    data = BillingService.get_features(request.user)
    return Response(data)
