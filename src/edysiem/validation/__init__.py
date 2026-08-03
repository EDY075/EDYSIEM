"""Validação declarativa de dados do EDY SIEM."""

from .engine import ValidationEngine, ValidationResult, ValidationRule
from .validators import (
    in_range,
    is_email,
    is_hash,
    is_hostname,
    is_ip,
    is_ipv4,
    is_ipv6,
    is_non_empty,
    is_url,
    validate_uuid,
)

__all__ = [
    "ValidationEngine",
    "ValidationResult",
    "ValidationRule",
    "in_range",
    "is_email",
    "is_hash",
    "is_hostname",
    "is_ip",
    "is_ipv4",
    "is_ipv6",
    "is_non_empty",
    "is_url",
    "validate_uuid",
]
