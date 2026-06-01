"""Unit tests for the structured logger."""

import json
import pytest

from hospitality_shared.infrastructure.logging.logger import StructuredLogger, get_logger


class TestStructuredLogger:
    @pytest.mark.unit
    def test_info_emits_json(self, capsys: pytest.CaptureFixture[str]) -> None:
        logger = StructuredLogger("test-service")
        logger.info("hello world")
        captured = capsys.readouterr()
        record = json.loads(captured.out.strip())
        assert record["level"] == "INFO"
        assert record["message"] == "hello world"
        assert record["service"] == "test-service"

    @pytest.mark.unit
    def test_extra_fields_included(self, capsys: pytest.CaptureFixture[str]) -> None:
        logger = StructuredLogger("test-service")
        logger.info("test", session_id="abc123", tenant_id="t1")
        captured = capsys.readouterr()
        record = json.loads(captured.out.strip())
        assert record["session_id"] == "abc123"
        assert record["tenant_id"] == "t1"

    @pytest.mark.unit
    def test_phone_number_masked(self, capsys: pytest.CaptureFixture[str]) -> None:
        logger = StructuredLogger("test-service")
        logger.info("caller is +15551234567")
        captured = capsys.readouterr()
        record = json.loads(captured.out.strip())
        assert "+15551234567" not in record["message"]
        assert "***" in record["message"]

    @pytest.mark.unit
    def test_email_masked(self, capsys: pytest.CaptureFixture[str]) -> None:
        logger = StructuredLogger("test-service")
        logger.info("email is john@example.com")
        captured = capsys.readouterr()
        record = json.loads(captured.out.strip())
        assert "john@example.com" not in record["message"]

    @pytest.mark.unit
    def test_bind_adds_persistent_context(self, capsys: pytest.CaptureFixture[str]) -> None:
        logger = StructuredLogger("test-service")
        logger.bind(tenant_id="restaurant-001")
        logger.info("bound context test")
        captured = capsys.readouterr()
        record = json.loads(captured.out.strip())
        assert record["tenant_id"] == "restaurant-001"

    @pytest.mark.unit
    def test_get_logger_returns_same_instance(self) -> None:
        a = get_logger("my-service")
        b = get_logger("my-service")
        assert a is b
