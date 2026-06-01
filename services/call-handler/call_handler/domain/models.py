"""Call handler domain models — ConversationSession aggregate."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class ConversationIntent(str, Enum):
    MAKE_RESERVATION = "MAKE_RESERVATION"
    CANCEL_RESERVATION = "CANCEL_RESERVATION"
    MODIFY_RESERVATION = "MODIFY_RESERVATION"
    FAQ = "FAQ"
    HUMAN_HANDOFF = "HUMAN_HANDOFF"
    UNKNOWN = "UNKNOWN"


class SessionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    TRANSFERRED = "TRANSFERRED"
    ABANDONED = "ABANDONED"


@dataclass
class ConversationTurn:
    role: str          # "user" | "assistant"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class ConversationSession:
    """Aggregate root for a single phone call conversation."""

    session_id: str                          # Amazon Connect Contact ID
    tenant_id: str
    caller_phone: str
    intent: ConversationIntent = ConversationIntent.UNKNOWN
    slots: dict[str, Any] = field(default_factory=dict)
    turn_history: list[ConversationTurn] = field(default_factory=list)
    status: SessionStatus = SessionStatus.ACTIVE
    reservation_id: str | None = None
    summary: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def add_turn(self, role: str, content: str) -> None:
        """Append a conversation turn and update the timestamp."""
        self.turn_history.append(ConversationTurn(role=role, content=content))
        self.updated_at = datetime.now(UTC).isoformat()

    def update_intent(self, intent: ConversationIntent) -> None:
        self.intent = intent
        self.updated_at = datetime.now(UTC).isoformat()

    def update_slot(self, key: str, value: Any) -> None:
        self.slots[key] = value
        self.updated_at = datetime.now(UTC).isoformat()

    def complete(self, summary: str | None = None) -> None:
        self.status = SessionStatus.COMPLETED
        self.summary = summary
        self.updated_at = datetime.now(UTC).isoformat()

    def transfer(self) -> None:
        self.status = SessionStatus.TRANSFERRED
        self.updated_at = datetime.now(UTC).isoformat()

    @property
    def turn_count(self) -> int:
        return len(self.turn_history)
