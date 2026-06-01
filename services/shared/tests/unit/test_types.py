"""Unit tests for shared domain value types."""

import pytest

from hospitality_shared.domain.types import Email, PhoneNumber, TenantId


class TestPhoneNumber:
    @pytest.mark.unit
    def test_valid_phone_normalises(self) -> None:
        phone = PhoneNumber("+1 (555) 123-4567")
        assert phone.value == "+15551234567"

    @pytest.mark.unit
    def test_valid_phone_no_plus(self) -> None:
        phone = PhoneNumber("15551234567")
        assert phone.value == "15551234567"

    @pytest.mark.unit
    def test_invalid_phone_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid phone number"):
            PhoneNumber("not-a-phone")

    @pytest.mark.unit
    def test_masked_returns_last_four(self) -> None:
        phone = PhoneNumber("+15551234567")
        assert phone.masked() == "***-***-4567"

    @pytest.mark.unit
    def test_str_returns_value(self) -> None:
        phone = PhoneNumber("+15551234567")
        assert str(phone) == "+15551234567"

    @pytest.mark.unit
    def test_frozen_immutable(self) -> None:
        phone = PhoneNumber("+15551234567")
        with pytest.raises(Exception):
            phone.value = "changed"  # type: ignore[misc]


class TestEmail:
    @pytest.mark.unit
    def test_valid_email_normalises_lowercase(self) -> None:
        email = Email("User@Example.COM")
        assert email.value == "user@example.com"

    @pytest.mark.unit
    def test_invalid_email_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid email"):
            Email("not-an-email")

    @pytest.mark.unit
    def test_masked_hides_local_part(self) -> None:
        email = Email("john.doe@example.com")
        assert "***" in email.masked()
        assert "@" in email.masked()

    @pytest.mark.unit
    def test_str_returns_value(self) -> None:
        email = Email("test@example.com")
        assert str(email) == "test@example.com"


class TestTenantId:
    @pytest.mark.unit
    def test_valid_tenant_id_normalises(self) -> None:
        tid = TenantId("  Restaurant-001  ")
        assert tid.value == "restaurant-001"

    @pytest.mark.unit
    def test_empty_tenant_id_raises(self) -> None:
        with pytest.raises(ValueError, match="cannot be empty"):
            TenantId("")

    @pytest.mark.unit
    def test_whitespace_only_raises(self) -> None:
        with pytest.raises(ValueError, match="cannot be empty"):
            TenantId("   ")
