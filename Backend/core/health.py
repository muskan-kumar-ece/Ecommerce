import time

from django.db import connection, OperationalError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """
    Lightweight health endpoint used by load balancers and uptime monitors.

    Returns HTTP 200 when the application and its critical dependencies (database)
    are reachable, and HTTP 503 when any dependency is down.

    Example response (healthy):
        {
            "status": "ok",
            "checks": {
                "database": "ok"
            },
            "response_time_ms": 4.2
        }

    Example response (unhealthy):
        {
            "status": "error",
            "checks": {
                "database": "error: could not connect"
            },
            "response_time_ms": 15.1
        }
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        start = time.monotonic()
        checks = {}
        http_status = 200

        # Database check
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            checks["database"] = "ok"
        except OperationalError as exc:
            checks["database"] = f"error: {exc}"
            http_status = 503

        elapsed_ms = round((time.monotonic() - start) * 1000, 2)
        all_ok = all(v == "ok" for v in checks.values())

        return Response(
            {
                "status": "ok" if all_ok else "error",
                "checks": checks,
                "response_time_ms": elapsed_ms,
            },
            status=http_status,
        )
