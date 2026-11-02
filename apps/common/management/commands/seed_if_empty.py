import runpy

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Load demo data on a fresh database, so a restart never overwrites it."

    def handle(self, *args, **options):
        if get_user_model().objects.exists():
            self.stdout.write("Database already has users; skipping seed.")
            return
        runpy.run_path(str(settings.BASE_DIR / "seed_data.py"))
