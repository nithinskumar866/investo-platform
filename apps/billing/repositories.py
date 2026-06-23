from datetime import timedelta

from django.db import transaction
from django.db.models import Count, F, Prefetch, Q, Sum
from django.utils import timezone

from .models import Coupon, Invoice, SubscriptionPlan, UserSubscription


class PlanRepository:
    """Data access for subscription plans."""

    @staticmethod
    def get_active_plans():
        return SubscriptionPlan.objects.filter(is_active=True).order_by("sort_order")

    @staticmethod
    def get_plan_by_slug(slug):
        try:
            return SubscriptionPlan.objects.get(slug=slug, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return None

    @staticmethod
    def get_plan_by_id(plan_id):
        try:
            return SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return None

    @staticmethod
    def get_free_plan():
        return SubscriptionPlan.objects.filter(
            tier=SubscriptionPlan.Tier.FREE, is_active=True,
        ).first()

    @staticmethod
    def get_premium_plans():
        return SubscriptionPlan.objects.filter(
            ~Q(tier=SubscriptionPlan.Tier.FREE), is_active=True,
        ).order_by("sort_order")


class SubscriptionRepository:
    """Data access for user subscriptions."""

    @staticmethod
    def get_user_subscription(user):
        try:
            return UserSubscription.objects.select_related("plan", "coupon").get(
                user=user,
            )
        except UserSubscription.DoesNotExist:
            return None

    @staticmethod
    def get_active_subscription(user):
        return UserSubscription.objects.select_related("plan").filter(
            user=user,
            status__in=[
                UserSubscription.Status.ACTIVE,
                UserSubscription.Status.TRIAL,
            ],
        ).first()

    @staticmethod
    @transaction.atomic
    def create_subscription(user, plan, status=UserSubscription.Status.TRIAL,
                            billing_cycle=UserSubscription.BillingCycle.MONTHLY,
                            trial_days=14, coupon=None):
        now = timezone.now()
        trial_end = now + timedelta(days=trial_days) if status == UserSubscription.Status.TRIAL else None

        sub, created = UserSubscription.objects.update_or_create(
            user=user,
            defaults={
                "plan": plan,
                "status": status,
                "billing_cycle": billing_cycle,
                "trial_start": now if trial_end else None,
                "trial_end": trial_end,
                "start_date": now,
                "end_date": trial_end if trial_end else now + timedelta(days=30),
                "coupon": coupon,
                "auto_renew": True,
            },
        )
        return sub

    @staticmethod
    @transaction.atomic
    def update_subscription(subscription, **kwargs):
        for key, value in kwargs.items():
            setattr(subscription, key, value)
        subscription.save()
        return subscription

    @staticmethod
    @transaction.atomic
    def cancel_subscription(subscription):
        subscription.status = UserSubscription.Status.CANCELLED
        subscription.auto_renew = False
        subscription.save()
        return subscription

    @staticmethod
    @transaction.atomic
    def renew_subscription(subscription):
        now = timezone.now()
        cycle_days = 365 if subscription.billing_cycle == UserSubscription.BillingCycle.YEARLY else 30
        subscription.status = UserSubscription.Status.ACTIVE
        subscription.start_date = now
        subscription.end_date = now + timedelta(days=cycle_days)
        subscription.save()
        return subscription

    @staticmethod
    def get_expired_subscriptions():
        return UserSubscription.objects.filter(
            status__in=[UserSubscription.Status.ACTIVE, UserSubscription.Status.TRIAL],
            end_date__lt=timezone.now(),
        )

    @staticmethod
    def get_expiring_soon(days=7):
        return UserSubscription.objects.filter(
            status=UserSubscription.Status.ACTIVE,
            end_date__gte=timezone.now(),
            end_date__lte=timezone.now() + timedelta(days=days),
            auto_renew=True,
        )


class InvoiceRepository:
    """Data access for invoices."""

    @staticmethod
    def get_user_invoices(user, limit=20):
        return Invoice.objects.filter(user=user).select_related("plan").order_by("-created_at")[:limit]

    @staticmethod
    @transaction.atomic
    def create_invoice(user, subscription, plan, amount,
                       billing_cycle=UserSubscription.BillingCycle.MONTHLY,
                       status=Invoice.Status.PAID,
                       payment_provider="", payment_reference=""):
        count = Invoice.objects.filter(user=user).count() + 1
        invoice_number = f"INV-{user.id:04d}-{count:04d}"

        now = timezone.now()
        cycle_days = 365 if billing_cycle == UserSubscription.BillingCycle.YEARLY else 30

        invoice = Invoice.objects.create(
            user=user,
            subscription=subscription,
            plan=plan,
            amount=amount,
            currency="USD",
            status=status,
            invoice_number=invoice_number,
            payment_provider=payment_provider,
            payment_reference=payment_reference,
            billing_cycle=billing_cycle,
            period_start=now,
            period_end=now + timedelta(days=cycle_days),
            paid_at=now if status == Invoice.Status.PAID else None,
        )
        return invoice

    @staticmethod
    def get_invoice_by_number(invoice_number):
        try:
            return Invoice.objects.get(invoice_number=invoice_number)
        except Invoice.DoesNotExist:
            return None

    @staticmethod
    def get_invoice_summary(user):
        return Invoice.objects.filter(user=user).aggregate(
            total_paid=Sum("amount", filter=Q(status=Invoice.Status.PAID)),
            total_pending=Sum("amount", filter=Q(status=Invoice.Status.PENDING)),
            invoice_count=Count("id"),
        )


class CouponRepository:
    """Data access for coupons."""

    @staticmethod
    def get_coupon_by_code(code):
        try:
            return Coupon.objects.get(code__iexact=code, is_active=True)
        except Coupon.DoesNotExist:
            return None

    @staticmethod
    def validate_coupon(coupon, user):
        if not coupon.is_valid:
            return False, "Coupon has expired or been exhausted"

        if coupon.usage_limit > 0 and coupon.used_count >= coupon.usage_limit:
            return False, "Coupon usage limit has been reached"

        user_usage = UserSubscription.objects.filter(
            coupon=coupon, user=user,
        ).count()
        if user_usage >= coupon.max_uses_per_user:
            return False, "You have already used this coupon"

        return True, "Coupon is valid"

    @staticmethod
    @transaction.atomic
    def apply_coupon(coupon):
        Coupon.objects.filter(id=coupon.id).update(used_count=F("used_count") + 1)

    @staticmethod
    def calculate_discounted_price(price, coupon):
        if coupon.discount_type == Coupon.DiscountType.PERCENTAGE:
            discount = price * (coupon.discount_value / 100)
            return max(price - discount, 0)
        return max(price - coupon.discount_value, 0)



