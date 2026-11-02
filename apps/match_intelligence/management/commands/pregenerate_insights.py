from django.core.management.base import BaseCommand

from apps.match_intelligence.models import MatchInsight
from apps.match_intelligence.services import MatchIntelligenceService
from apps.matching.models import MatchScore


class Command(BaseCommand):
    help = "Generate AI match explanations ahead of time, since each takes up to a minute on CPU."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=10, help="Number of top matches to process")
        parser.add_argument("--force", action="store_true", help="Replace explanations that already exist")

    def handle(self, *args, limit, force, **options):
        matches = MatchScore.objects.select_related("startup", "investor").order_by("-score")[:limit]
        for match in matches:
            if force:
                MatchInsight.objects.filter(match=match).delete()
            insight = MatchIntelligenceService.generate_match_explanation(match)
            self.stdout.write(f"{match.startup.name} / {match.investor.email}: {insight.summary[:80]}")
