"""Call Handler Lambda — entry point for Amazon Connect invocations.

Sprint 1 scope: greeting response to validate the Connect → Lambda integration.
Sprint 2 will add Bedrock NLU and multi-turn conversation logic.

Amazon Connect Contact Flow invokes this Lambda synchronously and expects
a JSON response within ~8 seconds.
"""

from __future__ import annotations

import os
from typing import Any

from pydantic import ValidationError

from call_handler.api.schemas import ConnectEvent, ConnectResponse
from call_handler.infrastructure.dynamodb_session_repository import (
    DynamoDBSessionRepository,
)
from call_handler.domain.models import ConversationSession
from hospitality_shared.application.middleware import lambda_handler_middleware
from hospitality_shared.infrastructure.logging.logger import get_logger

logger = get_logger("call-handler")

_GREETING = (
    "Hallo, vielen Dank für Ihren Anruf. Ich bin Ihr KI-Assistent. "
    "Ich kann Ihnen helfen, eine Reservierung vorzunehmen, zu ändern "
    "oder zu stornieren, oder Fragen zu unserem Restaurant beantworten. "
    "Wie kann ich Ihnen helfen?"
)

_ERROR_RESPONSE = (
    "Es tut mir leid, es gibt gerade ein technisches Problem. "
    "Bitte rufen Sie später noch einmal an."
)


@lambda_handler_middleware(service="call-handler")
def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Main Lambda handler invoked by Amazon Connect.

    Sprint 1: Validates the Connect integration by returning a greeting.
    The session is created and persisted to DynamoDB on first contact.
    """
    # Parse and validate the Connect event
    try:
        connect_event = ConnectEvent(**event)
    except ValidationError as exc:
        logger.error("Invalid Connect event structure", validation_errors=str(exc))
        return ConnectResponse(response=_ERROR_RESPONSE, action="transfer").to_dict()

    session_id = connect_event.session_id
    tenant_id = connect_event.tenant_id
    caller_phone = connect_event.contact_data.caller_phone

    logger.bind(session_id=session_id, tenant_id=tenant_id)
    logger.info("Inbound call received", caller_phone=caller_phone)

    repo = DynamoDBSessionRepository()

    # Load or create session
    session = repo.get(session_id)
    if session is None:
        session = ConversationSession(
            session_id=session_id,
            tenant_id=tenant_id,
            caller_phone=caller_phone,
        )
        logger.info("New session created")
    else:
        logger.info("Existing session loaded", turn_count=session.turn_count)

    # Sprint 1: Return greeting on first turn
    # Sprint 2 will replace this with Bedrock NLU routing
    user_input = connect_event.user_input
    if user_input:
        session.add_turn("user", user_input)

    response_text = _GREETING
    session.add_turn("assistant", response_text)
    repo.save(session)

    logger.info("Returning response to Connect", action="continue")

    return ConnectResponse(
        response=response_text,
        action="continue",
        session_attributes={},
    ).to_dict()
