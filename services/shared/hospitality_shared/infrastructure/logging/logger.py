"""Structured JSON logger for Lambda functions.

Emits log records as JSON to stdout (captured by CloudWatch Logs).
PII fields are automatically masked before emission.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from datetime import UTC, datetime
from typing import Any


# PII masking patterns
_PHONE_RE = re.compile(r"\+?\d[\d\s\-\(\)]{7,}\d")
_EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def _mask_pii(value: str) -> str:
    """Mask phone numbers and email addresses in a string."""
    value = _PHONE_RE.sub("***-***-XXXX", value)
    value = _EMAIL_RE.sub(lambda m: f"{m.group()[:2]}***@***.***", value)
    return value


class StructuredLogger:
    """Emits structured JSON log records to stdout.

    Usage::

        logger = get_logger("call-handler")
        logger.info("Session started", session_id="abc", tenant_id="t1")
        logger.error("Bedrock call failed", error=str(exc))
    """

    def __init__(self, service: str) -> None:
        self._service = service
        self._context: dict[str, Any] = {}

    def bind(self, **context: Any) -> None:
        """Attach persistent context fields to all subsequent log records."""
        self._context.update(context)

    def _emit(self, level: str, message: str, **fields: Any) -> None:
        record: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": level,
            "service": self._service,
            "message": _mask_pii(str(message)),
            **self._context,
            **fields,
        }
        # Mask any PII that slipped into string field values
        sanitised = {
            k: _mask_pii(str(v)) if isinstance(v, str) else v
            for k, v in record.items()
        }
        print(json.dumps(sanitised), file=sys.stdout, flush=True)  # noqa: T201

    def debug(self, message: str, **fields: Any) -> None:
        if os.environ.get("LOG_LEVEL", "INFO").upper() == "DEBUG":
            self._emit("DEBUG", message, **fields)

    def info(self, message: str, **fields: Any) -> None:
        self._emit("INFO", message, **fields)

    def warning(self, message: str, **fields: Any) -> None:
        self._emit("WARNING", message, **fields)

    def error(self, message: str, **fields: Any) -> None:
        self._emit("ERROR", message, **fields)

    def critical(self, message: str, **fields: Any) -> None:
        self._emit("CRITICAL", message, **fields)


# Module-level cache so each service gets one logger instance
_loggers: dict[str, StructuredLogger] = {}


def get_logger(service: str) -> StructuredLogger:
    """Return (or create) a StructuredLogger for the given service name."""
    if service not in _loggers:
        _loggers[service] = StructuredLogger(service)
    return _loggers[service]


# Suppress noisy boto3 / botocore debug logs in Lambda
logging.getLogger("boto3").setLevel(logging.WARNING)
logging.getLogger("botocore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
