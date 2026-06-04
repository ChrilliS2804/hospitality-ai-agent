"""Conversation engine — orchestrates the multi-turn conversation flow.

Responsibilities:
- Loads/creates conversation session from DynamoDB
- Formats conversation history for Bedrock
- Calls Bedrock Claude for NLU + response generation
- Parses structured output (intent, slots, response_text)
- Updates session state
- Returns the response text to speak to the caller
"""

from __future__ import annotations

from typing import Any

from call_handler.domain.models import (
    ConversationIntent,
    ConversationSession,
)
from call_handler.domain.prompts import MAX_HISTORY_TURNS, RESTAURANT_SYSTEM_PROMPT
from call_handler.infrastructure.bedrock_client import BedrockConversationClient
from hospitality_shared.infrastructure.logging.logger import get_logger

logger = get_logger("call-handler")


class ConversationEngine:
    """Drives a single turn of the multi-turn conversation.

    Each Lambda invocation = one turn. The engine:
    1. Takes the user's input and the existing session
    2. Calls Bedrock with history + new input
    3. Parses the structured response
    4. Updates the session (intent, slots, turn history)
    5. Returns the text to speak back to the caller
    """

    def __init__(self) -> None:
        self._bedrock = BedrockConversationClient()

    def process_turn(
        self,
        session: ConversationSession,
        user_input: str,
    ) -> str:
        """Process one conversational turn.

        Args:
            session: The current conversation session (mutated in place).
            user_input: What the caller said (transcribed by Connect).

        Returns:
            The response text to speak to the caller.
        """
        # Add user turn to history
        if user_input:
            session.add_turn("user", user_input)

        # Build messages array for Bedrock (trim to last N turns)
        messages = self._build_messages(session)

        # If no user input yet (first turn), add a synthetic greeting trigger
        if not messages:
            messages = [{"role": "user", "content": "Hallo"}]

        # Call Bedrock
        logger.info(
            "Calling Bedrock",
            turn_count=session.turn_count,
            message_count=len(messages),
        )

        raw_response = self._bedrock.converse(
            system_prompt=RESTAURANT_SYSTEM_PROMPT,
            messages=messages,
        )

        # Parse structured response
        parsed = self._bedrock.parse_structured_response(raw_response["content"])

        # Update session state
        self._update_session(session, parsed)

        # Extract response text to speak
        response_text = parsed.get("response_text", "")
        if not response_text:
            response_text = "Entschuldigung, können Sie das bitte wiederholen?"

        # Add assistant turn to history
        session.add_turn("assistant", response_text)

        logger.info(
            "Turn processed",
            intent=parsed.get("intent", "UNKNOWN"),
            next_action=parsed.get("next_action", "continue"),
            slots_complete=parsed.get("slots_complete", False),
        )

        return response_text

    def _build_messages(self, session: ConversationSession) -> list[dict[str, str]]:
        """Build the messages array from session history.

        Trims to last MAX_HISTORY_TURNS to control token usage.
        """
        messages: list[dict[str, str]] = []
        history = session.turn_history[-MAX_HISTORY_TURNS:]

        for turn in history:
            messages.append({
                "role": turn.role,
                "content": turn.content,
            })

        return messages

    def _update_session(
        self,
        session: ConversationSession,
        parsed: dict[str, Any],
    ) -> None:
        """Update session intent and slots from parsed Bedrock response."""
        # Update intent
        intent_str = parsed.get("intent", "UNKNOWN")
        try:
            session.update_intent(ConversationIntent(intent_str))
        except ValueError:
            session.update_intent(ConversationIntent.UNKNOWN)

        # Update slots (merge — don't overwrite with null)
        new_slots = parsed.get("slots", {})
        for key, value in new_slots.items():
            if value is not None:
                session.update_slot(key, value)

        # Check if conversation should end
        next_action = parsed.get("next_action", "continue")
        if next_action == "complete":
            session.complete()
        elif next_action == "handoff":
            session.transfer()
