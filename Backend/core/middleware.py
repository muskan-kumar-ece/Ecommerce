"""
Request-ID middleware.

Attaches a unique ``X-Request-ID`` header to every HTTP response so that
individual requests can be traced across log lines, Sentry events, and
downstream service calls.

If the incoming request already carries a ``X-Request-ID`` header (e.g. from
a load-balancer or a frontend that generated the ID), that value is reused.
Otherwise a new UUID4 is generated.

The ID is also stored in the Python ``logging`` context via
``logging.LoggerAdapter`` so that all log lines emitted during a request
automatically include it.

Usage
-----
Add to ``MIDDLEWARE`` **as early as possible** (right after
``SecurityMiddleware``) in ``settings/base.py``:

    MIDDLEWARE = [
        "django.middleware.security.SecurityMiddleware",
        "core.middleware.RequestIDMiddleware",  # ← add here
        ...
    ]
"""

import logging
import uuid

logger = logging.getLogger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"
REQUEST_ID_META_KEY = "HTTP_X_REQUEST_ID"


class RequestIDMiddleware:
    """Assign and propagate a unique request identifier for every HTTP request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.META.get(REQUEST_ID_META_KEY) or str(uuid.uuid4())
        request.request_id = request_id

        response = self.get_response(request)
        response[REQUEST_ID_HEADER] = request_id
        return response
