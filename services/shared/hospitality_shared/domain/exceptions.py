"""Shared domain exceptions used across all services."""

from __future__ import annotations


class HospitalityBaseError(Exception):
    """Base exception for all hospitality platform errors."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.code = code

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


class DomainValidationError(HospitalityBaseError):
    """Raised when a domain invariant is violated."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="DOMAIN_VALIDATION_ERROR")


class EntityNotFoundError(HospitalityBaseError):
    """Raised when a requested entity does not exist."""

    def __init__(self, entity_type: str, identifier: str) -> None:
        super().__init__(
            f"{entity_type} not found: {identifier}",
            code="ENTITY_NOT_FOUND",
        )
        self.entity_type = entity_type
        self.identifier = identifier


class ConflictError(HospitalityBaseError):
    """Raised when an operation conflicts with existing state."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="CONFLICT")


class InfrastructureError(HospitalityBaseError):
    """Raised when an infrastructure call fails (DynamoDB, Bedrock, SNS, etc.)."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message, code="INFRASTRUCTURE_ERROR")
        self.cause = cause


class TenantNotFoundError(EntityNotFoundError):
    """Raised when a tenant configuration cannot be found."""

    def __init__(self, tenant_id: str) -> None:
        super().__init__("Tenant", tenant_id)
