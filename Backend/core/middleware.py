"""
Request-ID middleware.

Attaches a unique ``X-Request-ID`` header to every HTTP response so that
individual requests can be traced across log lines, Sentry events, and
downstream service calls.

If the incoming request already carries a ``X-Request-ID`` header (e.g. from
a load-balancer or a frontend that generated the ID), that value is reused.
Otherwise a new UUID4 is generated.

The ID is also written into thread-local storage via ``core.log_filters`` so
that every ``logging`` call made during the request automatically includes the
ID in formatted log lines (requires ``RequestIDFilter`` to be wired into
``LOGGING`` — see ``settings/base.py``).
"""

import logging
import uuid

from .log_filters import set_request_id

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

        # Propagate to thread-local so logging filter can read it.
        set_request_id(request_id)

        response = self.get_response(request)
        response[REQUEST_ID_HEADER] = request_id
        return response
