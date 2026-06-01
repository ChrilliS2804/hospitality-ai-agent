"""Unit tests for shared domain exceptions."""

import pytest

from hospitality_shared.domain.exceptions import (
    ConflictError,
    DomainValidationError,
    EntityNotFoundError,
    InfrastructureError,
    TenantNotFoundError,
)


class TestDomainExceptions:
    @pytest.mark.unit
    def test_domain_validation_error_code(self) -> None:
        exc = DomainValidationError("bad input")
        assert exc.code == "DOMAIN_VALIDATION_ERROR"
        assert "bad input" in str(exc)

    @pytest.mark.unit
    def test_entity_not_found_message(self) -> None:
        exc = EntityNotFoundError("Reservation", "RES-001")
        assert exc.entity_type == "Reservation"
        assert exc.identifier == "RES-001"
        assert exc.code == "ENTITY_NOT_FOUND"

    @pytest.mark.unit
    def test_conflict_error_code(self) -> None:
        exc = ConflictError("slot already taken")
        assert exc.code == "CONFLICT"

    @pytest.mark.unit
    def test_infrastructure_error_wraps_cause(self) -> None:
        cause = RuntimeError("connection refused")
        exc = InfrastructureError("DynamoDB unavailable", cause=cause)
        assert exc.cause is cause
        assert exc.code == "INFRASTRUCTURE_ERROR"

    @pytest.mark.unit
    def test_tenant_not_found_is_entity_not_found(self) -> None:
        exc = TenantNotFoundError("tenant-abc")
        assert isinstance(exc, EntityNotFoundError)
        assert exc.identifier == "tenant-abc"
