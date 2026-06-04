"""Call Handler Lambda — entry point for Amazon Connect invocations.

Sprint 2: Multi-turn conversation powered by Bedrock Claude.
Each invocation = one conversational turn. Connect loops back on each
caller utterance, enabling natural back-and-forth dialogue.
"""

from __future__ import annotations

import os
from typing import Any

from pydantic import ValidationError

from call_handler.api.schemas import ConnectEvent, ConnectResponse
from call_handler.application.conversation_engine import ConversationEngine
from call_handler.domain.models import ConversationSession, SessionStatus
from call_handler.infrastructure.dynamodb_session_repository import (
    DynamoDBSessionRepository,
)
from hospitality_shared.application.middleware import lambda_handler_middleware
from hospitality_shared.infrastructure.logging.logger import get_logger

logger = get_logger("call-handler")

_ERROR_RESPONSE = (
    "Es tut mir leid, es gibt gerade ein technisches Problem. "
    "Bitte rufen Sie später noch einmal an."
)

_GREETING = (
    "Hallo, vielen Dank für Ihren Anruf. Ich bin Ihr KI-Assistent. "
    "Ich kann Ihnen helfen, eine Reservierung vorzunehmen, zu ändern "
    "oder zu stornieren, oder Fragen zu unserem Restaurant beantworten. "
    "Wie kann ich Ihnen helfen?"
)


@lambda_handler_middleware(service="call-handler")
def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Main Lambda handler invoked by Amazon Connect.

    Drives one turn of the multi-turn conversation:
    1. Parse Connect event
    2. Load or create session
    3. If first turn with no input → return greeting
    4. Otherwise → call Bedrock via ConversationEngine
    5. Save session and return response
    """
    # Parse and validate the Connect event
    try:
        connect_event = ConnectEvent(**event)
    except ValidationError as exc:
        logger.error("Invalid Connect event structure", validation_errors=str(exc))
        return ConnectResponse(response=_ERROR_RESPONSE, action="end").to_dict()

    session_id = connect_event.session_id
    tenant_id = connect_event.tenant_id
    caller_phone = connect_event.contact_data.caller_phone
    user_input = connect_event.user_input

    logger.bind(session_id=session_id, tenant_id=tenant_id)
    logger.info("Inbound call turn", caller_phone=caller_phone, has_input=bool(user_input))

    repo = DynamoDBSessionRepository()

    # Load or create session
    session = repo.get(session_id)
    is_new_session = session is None

    if session is None:
        session = ConversationSession(
            session_id=session_id,
            tenant_id=tenant_id,
            caller_phone=caller_phone,
        )
        logger.info("New session created")

    # If session is already completed or transferred, return a closing message
    if session.status in (SessionStatus.COMPLETED, SessionStatus.TRANSFERRED):
        response_text = "Vielen Dank für Ihren Anruf. Auf Wiederhören!"
        repo.save(session)
        return ConnectResponse(response=response_text, action="end").to_dict()

    # First turn with no user input → return greeting
    if is_new_session and not user_input:
        response_text = _GREETING
        session.add_turn("assistant", response_text)
        repo.save(session)
        logger.info("Returning greeting (first turn)")
        return ConnectResponse(response=response_text, action="continue").to_dict()

    # Process turn through conversation engine (Bedrock)
    try:
        engine = ConversationEngine()
        response_text = engine.process_turn(session, user_input)
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "Conversation engine error",
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
        response_text = (
            "Entschuldigung, ich habe gerade ein Problem. "
            "Kann ich Ihnen anders helfen?"
        )
        session.add_turn("assistant", response_text)

    # Determine action based on session status
    action = "continue"
    if session.status == SessionStatus.COMPLETED:
        action = "end"
    elif session.status == SessionStatus.TRANSFERRED:
        action = "transfer"

    repo.save(session)

    logger.info(
        "Returning response",
        action=action,
        intent=session.intent.value,
        turn_count=session.turn_count,
    )

    return ConnectResponse(response=response_text, action=action).to_dict()
