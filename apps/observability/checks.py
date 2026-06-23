import logging

from django.conf import settings
from django.core.cache import cache
from django.db import connections
from django.db.utils import OperationalError

logger = logging.getLogger(__name__)


class HealthCheckService:
    """Runs health checks on all platform dependencies."""

    @staticmethod
    def check_all():
        return {
            "database": HealthCheckService.check_database(),
            "redis_cache": HealthCheckService.check_redis(),
            "storage": HealthCheckService.check_storage(),
            "celery": HealthCheckService.check_celery(),
        }

    @staticmethod
    def check_database():
        try:
            connections["default"].cursor().execute("SELECT 1")
            return {"status": "healthy", "detail": "PostgreSQL responding"}
        except OperationalError as e:
            return {"status": "unhealthy", "detail": str(e)}
        except Exception as e:
            return {"status": "unhealthy", "detail": str(e)}

    @staticmethod
    def check_redis():
        try:
            cache.set("__healthcheck__", "ok", timeout=5)
            value = cache.get("__healthcheck__")
            if value == "ok":
                return {"status": "healthy", "detail": "Redis responding"}
            return {"status": "degraded", "detail": "Redis set/get mismatch"}
        except Exception as e:
            return {"status": "unhealthy", "detail": str(e)}

    @staticmethod
    def check_storage():
        from django.core.files.storage import default_storage
        try:
            test_path = "__healthcheck__test.txt"
            default_storage.save(test_path, ContentFile("ok"))
            default_storage.delete(test_path)
            return {"status": "healthy", "detail": "Storage responding"}
        except Exception as e:
            return {"status": "unhealthy", "detail": str(e)}

    @staticmethod
    def check_celery():
        try:
            from celery.app.control import Inspect
            from config.celery import app as celery_app
            inspect = Inspect(app=celery_app)
            workers = inspect.ping()
            if workers:
                return {"status": "healthy", "detail": f"{len(workers)} worker(s) responding"}
            return {"status": "degraded", "detail": "No Celery workers found"}
        except Exception as e:
            return {"status": "unhealthy", "detail": str(e)}

    @staticmethod
    def check_channel_layer():
        try:
            from channels.layers import get_channel_layer
            layer = get_channel_layer()
            if layer:
                return {"status": "healthy", "detail": "Channel layer responding"}
            return {"status": "degraded", "detail": "Channel layer not configured"}
        except Exception as e:
            return {"status": "unhealthy", "detail": str(e)}


from django.core.files.base import ContentFile
