"""Call handler domain exceptions."""

from __future__ import annotations

from hospitality_shared.domain.exceptions import HospitalityBaseError


class SessionNotFoundError(HospitalityBaseError):
    def __init__(self, session_id: str) -> None:
        super().__init__(f"Session not found: {session_id}", code="SESSION_NOT_FOUND")
        self.session_id = session_id


class MaxRetriesExceededError(HospitalityBaseError):
    def __init__(self, slot: str) -> None:
        super().__init__(
            f"Max retries exceeded collecting slot: {slot}",
            code="MAX_RETRIES_EXCEEDED",
        )
        self.slot = slot
