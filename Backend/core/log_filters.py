"""
Logging filters for the Ecommerce backend.

``RequestIDFilter`` injects the current request's ``X-Request-ID`` into
every log record so that all log lines produced during a request can be
correlated by their shared ID.  The ID is taken from threading-local
storage that ``RequestIDMiddleware`` writes to on each request.

When logging happens outside a request context (management commands, Celery
tasks, tests) the ``request_id`` attribute defaults to ``"-"``.

Usage (settings/base.py)
------------------------
LOGGING = {
    "filters": {
        "request_id": {
            "()": "core.log_filters.RequestIDFilter",
        },
    },
    "handlers": {
        "console": {
            ...
            "filters": ["request_id"],
        }
    },
    "formatters": {
        "verbose": {
            "format": "%(asctime)s %(levelname)s [%(request_id)s] %(name)s %(message)s",
        },
    },
}
"""

import logging
import threading

_local = threading.local()


def set_request_id(request_id: str) -> None:
    """Store *request_id* in thread-local storage for the current request."""
    _local.request_id = request_id


def get_request_id() -> str:
    """Return the request ID for the current thread, or ``"-"`` if unset."""
    return getattr(_local, "request_id", "-")


class RequestIDFilter(logging.Filter):
    """Logging filter that injects ``request_id`` into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003 – required by logging.Filter interface
        record.request_id = get_request_id()
        return True
