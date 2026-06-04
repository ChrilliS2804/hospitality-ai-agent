"""Unit tests for the conversation engine — mocked Bedrock."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from call_handler.application.conversation_engine import ConversationEngine
from call_handler.domain.models import (
    ConversationIntent,
    ConversationSession,
    SessionStatus,
)


def _make_session() -> ConversationSession:
    return ConversationSession(
        session_id="test-session",
        tenant_id="restaurant-001",
        caller_phone="+4915112345678",
    )


def _mock_bedrock_response(content: str) -> dict:
    return {
        "content": content,
        "input_tokens": 500,
        "output_tokens": 100,
        "stop_reason": "end_turn",
    }


class TestConversationEngine:
    @pytest.mark.unit
    @patch("call_handler.application.conversation_engine.BedrockConversationClient")
    def test_first_turn_reservation_intent(self, mock_bedrock_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.converse.return_value = _mock_bedrock_response(
            '{"intent": "MAKE_RESERVATION", "slots": {"date": null, "time": null, '
            '"party_size": null, "guest_name": null, "phone": null, "reference_number": null}, '
            '"response_text": "Gerne! Für welches Datum?", '
            '"next_action": "continue", "slots_complete": false}'
        )
        mock_client.parse_structured_response = (
            ConversationEngine.__new__(ConversationEngine)
        )
        # Use the real parse method
        from call_handler.infrastructure.bedrock_client import BedrockConversationClient as RealClient
        mock_client.parse_structured_response = RealClient().parse_structured_response
        mock_bedrock_cls.return_value = mock_client

        session = _make_session()
        engine = ConversationEngine()
        response = engine.process_turn(session, "Ich möchte einen Tisch reservieren")

        assert response == "Gerne! Für welches Datum?"
        assert session.intent == ConversationIntent.MAKE_RESERVATION
        assert session.status == SessionStatus.ACTIVE

    @pytest.mark.unit
    @patch("call_handler.application.conversation_engine.BedrockConversationClient")
    def test_slot_filling_date_and_time(self, mock_bedrock_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.converse.return_value = _mock_bedrock_response(
            '{"intent": "MAKE_RESERVATION", "slots": {"date": "2026-06-07", "time": "19:00", '
            '"party_size": 4, "guest_name": null, "phone": null, "reference_number": null}, '
            '"response_text": "Samstag 19 Uhr für 4 Personen. Auf welchen Namen?", '
            '"next_action": "continue", "slots_complete": false}'
        )
        from call_handler.infrastructure.bedrock_client import BedrockConversationClient as RealClient
        mock_client.parse_structured_response = RealClient().parse_structured_response
        mock_bedrock_cls.return_value = mock_client

        session = _make_session()
        session.update_intent(ConversationIntent.MAKE_RESERVATION)
        engine = ConversationEngine()
        response = engine.process_turn(session, "Diesen Samstag um 19 Uhr für 4 Personen")

        assert session.slots.get("date") == "2026-06-07"
        assert session.slots.get("time") == "19:00"
        assert session.slots.get("party_size") == 4
        assert "Namen" in response

    @pytest.mark.unit
    @patch("call_handler.application.conversation_engine.BedrockConversationClient")
    def test_confirm_action_keeps_session_active(self, mock_bedrock_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.converse.return_value = _mock_bedrock_response(
            '{"intent": "MAKE_RESERVATION", "slots": {"date": "2026-06-07", "time": "19:00", '
            '"party_size": 4, "guest_name": "Schmid", "phone": null, "reference_number": null}, '
            '"response_text": "Reservierung für 4 Personen am Samstag um 19 Uhr auf Schmid. Stimmt das?", '
            '"next_action": "confirm", "slots_complete": true}'
        )
        from call_handler.infrastructure.bedrock_client import BedrockConversationClient as RealClient
        mock_client.parse_structured_response = RealClient().parse_structured_response
        mock_bedrock_cls.return_value = mock_client

        session = _make_session()
        engine = ConversationEngine()
        engine.process_turn(session, "Schmid")

        assert session.slots.get("guest_name") == "Schmid"
        assert session.status == SessionStatus.ACTIVE  # Not yet completed

    @pytest.mark.unit
    @patch("call_handler.application.conversation_engine.BedrockConversationClient")
    def test_complete_action_marks_session_completed(self, mock_bedrock_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.converse.return_value = _mock_bedrock_response(
            '{"intent": "MAKE_RESERVATION", "slots": {"date": "2026-06-07", "time": "19:00", '
            '"party_size": 4, "guest_name": "Schmid", "phone": null, "reference_number": null}, '
            '"response_text": "Ihre Reservierung ist bestätigt. Auf Wiederhören!", '
            '"next_action": "complete", "slots_complete": true}'
        )
        from call_handler.infrastructure.bedrock_client import BedrockConversationClient as RealClient
        mock_client.parse_structured_response = RealClient().parse_structured_response
        mock_bedrock_cls.return_value = mock_client

        session = _make_session()
        engine = ConversationEngine()
        engine.process_turn(session, "Ja, genau")

        assert session.status == SessionStatus.COMPLETED

    @pytest.mark.unit
    @patch("call_handler.application.conversation_engine.BedrockConversationClient")
    def test_handoff_action_marks_session_transferred(self, mock_bedrock_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.converse.return_value = _mock_bedrock_response(
            '{"intent": "HUMAN_HANDOFF", "slots": {}, '
            '"response_text": "Ich verbinde Sie mit einem Mitarbeiter.", '
            '"next_action": "handoff", "slots_complete": false}'
        )
        from call_handler.infrastructure.bedrock_client import BedrockConversationClient as RealClient
        mock_client.parse_structured_response = RealClient().parse_structured_response
        mock_bedrock_cls.return_value = mock_client

        session = _make_session()
        engine = ConversationEngine()
        engine.process_turn(session, "Ich möchte mit einem Menschen sprechen")

        assert session.intent == ConversationIntent.HUMAN_HANDOFF
        assert session.status == SessionStatus.TRANSFERRED

    @pytest.mark.unit
    @patch("call_handler.application.conversation_engine.BedrockConversationClient")
    def test_unparseable_response_returns_fallback(self, mock_bedrock_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.converse.return_value = _mock_bedrock_response(
            "Ich bin nicht sicher, was Sie meinen."
        )
        from call_handler.infrastructure.bedrock_client import BedrockConversationClient as RealClient
        mock_client.parse_structured_response = RealClient().parse_structured_response
        mock_bedrock_cls.return_value = mock_client

        session = _make_session()
        engine = ConversationEngine()
        response = engine.process_turn(session, "blah blah blah")

        # Should use the raw text as response
        assert "nicht sicher" in response

    @pytest.mark.unit
    @patch("call_handler.application.conversation_engine.BedrockConversationClient")
    def test_slots_merge_not_overwrite_with_null(self, mock_bedrock_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.converse.return_value = _mock_bedrock_response(
            '{"intent": "MAKE_RESERVATION", "slots": {"date": "2026-06-07", "time": null, '
            '"party_size": null, "guest_name": null, "phone": null, "reference_number": null}, '
            '"response_text": "Für welche Uhrzeit?", '
            '"next_action": "continue", "slots_complete": false}'
        )
        from call_handler.infrastructure.bedrock_client import BedrockConversationClient as RealClient
        mock_client.parse_structured_response = RealClient().parse_structured_response
        mock_bedrock_cls.return_value = mock_client

        session = _make_session()
        session.update_slot("party_size", 4)  # Pre-existing slot
        engine = ConversationEngine()
        engine.process_turn(session, "Am Samstag")

        # party_size should still be 4, not overwritten
        assert session.slots["party_size"] == 4
        assert session.slots["date"] == "2026-06-07"
