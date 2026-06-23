from datetime import timedelta

from django.utils import timezone

from apps.common.exceptions import ApplicationError

from .models import Invoice, SubscriptionPlan, UserSubscription
from .repositories import (
    CouponRepository,
    InvoiceRepository,
    PlanRepository,
    SubscriptionRepository,
)


class BillingService:
    """Business logic for subscription and billing operations."""

    # ═══════════════════════════════════════════════════════════════
    #  PLAN QUERIES
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def get_plans():
        return PlanRepository.get_active_plans()

    @staticmethod
    def get_plan(slug):
        plan = PlanRepository.get_plan_by_slug(slug)
        if not plan:
            raise ApplicationError("Plan not found", "NOT_FOUND", 404)
        return plan

    # ═══════════════════════════════════════════════════════════════
    #  SUBSCRIPTION MANAGEMENT
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def get_subscription(user):
        sub = SubscriptionRepository.get_user_subscription(user)
        if not sub:
            free_plan = PlanRepository.get_free_plan()
            if not free_plan:
                return None
            sub = SubscriptionRepository.create_subscription(
                user, free_plan,
                status=UserSubscription.Status.ACTIVE,
                trial_days=0,
            )
        return sub

    @staticmethod
    def subscribe(user, plan_slug, billing_cycle="monthly", coupon_code=None):
        plan = PlanRepository.get_plan_by_slug(plan_slug)
        if not plan:
            raise ApplicationError("Plan not found", "NOT_FOUND", 404)

        if plan.tier == SubscriptionPlan.Tier.FREE:
            raise ApplicationError("Cannot subscribe to the free plan", "INVALID_PLAN", 400)

        cycle = (
            UserSubscription.BillingCycle.YEARLY
            if billing_cycle == "yearly"
            else UserSubscription.BillingCycle.MONTHLY
        )

        price = plan.yearly_price if cycle == UserSubscription.BillingCycle.YEARLY else plan.monthly_price

        coupon = None
        if coupon_code:
            coupon = CouponRepository.get_coupon_by_code(coupon_code)
            if not coupon:
                raise ApplicationError("Invalid coupon code", "INVALID_COUPON", 400)
            valid, msg = CouponRepository.validate_coupon(coupon, user)
            if not valid:
                raise ApplicationError(msg, "COUPON_ERROR", 400)
            price = CouponRepository.calculate_discounted_price(price, coupon)

        existing = SubscriptionRepository.get_user_subscription(user)
        if existing:
            if existing.status in [
                UserSubscription.Status.ACTIVE,
                UserSubscription.Status.TRIAL,
            ] and existing.plan and existing.plan.tier != SubscriptionPlan.Tier.FREE:
                raise ApplicationError(
                    "Already subscribed to a premium plan", "ALREADY_SUBSCRIBED", 400,
                )

            SubscriptionRepository.update_subscription(
                existing,
                plan=plan,
                status=UserSubscription.Status.ACTIVE,
                billing_cycle=cycle,
                coupon=coupon,
                start_date=timezone.now(),
                end_date=timezone.now() + timedelta(
                    days=365 if cycle == UserSubscription.BillingCycle.YEARLY else 30,
                ),
            )
            subscription = existing
        else:
            subscription = SubscriptionRepository.create_subscription(
                user, plan,
                status=UserSubscription.Status.ACTIVE,
                billing_cycle=cycle,
                trial_days=0,
                coupon=coupon,
            )

        InvoiceRepository.create_invoice(
            user=user,
            subscription=subscription,
            plan=plan,
            amount=price,
            billing_cycle=cycle,
            status=Invoice.Status.PAID,
            payment_provider="system",
            payment_reference=f"auto-{subscription.id}",
        )

        if coupon:
            CouponRepository.apply_coupon(coupon)

        return subscription

    @staticmethod
    def cancel_subscription(user):
        sub = SubscriptionRepository.get_user_subscription(user)
        if not sub:
            raise ApplicationError("No active subscription", "NOT_FOUND", 404)

        if sub.status not in [
            UserSubscription.Status.ACTIVE,
            UserSubscription.Status.TRIAL,
        ]:
            raise ApplicationError("Subscription is not active", "INVALID_STATUS", 400)

        SubscriptionRepository.cancel_subscription(sub)

        free_plan = PlanRepository.get_free_plan()
        if free_plan:
            SubscriptionRepository.update_subscription(
                sub, plan=free_plan, end_date=timezone.now(),
            )

        return sub

    @staticmethod
    def renew_subscription(user):
        sub = SubscriptionRepository.get_user_subscription(user)
        if not sub:
            raise ApplicationError("No subscription found", "NOT_FOUND", 404)

        if sub.status != UserSubscription.Status.ACTIVE:
            raise ApplicationError("Subscription is not active", "INVALID_STATUS", 400)

        price = (
            sub.plan.yearly_price if sub.billing_cycle == UserSubscription.BillingCycle.YEARLY
            else sub.plan.monthly_price
        )
        if sub.coupon and sub.coupon.is_valid:
            price = CouponRepository.calculate_discounted_price(price, sub.coupon)

        sub = SubscriptionRepository.renew_subscription(sub)

        InvoiceRepository.create_invoice(
            user=user,
            subscription=sub,
            plan=sub.plan,
            amount=price,
            billing_cycle=sub.billing_cycle,
            status=Invoice.Status.PAID,
            payment_provider="system",
            payment_reference=f"renew-{sub.id}-{timezone.now().timestamp()}",
        )

        return sub

    # ═══════════════════════════════════════════════════════════════
    #  COUPONS
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def apply_coupon(user, coupon_code):
        coupon = CouponRepository.get_coupon_by_code(coupon_code)
        if not coupon:
            raise ApplicationError("Invalid coupon code", "INVALID_COUPON", 404)

        valid, msg = CouponRepository.validate_coupon(coupon, user)
        if not valid:
            raise ApplicationError(msg, "COUPON_ERROR", 400)

        sub = SubscriptionRepository.get_user_subscription(user)
        if not sub or not sub.plan:
            raise ApplicationError("No active subscription", "NOT_FOUND", 404)

        price = (
            sub.plan.yearly_price if sub.billing_cycle == UserSubscription.BillingCycle.YEARLY
            else sub.plan.monthly_price
        )
        discounted = CouponRepository.calculate_discounted_price(price, coupon)

        SubscriptionRepository.update_subscription(sub, coupon=coupon)
        CouponRepository.apply_coupon(coupon)

        return {
            "original_price": float(price),
            "discounted_price": float(discounted),
            "discount": float(price - discounted),
            "coupon_code": coupon.code,
        }

    # ═══════════════════════════════════════════════════════════════
    #  INVOICES
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def get_invoices(user):
        return InvoiceRepository.get_user_invoices(user)

    # ═══════════════════════════════════════════════════════════════
    #  USAGE & FEATURE ACCESS
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def get_usage(user):
        sub = SubscriptionRepository.get_user_subscription(user)
        if not sub or not sub.plan:
            return {}

        limits = sub.plan.limits or {}
        usage = {}

        from apps.matching.models import MatchScore
        from apps.chat.models import Conversation
        from apps.data_room.models import DataRoomDocument
        from apps.activity_feed.models import ActivityFeed

        usage["matches"] = MatchScore.objects.filter(investor=user).count()
        usage["conversations"] = Conversation.objects.filter(
            participants__user=user,
        ).distinct().count()
        usage["data_room_documents"] = DataRoomDocument.objects.filter(
            data_room__startup__owner=user,
        ).count()
        usage["feed_activities"] = ActivityFeed.objects.filter(actor=user).count()

        return {
            "plan": sub.plan.slug,
            "plan_tier": sub.plan.tier,
            "limits": limits,
            "usage": usage,
        }

    @staticmethod
    def check_feature_access(user, feature_key):
        sub = SubscriptionRepository.get_user_subscription(user)
        if not sub or not sub.plan:
            return {"has_access": False, "feature": feature_key}

        plan = sub.plan
        features = plan.features or {}

        if feature_key in features:
            has_access = bool(features[feature_key])
        else:
            has_access = plan.tier != SubscriptionPlan.Tier.FREE

        return {"has_access": has_access, "feature": feature_key, "plan_tier": plan.tier}

    @staticmethod
    def check_usage_limit(user, resource_key, current_count=None):
        sub = SubscriptionRepository.get_user_subscription(user)
        if not sub or not sub.plan:
            return {"within_limit": True, "limit": None, "current": current_count}

        limits = sub.plan.limits or {}
        limit = limits.get(resource_key)

        if limit is None:
            return {"within_limit": True, "limit": None, "current": current_count}

        if current_count is None:
            current_count = BillingService._get_resource_count(user, resource_key)

        return {
            "within_limit": current_count < limit,
            "limit": limit,
            "current": current_count,
            "remaining": max(limit - current_count, 0),
        }

    @staticmethod
    def _get_resource_count(user, resource_key):
        mapping = {
            "matches": ("apps.matching.models.MatchScore", {"investor": user}),
            "conversations": ("apps.chat.models.Conversation", {"participants__user": user}),
            "data_room_storage": ("apps.data_room.models.DataRoomDocument", {"data_room__startup__owner": user}),
            "saved_searches": ("apps.search_app.models.SavedSearch", {"user": user}),
        }
        if resource_key not in mapping:
            return 0
        from django.apps import apps
        model_path, filters = mapping[resource_key]
        parts = model_path.split(".")
        model = apps.get_model(parts[0], parts[2])
        if resource_key == "conversations":
            return model.objects.filter(**filters).distinct().count()
        return model.objects.filter(**filters).count()

    # ═══════════════════════════════════════════════════════════════
    #  FEATURES LIST
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def get_features(user):
        sub = SubscriptionRepository.get_user_subscription(user)
        plans = PlanRepository.get_active_plans()

        current_tier = sub.plan.tier if sub and sub.plan else SubscriptionPlan.Tier.FREE

        data = []
        for plan in plans:
            data.append({
                "id": plan.id,
                "name": plan.name,
                "slug": plan.slug,
                "tier": plan.tier,
                "monthly_price": float(plan.monthly_price),
                "yearly_price": float(plan.yearly_price),
                "features": plan.features,
                "limits": plan.limits,
                "is_popular": plan.is_popular,
                "is_current": plan.tier == current_tier,
                "sort_order": plan.sort_order,
            })
        return data
