"""
AI Provider Abstraction for match intelligence.

Current: RuleBasedProvider generates explanations from score_breakdown.
Future: Swap provider via MATCH_AI_PROVIDER setting without changing service code.

Usage in settings:
    MATCH_AI_PROVIDER = "apps.match_intelligence.providers.RuleBasedProvider"
    # Future:
    # MATCH_AI_PROVIDER = "apps.match_intelligence.providers.OpenAIProvider"
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class MatchExplanation:
    summary: str
    strengths: list
    risks: list
    recommendations: list


class BaseMatchAIProvider(ABC):
    """Abstract base for match explanation providers."""

    WEIGHT_LABELS = {
        "industry": "Industry Alignment",
        "stage": "Stage Compatibility",
        "funding": "Funding Match",
        "geography": "Geography Match",
        "keywords": "Keyword Relevance",
        "startup_completeness": "Startup Profile Quality",
        "investor_completeness": "Investor Profile Quality",
        "startup_activity": "Startup Engagement",
        "investor_activity": "Investor Engagement",
    }

    @abstractmethod
    def generate_explanation(self, match) -> MatchExplanation:
        ...


class RuleBasedProvider(BaseMatchAIProvider):
    """Rule-based explanation engine using score_breakdown data."""

    THRESHOLD_HIGH = 70.0
    THRESHOLD_MEDIUM = 40.0

    def generate_explanation(self, match) -> MatchExplanation:
        breakdown = match.score_breakdown or {}
        weights = self._get_weights()

        strengths = self._compute_strengths(breakdown, weights)
        risks = self._compute_risks(breakdown, weights)
        summary = self._compute_summary(match, breakdown, strengths, risks)
        recommendations = self._compute_recommendations(
            match, breakdown, strengths, risks,
        )

        return MatchExplanation(
            summary=summary,
            strengths=strengths,
            risks=risks,
            recommendations=recommendations,
        )

    def _get_weights(self):
        from django.conf import settings
        return getattr(settings, "MATCHING_WEIGHTS", {
            "industry": 30, "stage": 15, "funding": 15,
            "geography": 10, "keywords": 10,
            "startup_completeness": 5, "investor_completeness": 5,
            "startup_activity": 5, "investor_activity": 5,
        })

    def _score_contribution(self, raw_score, weight):
        return (raw_score / 100.0) * weight

    def _compute_strengths(self, breakdown, weights):
        strengths = []
        for key, raw in breakdown.items():
            contribution = self._score_contribution(raw, weights.get(key, 0))
            if raw >= self.THRESHOLD_HIGH and contribution >= 3:
                label = self.WEIGHT_LABELS.get(key, key)
                strengths.append({
                    "factor": key,
                    "label": label,
                    "score": raw,
                    "weight": weights.get(key, 0),
                    "contribution": round(contribution, 1),
                    "description": self._strength_description(key, raw),
                })
        strengths.sort(key=lambda s: s["contribution"], reverse=True)
        return strengths

    def _strength_description(self, key, score):
        descriptions = {
            "industry": "Strong industry alignment between investor preferences and startup focus",
            "stage": "Investor's preferred stage matches the startup's current stage",
            "funding": "Funding requirements align with investor's ticket size range",
            "geography": "Geographic preferences align — same or nearby region",
            "keywords": "High keyword relevance in investment focus and startup description",
            "startup_completeness": "Startup has a well-filled profile with comprehensive information",
            "investor_completeness": "Investor has a complete profile with detailed preferences",
            "startup_activity": "Startup has regular platform engagement and recent activity",
            "investor_activity": "Investor is actively engaged on the platform",
        }
        return descriptions.get(key, f"Strong {key} match ({score}/100)")

    def _compute_risks(self, breakdown, weights):
        risks = []
        for key, raw in breakdown.items():
            contribution = self._score_contribution(raw, weights.get(key, 0))
            if raw < self.THRESHOLD_MEDIUM and weights.get(key, 0) >= 5:
                label = self.WEIGHT_LABELS.get(key, key)
                risks.append({
                    "factor": key,
                    "label": label,
                    "score": raw,
                    "weight": weights.get(key, 0),
                    "impact": round(weights.get(key, 0) - contribution, 1),
                    "description": self._risk_description(key, raw),
                })
        risks.sort(key=lambda r: r["impact"], reverse=True)

        if not risks and breakdown.get("startup_completeness", 100) < 30:
            risks.append({
                "factor": "startup_completeness",
                "label": "Startup Profile Quality",
                "score": breakdown.get("startup_completeness", 0),
                "weight": weights.get("startup_completeness", 5),
                "impact": 5.0,
                "description": "Startup profile is sparse — investors may not have enough information",
            })

        return risks

    def _risk_description(self, key, score):
        descriptions = {
            "stage": "Startup stage may not match investor's preferred investment stage",
            "geography": "Geographic distance may be a concern for hands-on investors",
            "funding": "Funding amount may be outside the investor's typical ticket size",
            "startup_completeness": "Incomplete startup profile may reduce investor confidence",
            "investor_completeness": "Limited investor profile information available",
            "keywords": "Limited keyword overlap in focus areas and descriptions",
            "industry": "Industry may not align with investor's core focus areas",
            "startup_activity": "Low startup platform activity — may indicate reduced engagement",
            "investor_activity": "Low investor platform activity — may respond slowly",
        }
        return descriptions.get(key, f"Below-average {key} score ({score}/100)")

    def _compute_summary(self, match, breakdown, strengths, risks):
        total = float(match.score)
        top_strength = strengths[0]["label"] if strengths else "general fit"
        top_risk = risks[0]["label"] if risks else None

        if total >= 80:
            base = f"Strong match ({total:.0f}/100) — excellent alignment on {top_strength.lower()}"
        elif total >= 60:
            base = f"Good match ({total:.0f}/100) — solid {top_strength.lower()} with room for improvement"
        elif total >= 40:
            base = f"Moderate match ({total:.0f}/100) — some alignment on {top_strength.lower()}"
        else:
            base = f"Low match ({total:.0f}/100) — limited alignment across key factors"

        if top_risk:
            base += f". Main concern: {top_risk.lower()}"

        return base

    def _compute_recommendations(self, match, breakdown, strengths, risks):
        recommendations = []
        risk_factors = {r["factor"] for r in risks}
        user = getattr(match, "investor", None) or getattr(match, "startup", None)

        if "startup_completeness" in risk_factors:
            recommendations.append({
                "target": "founder",
                "action": "Complete your startup profile",
                "detail": "Add your pitch deck, traction metrics, and team information to attract investors",
                "priority": "high",
            })

        if "industry" in risk_factors:
            recommendations.append({
                "target": "founder",
                "action": "Clarify your industry focus",
                "detail": "Update your startup industry to match searchable categories",
                "priority": "medium",
            })

        has_document_risk = any(
            r["factor"] in ("startup_completeness", "startup_activity")
            for r in risks
        )
        if has_document_risk:
            recommendations.append({
                "target": "founder",
                "action": "Upload supporting documents",
                "detail": "Add your pitch deck, financials, and traction reports to the data room",
                "priority": "medium",
            })

        recommendations.append({
            "for": "both",
            "action": "Schedule an intro call",
            "detail": "A quick 15-minute intro call can help both sides explore the opportunity",
            "priority": "high",
        })

        if "startup_completeness" not in risk_factors:
            recommendations.append({
                "target": "investor",
                "action": "Review traction metrics",
                "detail": "Request data room access to review detailed traction and financial metrics",
                "priority": "medium",
            })

        recommendations.append({
            "for": "founder",
            "action": "Send a personalized message",
            "detail": "Highlight key achievements and why you're seeking this investor specifically",
            "priority": "medium",
        })

        if "geography" in risk_factors:
            recommendations.append({
                "target": "both",
                "action": "Discuss remote collaboration",
                "detail": "Clarify remote work expectations and communication cadence upfront",
                "priority": "low",
            })

        return recommendations


class OpenAIProvider(BaseMatchAIProvider):
    """LLM-powered explanation provider (future).

    Configure via:
        MATCH_AI_PROVIDER = "apps.match_intelligence.providers.OpenAIProvider"
        OPENAI_API_KEY = ...

    The provider will send score_breakdown + profile data to GPT-4
    and return a structured MatchExplanation.
    """

    def generate_explanation(self, match) -> MatchExplanation:
        raise NotImplementedError("OpenAI provider not yet implemented")


class GeminiProvider(BaseMatchAIProvider):
    """Gemini-powered explanation provider (future placeholder)."""

    def generate_explanation(self, match) -> MatchExplanation:
        raise NotImplementedError("Gemini provider not yet implemented")
