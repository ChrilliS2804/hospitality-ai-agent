"""Call Handler Lambda — entry point for Amazon Connect and Lex V2 invocations.

Sprint 2: Multi-turn conversation powered by Bedrock Claude.

This Lambda is invoked in two ways:
1. Directly by Connect Contact Flow (first turn — greeting)
2. By Lex V2 FallbackIntent fulfillment (subsequent turns — speech transcribed)

The handler detects the event source and routes accordingly.
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
    "Bitte rufen Sie spaeter noch einmal an."
)

_GREETING = (
    "Hallo, vielen Dank fuer Ihren Anruf. Ich bin Ihr KI-Assistent. "
    "Ich kann Ihnen helfen, eine Reservierung vorzunehmen, zu aendern "
    "oder zu stornieren, oder Fragen zu unserem Restaurant beantworten. "
    "Wie kann ich Ihnen helfen?"
)


def _is_lex_event(event: dict[str, Any]) -> bool:
    """Detect if this is a Lex V2 fulfillment event."""
    return "sessionState" in event and "inputTranscript" in event


def _handle_lex_event(event: dict[str, Any]) -> dict[str, Any]:
    """Handle a Lex V2 FallbackIntent fulfillment event.

    Lex V2 event structure:
    {
        "sessionId": "...",
        "inputTranscript": "what the caller said",
        "sessionState": {
            "intent": {"name": "FallbackIntent", ...},
            "sessionAttributes": {...}
        },
        ...
    }

    Returns Lex V2 response format with dialogAction + messages.
    """
    session_id = event.get("sessionId", "unknown")
    user_input = event.get("inputTranscript", "")
    session_attrs = event.get("sessionState", {}).get("sessionAttributes", {})
    tenant_id = session_attrs.get("tenant_id", "default")

    logger.bind(session_id=session_id, tenant_id=tenant_id)
    logger.info("Lex fulfillment turn", has_input=bool(user_input))

    repo = DynamoDBSessionRepository()

    # Load or create session
    session = repo.get(session_id)
    if session is None:
        caller_phone = session_attrs.get("caller_phone", "")
        session = ConversationSession(
            session_id=session_id,
            tenant_id=tenant_id,
            caller_phone=caller_phone,
        )
        logger.info("New session created from Lex event")

    # If completed/transferred, close the conversation
    if session.status in (SessionStatus.COMPLETED, SessionStatus.TRANSFERRED):
        response_text = "Vielen Dank fuer Ihren Anruf. Auf Wiederhoeren!"
        return _lex_close_response(event, response_text, session_attrs)

    # Process turn through conversation engine
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
            "Koennen Sie das bitte wiederholen?"
        )
        session.add_turn("assistant", response_text)

    repo.save(session)

    # Determine if we should close or elicit more input
    if session.status in (SessionStatus.COMPLETED, SessionStatus.TRANSFERRED):
        return _lex_close_response(event, response_text, session_attrs)

    return _lex_elicit_response(event, response_text, session_attrs)


def _lex_elicit_response(
    event: dict[str, Any],
    message: str,
    session_attrs: dict[str, str],
) -> dict[str, Any]:
    """Return Lex response that speaks the message and waits for more input."""
    return {
        "sessionState": {
            "dialogAction": {
                "type": "ElicitIntent",
            },
            "intent": {
                "name": "FallbackIntent",
                "state": "InProgress",
            },
            "sessionAttributes": session_attrs,
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": message,
            }
        ],
    }


def _lex_close_response(
    event: dict[str, Any],
    message: str,
    session_attrs: dict[str, str],
) -> dict[str, Any]:
    """Return Lex response that speaks the message and ends the conversation."""
    return {
        "sessionState": {
            "dialogAction": {
                "type": "Close",
            },
            "intent": {
                "name": "FallbackIntent",
                "state": "Fulfilled",
            },
            "sessionAttributes": session_attrs,
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": message,
            }
        ],
    }


@lambda_handler_middleware(service="call-handler")
def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Main Lambda handler — routes between Connect direct and Lex V2 events."""

    # Route based on event source
    if _is_lex_event(event):
        return _handle_lex_event(event)

    # Connect direct invocation (first turn / greeting)
    try:
        connect_event = ConnectEvent(**event)
    except ValidationError as exc:
        logger.error("Invalid event structure", validation_errors=str(exc))
        return ConnectResponse(response=_ERROR_RESPONSE, action="end").to_dict()

    session_id = connect_event.session_id
    tenant_id = connect_event.tenant_id
    caller_phone = connect_event.contact_data.caller_phone
    user_input = connect_event.user_input

    logger.bind(session_id=session_id, tenant_id=tenant_id)
    logger.info("Connect direct turn", caller_phone=caller_phone, has_input=bool(user_input))

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

    # If session is already completed or transferred
    if session.status in (SessionStatus.COMPLETED, SessionStatus.TRANSFERRED):
        response_text = "Vielen Dank fuer Ihren Anruf. Auf Wiederhoeren!"
        repo.save(session)
        return ConnectResponse(response=response_text, action="end").to_dict()

    # First turn with no user input — return greeting
    if is_new_session and not user_input:
        response_text = _GREETING
        session.add_turn("assistant", response_text)
        repo.save(session)
        logger.info("Returning greeting (first turn)")
        return ConnectResponse(response=response_text, action="continue").to_dict()

    # If Connect passes user input directly (without Lex), process it
    if user_input:
        try:
            engine = ConversationEngine()
            response_text = engine.process_turn(session, user_input)
        except Exception as exc:  # noqa: BLE001
            logger.error("Conversation engine error", error_message=str(exc))
            response_text = "Entschuldigung, koennen Sie das bitte wiederholen?"
            session.add_turn("assistant", response_text)
    else:
        response_text = _GREETING

    action = "continue"
    if session.status == SessionStatus.COMPLETED:
        action = "end"
    elif session.status == SessionStatus.TRANSFERRED:
        action = "transfer"

    repo.save(session)
    return ConnectResponse(response=response_text, action=action).to_dict()
