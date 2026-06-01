"""Shared domain value types used across all services."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class PhoneNumber:
    """E.164-normalised phone number value object."""

    value: str

    _E164_RE = re.compile(r"^\+?[1-9]\d{7,14}$")

    def __post_init__(self) -> None:
        normalised = re.sub(r"[\s\-\(\)]", "", self.value)
        if not self._E164_RE.match(normalised):
            raise ValueError(f"Invalid phone number: {self.value!r}")
        # Store normalised form — frozen dataclass requires object.__setattr__
        object.__setattr__(self, "value", normalised)

    def masked(self) -> str:
        """Return PII-safe masked representation for logging."""
        if len(self.value) >= 4:
            return f"***-***-{self.value[-4:]}"
        return "***"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Email:
    """Validated email address value object."""

    value: str

    _EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def __post_init__(self) -> None:
        normalised = self.value.strip().lower()
        if not self._EMAIL_RE.match(normalised):
            raise ValueError(f"Invalid email address: {self.value!r}")
        object.__setattr__(self, "value", normalised)

    def masked(self) -> str:
        """Return PII-safe masked representation for logging."""
        local, _, domain = self.value.partition("@")
        return f"{local[:2]}***@{domain}"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class TenantId:
    """Tenant identifier value object."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("TenantId cannot be empty")
        object.__setattr__(self, "value", self.value.strip().lower())

    def __str__(self) -> str:
        return self.value
