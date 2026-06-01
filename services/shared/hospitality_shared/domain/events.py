"""Base domain event types shared across all services."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    tenant_id: str = ""

    @property
    def event_type(self) -> str:
        """Return the event type name (class name by default)."""
        return self.__class__.__name__

    def to_dict(self) -> dict[str, object]:
        """Serialise event to a plain dict for EventBridge."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at,
            "tenant_id": self.tenant_id,
        }
