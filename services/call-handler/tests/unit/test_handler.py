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
    def test_new_session_returns_greeting(self, mock_repo_cls: MagicMock) -> None:
        mock_repo = MagicMock()
        mock_repo.get.return_value = None
        mock_repo_cls.return_value = mock_repo

        result = handler(_make_connect_event(), _FakeContext())

        assert result["action"] == "continue"
        assert "reservation" in result["response"].lower()
        mock_repo.save.assert_called_once()

    @pytest.mark.unit
    @patch("call_handler.api.handler.DynamoDBSessionRepository")
    def test_existing_session_loaded(self, mock_repo_cls: MagicMock) -> None:
        existing = ConversationSession(
            session_id="test-contact-001",
            tenant_id="restaurant-001",
            caller_phone="+15551234567",
        )
        existing.add_turn("assistant", "Hello!")

        mock_repo = MagicMock()
        mock_repo.get.return_value = existing
        mock_repo_cls.return_value = mock_repo

        result = handler(_make_connect_event(), _FakeContext())

        assert result["action"] == "continue"
        mock_repo.save.assert_called_once()

    @pytest.mark.unit
    @patch("call_handler.api.handler.DynamoDBSessionRepository")
    def test_user_input_added_to_session(self, mock_repo_cls: MagicMock) -> None:
        mock_repo = MagicMock()
        mock_repo.get.return_value = None
        mock_repo_cls.return_value = mock_repo

        handler(
            _make_connect_event(user_input="I want to make a reservation"),
            _FakeContext(),
        )

        saved: ConversationSession = mock_repo.save.call_args[0][0]
        user_turns = [t for t in saved.turn_history if t.role == "user"]
        assert len(user_turns) == 1
        assert "reservation" in user_turns[0].content.lower()

    @pytest.mark.unit
    @patch("call_handler.api.handler.DynamoDBSessionRepository")
    def test_session_attributes_returned(self, mock_repo_cls: MagicMock) -> None:
        mock_repo = MagicMock()
        mock_repo.get.return_value = None
        mock_repo_cls.return_value = mock_repo

        result = handler(
            _make_connect_event(contact_id="abc-123", tenant_id="t1"),
            _FakeContext(),
        )

        assert result["sessionAttributes"]["session_id"] == "abc-123"
        assert result["sessionAttributes"]["tenant_id"] == "t1"

    @pytest.mark.unit
    def test_invalid_event_returns_transfer(self) -> None:
        result = handler({"bad": "event"}, _FakeContext())
        assert result["action"] == "transfer"

    @pytest.mark.unit
    @patch("call_handler.api.handler.DynamoDBSessionRepository")
    def test_empty_user_input_not_added_as_turn(self, mock_repo_cls: MagicMock) -> None:
        mock_repo = MagicMock()
        mock_repo.get.return_value = None
        mock_repo_cls.return_value = mock_repo

        handler(_make_connect_event(user_input=""), _FakeContext())

        saved: ConversationSession = mock_repo.save.call_args[0][0]
        user_turns = [t for t in saved.turn_history if t.role == "user"]
        assert len(user_turns) == 0
