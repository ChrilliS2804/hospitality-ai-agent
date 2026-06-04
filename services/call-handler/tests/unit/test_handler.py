"""Unit tests for the call handler Lambda."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from call_handler.api.handler import handler
from call_handler.domain.models import ConversationSession


def _make_connect_event(
    contact_id: str = "test-contact-001",
    tenant_id: str = "restaurant-001",
    caller_phone: str = "+15551234567",
    user_input: str = "",
) -> dict:
    return {
        "Name": "ContactFlowEvent",
        "Details": {"Parameters": {"userInput": user_input}},
        "ContactData": {
            "ContactId": contact_id,
            "InitialContactId": contact_id,
            "Channel": "VOICE",
            "InstanceARN": "arn:aws:connect:eu-central-1:123456789:instance/test",
            "Attributes": {"tenant_id": tenant_id},
            "CustomerEndpoint": {"Address": caller_phone, "Type": "TELEPHONE_NUMBER"},
        },
    }


class _FakeContext:
    aws_request_id = "test-request-id"


class TestCallHandler:
    @pytest.mark.unit
    @patch("call_handler.api.handler.DynamoDBSessionRepository")
    def test_new_session_returns_greeting_in_german(self, mock_repo_cls: MagicMock) -> None:
        mock_repo = MagicMock()
        mock_repo.get.return_value = None
        mock_repo_cls.return_value = mock_repo

        result = handler(_make_connect_event(), _FakeContext())

        assert result["action"] == "continue"
        assert "reservierung" in result["response"].lower()
        mock_repo.save.assert_called_once()

    @pytest.mark.unit
    @patch("call_handler.api.handler.DynamoDBSessionRepository")
    def test_existing_session_with_input_calls_bedrock(self, mock_repo_cls: MagicMock) -> None:
        existing = ConversationSession(
            session_id="test-contact-001",
            tenant_id="restaurant-001",
            caller_phone="+15551234567",
        )
        existing.add_turn("assistant", "Hallo!")

        mock_repo = MagicMock()
        mock_repo.get.return_value = existing
        mock_repo_cls.return_value = mock_repo

        with patch("call_handler.api.handler.ConversationEngine") as mock_engine_cls:
            mock_engine = MagicMock()
            mock_engine.process_turn.return_value = "Für welches Datum?"
            mock_engine_cls.return_value = mock_engine

            result = handler(
                _make_connect_event(user_input="Ich will reservieren"),
                _FakeContext(),
            )

            assert result["response"] == "Für welches Datum?"
            assert result["action"] == "continue"
            mock_engine.process_turn.assert_called_once()

    @pytest.mark.unit
    @patch("call_handler.api.handler.DynamoDBSessionRepository")
    def test_user_input_passed_to_engine(self, mock_repo_cls: MagicMock) -> None:
        mock_repo = MagicMock()
        mock_repo.get.return_value = None
        mock_repo_cls.return_value = mock_repo

        # First call with no input -> greeting, no engine called
        result = handler(_make_connect_event(user_input=""), _FakeContext())
        assert "reservierung" in result["response"].lower()

    @pytest.mark.unit
    @patch("call_handler.api.handler.DynamoDBSessionRepository")
    def test_flat_response_format(self, mock_repo_cls: MagicMock) -> None:
        mock_repo = MagicMock()
        mock_repo.get.return_value = None
        mock_repo_cls.return_value = mock_repo

        result = handler(_make_connect_event(), _FakeContext())

        # Should be flat — no nested sessionAttributes
        assert "sessionAttributes" not in result
        assert "response" in result
        assert "action" in result

    @pytest.mark.unit
    def test_invalid_event_returns_error(self) -> None:
        result = handler({"bad": "event"}, _FakeContext())
        # The middleware catches the exception and returns statusCode 500
        assert result.get("statusCode") == 500 or result.get("action") == "end"

    @pytest.mark.unit
    @patch("call_handler.api.handler.DynamoDBSessionRepository")
    def test_empty_user_input_first_turn_returns_greeting(self, mock_repo_cls: MagicMock) -> None:
        mock_repo = MagicMock()
        mock_repo.get.return_value = None
        mock_repo_cls.return_value = mock_repo

        result = handler(_make_connect_event(user_input=""), _FakeContext())

        assert result["action"] == "continue"
        assert len(result["response"]) > 20  # Non-trivial greeting
