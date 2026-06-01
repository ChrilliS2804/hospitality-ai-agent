"""Lambda middleware — wraps handlers with logging, tracing, and error handling.

Usage::

    from hospitality_shared.application.middleware import lambda_handler_middleware

    @lambda_handler_middleware(service="call-handler")
    def handler(event: dict, context: object) -> dict:
        ...
"""

from __future__ import annotations

import functools
import os
import time
from typing import Any, Callable

from hospitality_shared.domain.exceptions import HospitalityBaseError
from hospitality_shared.infrastructure.logging.logger import get_logger


def lambda_handler_middleware(service: str) -> Callable[..., Any]:
    """Decorator factory that wraps a Lambda handler with cross-cutting concerns.

    Adds:
    - Structured logging with request/response metadata
    - X-Ray trace ID binding
    - Execution duration logging
    - Standardised error handling and response formatting
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(event: dict[str, Any], context: Any) -> dict[str, Any]:
            logger = get_logger(service)
            start = time.monotonic()

            # Bind Lambda context to logger
            aws_request_id = getattr(context, "aws_request_id", "local")
            logger.bind(aws_request_id=aws_request_id)

            # Bind X-Ray trace ID if present
            trace_id = os.environ.get("_X_AMZN_TRACE_ID", "")
            if trace_id:
                logger.bind(trace_id=trace_id)

            logger.info("Lambda invocation started", event_keys=list(event.keys()))

            try:
                result = func(event, context)
                duration_ms = int((time.monotonic() - start) * 1000)
                logger.info("Lambda invocation completed", duration_ms=duration_ms)
                return result  # type: ignore[no-any-return]

            except HospitalityBaseError as exc:
                duration_ms = int((time.monotonic() - start) * 1000)
                logger.error(
                    "Domain error in Lambda handler",
                    error_code=exc.code,
                    error_message=exc.message,
                    duration_ms=duration_ms,
                )
                return {
                    "statusCode": 400,
                    "error": exc.code,
                    "message": exc.message,
                }

            except Exception as exc:  # noqa: BLE001
                duration_ms = int((time.monotonic() - start) * 1000)
                logger.error(
                    "Unhandled exception in Lambda handler",
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                    duration_ms=duration_ms,
                )
                return {
                    "statusCode": 500,
                    "error": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred.",
                }

        return wrapper

    return decorator
