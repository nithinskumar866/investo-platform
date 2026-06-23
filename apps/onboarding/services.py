import logging
from django.utils import timezone

from .models import (
    OnboardingWizard,
    OnboardingStep,
    FounderOnboardingData,
    InvestorOnboardingData,
)

logger = logging.getLogger(__name__)

FOUNDER_STEPS = [
    ("company_info", "Company Information"),
    ("business_model", "Business Model"),
    ("traction", "Traction & Competitors"),
    ("pitch_deck", "Pitch Deck"),
    ("review", "Review & Complete"),
]

INVESTOR_STEPS = [
    ("profile", "Profile & Bio"),
    ("focus", "Investment Focus"),
    ("ticket", "Ticket Size & Geography"),
    ("experience", "Experience"),
    ("review", "Review & Complete"),
]


class OnboardingService:

    @staticmethod
    def start_onboarding(user, wizard_type):
        wizard, created = OnboardingWizard.objects.get_or_create(
            user=user,
            defaults={
                "wizard_type": wizard_type,
                "current_step": wizard_type,
            },
        )
        if not created:
            wizard.wizard_type = wizard_type
            wizard.is_complete = False
            wizard.save()

        wizard.steps.all().delete()

        steps = FOUNDER_STEPS if wizard_type == "founder" else INVESTOR_STEPS
        for i, (key, label) in enumerate(steps):
            OnboardingStep.objects.create(
                wizard=wizard,
                step_key=key,
                step_label=label,
            )

        wizard.current_step = steps[0][0]
        wizard.save()

        return wizard

    @staticmethod
    def get_wizard(user):
        return OnboardingWizard.objects.filter(user=user).first()

    @staticmethod
    def get_progress(user):
        wizard = OnboardingService.get_wizard(user)
        if not wizard:
            return None

        steps_qs = wizard.steps.all().order_by("id")
        total = steps_qs.count()
        completed = steps_qs.filter(is_completed=True).count()

        return {
            "total_steps": total,
            "completed_steps": completed,
            "current_step": wizard.current_step,
            "is_complete": wizard.is_complete,
            "steps": [
                {
                    "step_key": s.step_key,
                    "step_label": s.step_label,
                    "is_completed": s.is_completed,
                    "completed_at": s.completed_at.isoformat() if s.completed_at else None,
                }
                for s in steps_qs
            ],
        }

    @staticmethod
    def complete_step(user, step_key, data):
        wizard = OnboardingService.get_wizard(user)
        if not wizard:
            return None

        step = wizard.steps.filter(step_key=step_key).first()
        if not step:
            return None

        step.data = data
        step.is_completed = True
        step.completed_at = timezone.now()
        step.save()

        steps = wizard.steps.all().order_by("id")
        next_step = steps.filter(is_completed=False).first()
        if next_step:
            wizard.current_step = next_step.step_key
        else:
            wizard.current_step = step_key
        wizard.save()

        return OnboardingService.get_progress(user)

    @staticmethod
    def complete_onboarding(user):
        wizard = OnboardingService.get_wizard(user)
        if not wizard:
            return None

        wizard.is_complete = True
        wizard.save()

        if wizard.wizard_type == "founder":
            data_obj, _ = FounderOnboardingData.objects.get_or_create(user=user)
        else:
            data_obj, _ = InvestorOnboardingData.objects.get_or_create(user=user)

        return wizard

    @staticmethod
    def get_founder_data(user):
        data, _ = FounderOnboardingData.objects.get_or_create(user=user)
        return data

    @staticmethod
    def get_investor_data(user):
        data, _ = InvestorOnboardingData.objects.get_or_create(user=user)
        return data
