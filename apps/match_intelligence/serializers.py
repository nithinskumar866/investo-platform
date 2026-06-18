from rest_framework import serializers

from .models import MatchInsight, MatchFeedback


class StrengthSerializer(serializers.Serializer):
    factor = serializers.CharField()
    label = serializers.CharField()
    score = serializers.FloatField()
    weight = serializers.IntegerField()
    contribution = serializers.FloatField()
    description = serializers.CharField()


class RiskSerializer(serializers.Serializer):
    factor = serializers.CharField()
    label = serializers.CharField()
    score = serializers.FloatField()
    weight = serializers.IntegerField()
    impact = serializers.FloatField()
    description = serializers.CharField()


class RecommendationSerializer(serializers.Serializer):
    target = serializers.CharField()
    action = serializers.CharField()
    detail = serializers.CharField()
    priority = serializers.CharField()


class MatchInsightSerializer(serializers.ModelSerializer):
    match_id = serializers.IntegerField(read_only=True)
    strengths = StrengthSerializer(many=True)
    risks = RiskSerializer(many=True)
    recommendations = RecommendationSerializer(many=True)

    class Meta:
        model = MatchInsight
        fields = [
            "id", "match_id", "summary",
            "strengths", "risks", "recommendations",
            "generated_at",
        ]


class MatchFeedbackSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = MatchFeedback
        fields = ["id", "user", "user_email", "match", "rating", "feedback", "created_at"]
        read_only_fields = ["user", "created_at"]


class SubmitFeedbackSerializer(serializers.Serializer):
    match_id = serializers.IntegerField()
    rating = serializers.ChoiceField(choices=[1, 2, 3, 4, 5])
    feedback = serializers.CharField(required=False, allow_blank=True, default="")


class PatternAnalyticsSerializer(serializers.Serializer):
    most_common_mismatches = serializers.ListField()
    top_converting_patterns = serializers.ListField()


class InsightAnalyticsSerializer(serializers.Serializer):
    total_insights_generated = serializers.IntegerField()
    total_feedback_submitted = serializers.IntegerField()
    average_rating = serializers.FloatField(allow_null=True)
    rating_distribution = serializers.ListField()
    feedback_rate = serializers.FloatField()
