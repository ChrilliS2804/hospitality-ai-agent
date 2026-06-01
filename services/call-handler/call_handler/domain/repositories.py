"""Repository interface for ConversationSession."""

from __future__ import annotations

from abc import ABC, abstractmethod

from call_handler.domain.models import ConversationSession


class ISessionRepository(ABC):
    """Port (interface) for session persistence.

    The infrastructure layer provides the DynamoDB implementation.
    The domain layer has no knowledge of DynamoDB.
    """

    @abstractmethod
    def get(self, session_id: str) -> ConversationSession | None:
        """Retrieve a session by ID. Returns None if not found."""

    @abstractmethod
    def save(self, session: ConversationSession) -> None:
        """Persist a session (create or update)."""

    @abstractmethod
    def delete(self, session_id: str) -> None:
        """Delete a session (used for cleanup)."""
