"""Common input validators used across Lambda handlers."""

from __future__ import annotations

from typing import Any

from hospitality_shared.domain.exceptions import DomainValidationError


def require_field(event: dict[str, Any], field: str) -> Any:
    """Assert a required field is present and non-empty in the event dict.

    Args:
        event: The Lambda event dict.
        field: The required field name.

    Returns:
        The field value.

    Raises:
        DomainValidationError: If the field is missing or empty.
    """
    value = event.get(field)
    if value is None or (isinstance(value, str) and not value.strip()):
        raise DomainValidationError(f"Required field missing or empty: '{field}'")
    return value


def require_fields(event: dict[str, Any], *fields: str) -> dict[str, Any]:
    """Assert multiple required fields are present and return them as a dict.

    Args:
        event: The Lambda event dict.
        *fields: Required field names.

    Returns:
        Dict of field_name → value for all required fields.

    Raises:
        DomainValidationError: If any field is missing or empty.
    """
    return {field: require_field(event, field) for field in fields}
