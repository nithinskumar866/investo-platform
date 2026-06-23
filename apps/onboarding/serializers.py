from rest_framework import serializers

from .models import (
    OnboardingWizard,
    OnboardingStep,
    FounderOnboardingData,
    InvestorOnboardingData,
)


class OnboardingStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnboardingStep
        fields = "__all__"
        read_only_fields = ["id", "wizard"]


class OnboardingWizardSerializer(serializers.ModelSerializer):
    steps = OnboardingStepSerializer(many=True, read_only=True)

    class Meta:
        model = OnboardingWizard
        fields = "__all__"
        read_only_fields = ["id", "user", "started_at", "updated_at"]


class FounderOnboardingSerializer(serializers.ModelSerializer):
    class Meta:
        model = FounderOnboardingData
        fields = "__all__"
        read_only_fields = ["id", "user"]


class InvestorOnboardingSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvestorOnboardingData
        fields = "__all__"
        read_only_fields = ["id", "user"]


class OnboardingProgressSerializer(serializers.Serializer):
    total_steps = serializers.IntegerField()
    completed_steps = serializers.IntegerField()
    current_step = serializers.CharField()
    is_complete = serializers.BooleanField()
    steps = serializers.ListField(child=serializers.DictField())


class StartOnboardingSerializer(serializers.Serializer):
    wizard_type = serializers.ChoiceField(choices=["founder", "investor"])
