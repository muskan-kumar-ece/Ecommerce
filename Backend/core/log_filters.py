"""
Logging utilities for the Ecommerce backend.

This module provides two things:

1. ``RequestIDFilter`` — injects the current ``X-Request-ID`` into every log
   record so that all log lines produced during a request can be correlated.
   The ID is stored in thread-local storage by ``RequestIDMiddleware`` and
   falls back to ``"-"`` outside request context (management commands, etc.).

2. ``JsonFormatter`` — optional structured JSON log formatter, activated when
   ``LOG_FORMAT=json`` is set in the environment.  Each log line is a single
   JSON object with a fixed set of fields, suitable for ingestion by log
   aggregation platforms (CloudWatch, Datadog, Loki, etc.).

Usage (settings/base.py)
------------------------
LOGGING = {
    "filters": {
        "request_id": {
            "()": "core.log_filters.RequestIDFilter",
        },
    },
    "formatters": {
        "verbose": {
            "format": "%(asctime)s %(levelname)s [%(request_id)s] %(name)s %(message)s",
        },
        "json": {
            "()": "core.log_filters.JsonFormatter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json" if LOG_FORMAT == "json" else "verbose",
            "filters": ["request_id"],
        }
    },
}
"""

import json
import logging
import threading
import traceback

_local = threading.local()


# ---------------------------------------------------------------------------
# Thread-local helpers
# ---------------------------------------------------------------------------


def set_request_id(request_id: str) -> None:
    """Store *request_id* in thread-local storage for the current request."""
    _local.request_id = request_id


def get_request_id() -> str:
    """Return the request ID for the current thread, or ``"-"`` if unset."""
    return getattr(_local, "request_id", "-")


# ---------------------------------------------------------------------------
# Logging filter
# ---------------------------------------------------------------------------


class RequestIDFilter(logging.Filter):
    """Logging filter that injects ``request_id`` into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003 – required by logging.Filter interface
        record.request_id = get_request_id()
        return True


# ---------------------------------------------------------------------------
# JSON formatter
# ---------------------------------------------------------------------------


class JsonFormatter(logging.Formatter):
    """
    Emit one JSON object per log line.

    Output schema
    -------------
    {
        "timestamp":  "2026-03-08T06:00:00.123456+00:00",
        "level":      "ERROR",
        "request_id": "b1c2d3e4-...",
        "logger":     "payments.services",
        "message":    "Razorpay create-order API call failed ...",
        "exc_info":   "Traceback (most recent call last): ..."  // only when an exception is attached
    }

    The ``request_id`` field is populated by ``RequestIDFilter`` which must
    be listed in the handler's ``filters`` list alongside this formatter.
    If the filter is absent the field defaults to ``"-"``.
    """

    def format(self, record: logging.LogRecord) -> str:
        from datetime import datetime, timezone as dt_timezone
        payload: dict = {
            "timestamp": datetime.fromtimestamp(record.created, tz=dt_timezone.utc).isoformat(timespec="microseconds"),
            "level": record.levelname,
            "request_id": getattr(record, "request_id", "-"),
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = "".join(traceback.format_exception(*record.exc_info)).rstrip()
        return json.dumps(payload, ensure_ascii=False)
