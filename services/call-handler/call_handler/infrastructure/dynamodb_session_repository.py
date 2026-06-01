"""DynamoDB implementation of ISessionRepository.

Single global table: hospitality-{environment}
Session key pattern:
  PK = SESSION#{session_id}
  SK = SESSION#{session_id}
"""

from __future__ import annotations

import json
import os
import time
from typing import Any

from botocore.exceptions import ClientError

from call_handler.domain.models import (
    ConversationIntent,
    ConversationSession,
    ConversationTurn,
    SessionStatus,
)
from call_handler.domain.repositories import ISessionRepository
from hospitality_shared.domain.exceptions import InfrastructureError
from hospitality_shared.infrastructure.aws.clients import get_dynamodb_resource
from hospitality_shared.infrastructure.logging.logger import get_logger

logger = get_logger("call-handler")

_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", "hospitality-dev")
_SESSION_TTL_SECONDS = int(os.environ.get("SESSION_TTL_SECONDS", str(24 * 60 * 60)))


class DynamoDBSessionRepository(ISessionRepository):
    """Persists ConversationSession to the single global DynamoDB table."""

    def __init__(self) -> None:
        self._table = get_dynamodb_resource().Table(_TABLE_NAME)

    def get(self, session_id: str) -> ConversationSession | None:
        try:
            response = self._table.get_item(
                Key={
                    "PK": f"SESSION#{session_id}",
                    "SK": f"SESSION#{session_id}",
                }
            )
        except ClientError as exc:
            raise InfrastructureError(
                f"DynamoDB get_item failed for session {session_id}",
                cause=exc,
            ) from exc

        item = response.get("Item")
        if not item:
            return None
        return self._deserialise(item)

    def save(self, session: ConversationSession) -> None:
        item = self._serialise(session)
        try:
            self._table.put_item(Item=item)
        except ClientError as exc:
            raise InfrastructureError(
                f"DynamoDB put_item failed for session {session.session_id}",
                cause=exc,
            ) from exc
        logger.debug("Session saved", session_id=session.session_id)

    def delete(self, session_id: str) -> None:
        try:
            self._table.delete_item(
                Key={
                    "PK": f"SESSION#{session_id}",
                    "SK": f"SESSION#{session_id}",
                }
            )
        except ClientError as exc:
            raise InfrastructureError(
                f"DynamoDB delete_item failed for session {session_id}",
                cause=exc,
            ) from exc

    # ── Serialisation ──────────────────────────────────────────────────────

    def _serialise(self, session: ConversationSession) -> dict[str, Any]:
        ttl = int(time.time()) + _SESSION_TTL_SECONDS
        return {
            "PK": f"SESSION#{session.session_id}",
            "SK": f"SESSION#{session.session_id}",
            "GSI1PK": f"TENANT#{session.tenant_id}#SESSION",
            "GSI1SK": f"CREATED#{session.created_at}",
            "entity_type": "SESSION",
            "session_id": session.session_id,
            "tenant_id": session.tenant_id,
            "caller_phone": session.caller_phone,
            "intent": session.intent.value,
            "slots": session.slots,
            "turn_history": [
                {"role": t.role, "content": t.content, "timestamp": t.timestamp}
                for t in session.turn_history
            ],
            "status": session.status.value,
            "reservation_id": session.reservation_id,
            "summary": session.summary,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "ttl": ttl,
        }

    def _deserialise(self, item: dict[str, Any]) -> ConversationSession:
        turns = [
            ConversationTurn(
                role=t["role"],
                content=t["content"],
                timestamp=t.get("timestamp", ""),
            )
            for t in item.get("turn_history", [])
        ]
        return ConversationSession(
            session_id=item["session_id"],
            tenant_id=item["tenant_id"],
            caller_phone=item["caller_phone"],
            intent=ConversationIntent(item.get("intent", "UNKNOWN")),
            slots=item.get("slots", {}),
            turn_history=turns,
            status=SessionStatus(item.get("status", "ACTIVE")),
            reservation_id=item.get("reservation_id"),
            summary=item.get("summary"),
            created_at=item["created_at"],
            updated_at=item["updated_at"],
        )
