import logging
import time

from django.conf import settings
from django.core.cache import cache
from django.db import connection, OperationalError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """
    Lightweight health endpoint used by load balancers and uptime monitors.

    Probes every configured dependency and returns HTTP 200 when all are
    healthy, HTTP 503 when any dependency is degraded.

    Response schema
    ---------------
    {
        "status": "ok" | "error",
        "checks": {
            "database": "ok" | "error: <reason>",
            "cache":    "ok" | "error: <reason>" | "skipped"
        },
        "response_time_ms": <float>
    }
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        start = time.monotonic()
        checks = {}
        http_status = 200

        # --- Database ---
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            checks["database"] = "ok"
        except OperationalError as exc:
            checks["database"] = f"error: {exc}"
            http_status = 503
            logger.error("Health check: database probe failed: %s", exc)

        # --- Cache (Redis when configured, skipped otherwise) ---
        cache_redis_url = getattr(settings, "CACHE_REDIS_URL", "")
        if cache_redis_url:
            try:
                cache.set("health_probe", "1", timeout=5)
                if cache.get("health_probe") != "1":
                    raise RuntimeError("cache round-trip returned unexpected value")
                checks["cache"] = "ok"
            except Exception as exc:  # noqa: BLE001
                checks["cache"] = f"error: {exc}"
                http_status = 503
                logger.error("Health check: cache probe failed: %s", exc)
        else:
            checks["cache"] = "skipped"

        elapsed_ms = round((time.monotonic() - start) * 1000, 2)
        all_ok = all(v in ("ok", "skipped") for v in checks.values())

        return Response(
            {
                "status": "ok" if all_ok else "error",
                "checks": checks,
                "response_time_ms": elapsed_ms,
            },
            status=http_status,
        )
