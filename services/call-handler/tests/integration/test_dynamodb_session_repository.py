"""Integration tests for DynamoDBSessionRepository using moto."""

from __future__ import annotations

import os

import boto3
import pytest
from moto import mock_aws

from call_handler.domain.models import (
    ConversationIntent,
    ConversationSession,
    SessionStatus,
)
from call_handler.infrastructure.dynamodb_session_repository import (
    DynamoDBSessionRepository,
)

TABLE_NAME = "hospitality-ai-test-table"


def _create_table(dynamodb_resource) -> None:
    """Create the single global table with the correct key schema."""
    dynamodb_resource.create_table(
        TableName=TABLE_NAME,
        KeySchema=[
            {"AttributeName": "PK", "KeyType": "HASH"},
            {"AttributeName": "SK", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "PK", "AttributeType": "S"},
            {"AttributeName": "SK", "AttributeType": "S"},
            {"AttributeName": "GSI1PK", "AttributeType": "S"},
            {"AttributeName": "GSI1SK", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "GSI1",
                "KeySchema": [
                    {"AttributeName": "GSI1PK", "KeyType": "HASH"},
                    {"AttributeName": "GSI1SK", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )


@pytest.fixture(autouse=True)
def aws_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DYNAMODB_TABLE_NAME", TABLE_NAME)
    monkeypatch.setenv("AWS_DEFAULT_REGION", "eu-central-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("XRAY_ENABLED", "false")


@pytest.fixture()
def repo() -> DynamoDBSessionRepository:
    """Return a repository backed by a moto-mocked DynamoDB table."""
    # Clear lru_cache so moto intercepts fresh boto3 clients
    from hospitality_shared.infrastructure.aws.clients import (
        get_dynamodb_resource,
    )
    get_dynamodb_resource.cache_clear()

    with mock_aws():
        resource = boto3.resource("dynamodb", region_name="eu-central-1")
        _create_table(resource)
        yield DynamoDBSessionRepository()


def _make_session(session_id: str = "sess-001") -> ConversationSession:
    return ConversationSession(
        session_id=session_id,
        tenant_id="restaurant-001",
        caller_phone="+15551234567",
    )


class TestDynamoDBSessionRepository:
    @pytest.mark.integration
    def test_save_and_get_roundtrip(self, repo: DynamoDBSessionRepository) -> None:
        session = _make_session()
        session.add_turn("user", "I want a table for two")
        session.add_turn("assistant", "Sure, what date?")
        session.update_intent(ConversationIntent.MAKE_RESERVATION)
        session.update_slot("party_size", 2)

        repo.save(session)
        loaded = repo.get("sess-001")

        assert loaded is not None
        assert loaded.session_id == "sess-001"
        assert loaded.tenant_id == "restaurant-001"
        assert loaded.intent == ConversationIntent.MAKE_RESERVATION
        assert loaded.slots["party_size"] == 2
        assert len(loaded.turn_history) == 2
        assert loaded.turn_history[0].role == "user"
        assert loaded.turn_history[1].role == "assistant"

    @pytest.mark.integration
    def test_get_nonexistent_returns_none(self, repo: DynamoDBSessionRepository) -> None:
        result = repo.get("does-not-exist")
        assert result is None

    @pytest.mark.integration
    def test_save_overwrites_existing(self, repo: DynamoDBSessionRepository) -> None:
        session = _make_session()
        repo.save(session)

        session.update_intent(ConversationIntent.FAQ)
        session.add_turn("user", "What time do you open?")
        repo.save(session)

        loaded = repo.get("sess-001")
        assert loaded is not None
        assert loaded.intent == ConversationIntent.FAQ
        assert len(loaded.turn_history) == 1

    @pytest.mark.integration
    def test_delete_removes_session(self, repo: DynamoDBSessionRepository) -> None:
        session = _make_session()
        repo.save(session)
        assert repo.get("sess-001") is not None

        repo.delete("sess-001")
        assert repo.get("sess-001") is None

    @pytest.mark.integration
    def test_session_status_persisted(self, repo: DynamoDBSessionRepository) -> None:
        session = _make_session()
        session.transfer()
        repo.save(session)

        loaded = repo.get("sess-001")
        assert loaded is not None
        assert loaded.status == SessionStatus.TRANSFERRED

    @pytest.mark.integration
    def test_ttl_field_set(self, repo: DynamoDBSessionRepository) -> None:
        import time
        session = _make_session()
        repo.save(session)

        # Read raw item to check TTL was written
        resource = boto3.resource("dynamodb", region_name="eu-central-1")
        table = resource.Table(TABLE_NAME)
        item = table.get_item(
            Key={"PK": "SESSION#sess-001", "SK": "SESSION#sess-001"}
        )["Item"]

        assert "ttl" in item
        assert int(item["ttl"]) > int(time.time())
