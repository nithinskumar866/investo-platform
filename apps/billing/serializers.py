from rest_framework import serializers

from .models import Coupon, Invoice, SubscriptionPlan, UserSubscription


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = [
            "id", "name", "slug", "tier", "description",
            "monthly_price", "yearly_price",
            "features", "limits", "is_popular", "sort_order",
        ]


class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    plan_slug = serializers.SlugField(write_only=True)

    class Meta:
        model = UserSubscription
        fields = [
            "id", "plan", "plan_slug", "status", "billing_cycle",
            "trial_start", "trial_end", "start_date", "end_date",
            "auto_renew", "created_at",
        ]
        read_only_fields = [
            "id", "status", "trial_start", "trial_end",
            "start_date", "end_date", "created_at",
        ]


class InvoiceSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source="plan.name", read_only=True)
    plan_slug = serializers.CharField(source="plan.slug", read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id", "invoice_number", "amount", "currency", "status",
            "billing_cycle", "plan_name", "plan_slug",
            "period_start", "period_end", "paid_at", "payment_provider",
            "created_at",
        ]


class SubscribeSerializer(serializers.Serializer):
    plan_slug = serializers.SlugField()
    billing_cycle = serializers.ChoiceField(
        choices=["monthly", "yearly"], default="monthly",
    )
    coupon_code = serializers.CharField(required=False, allow_blank=True)


class ApplyCouponSerializer(serializers.Serializer):
    coupon_code = serializers.CharField()


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = [
            "id", "code", "discount_type", "discount_value",
            "description", "usage_limit", "used_count", "is_active",
            "expires_at",
        ]
        read_only_fields = ["used_count"]


class UsageSerializer(serializers.Serializer):
    plan = serializers.CharField()
    plan_tier = serializers.CharField()
    limits = serializers.JSONField()
    usage = serializers.JSONField()


class FeatureAccessSerializer(serializers.Serializer):
    has_access = serializers.BooleanField()
    feature = serializers.CharField()
    plan_tier = serializers.CharField(required=False)
