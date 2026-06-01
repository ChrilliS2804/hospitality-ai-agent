"""X-Ray tracing helpers.

Wraps aws_xray_sdk with graceful fallback when X-Ray is not available
(e.g. local unit tests). Active tracing is enabled via Lambda environment
variable XRAY_ENABLED=true.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Generator


def _xray_enabled() -> bool:
    return os.environ.get("XRAY_ENABLED", "false").lower() == "true"


def get_tracer() -> Any:
    """Return the X-Ray recorder if tracing is enabled, else a no-op stub."""
    if _xray_enabled():
        try:
            from aws_xray_sdk.core import xray_recorder  # type: ignore[import-untyped]
            return xray_recorder
        except ImportError:
            pass
    return _NoOpTracer()


@contextmanager
def traced_subsegment(name: str, **annotations: str) -> Generator[Any, None, None]:
    """Context manager that creates an X-Ray subsegment if tracing is enabled."""
    if _xray_enabled():
        try:
            from aws_xray_sdk.core import xray_recorder  # type: ignore[import-untyped]
            with xray_recorder.in_subsegment(name) as subsegment:
                for key, value in annotations.items():
                    subsegment.put_annotation(key, value)
                yield subsegment
            return
        except Exception:  # noqa: BLE001
            pass
    yield None


class _NoOpTracer:
    """No-op tracer used when X-Ray is disabled or unavailable."""

    def put_annotation(self, *_: Any, **__: Any) -> None:
        pass

    def put_metadata(self, *_: Any, **__: Any) -> None:
        pass

    def begin_subsegment(self, *_: Any, **__: Any) -> "_NoOpTracer":
        return self

    def end_subsegment(self) -> None:
        pass

    def __enter__(self) -> "_NoOpTracer":
        return self

    def __exit__(self, *_: Any) -> None:
        pass
