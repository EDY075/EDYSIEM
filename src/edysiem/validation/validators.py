"""Validadores booleanos livres de HTTP (utilizáveis em qualquer contexto)."""

from __future__ import annotations

import ipaddress
import re
from collections.abc import Mapping, Sequence
from typing import Any
from uuid import UUID

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_HASH_RE = re.compile(r"^[0-9a-fA-F]{32,128}$")
_URL_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://[^\s]+$")
_HOST_PATTERN = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?$")


def is_ipv4(value: str) -> bool:
    """Verdadeiro se a string representa um IPv4 válido."""
    try:
        addr = ipaddress.ip_address(value.strip())
    except ValueError:
        return False
    return isinstance(addr, ipaddress.IPv4Address)


def is_ipv6(value: str) -> bool:
    """Verdadeiro se a string representa um IPv6 válido."""
    try:
        addr = ipaddress.ip_address(value.strip())
    except ValueError:
        return False
    return isinstance(addr, ipaddress.IPv6Address)


def is_ip(value: str) -> bool:
    """Verdadeiro se a string for IPv4 ou IPv6 válido."""
    try:
        ipaddress.ip_address(value.strip())
    except ValueError:
        return False
    return True


def is_hash(value: str, *, length: int | None = None) -> bool:
    """Verdadeiro se a string for um hash hex (md5/sha1/sha256)."""
    candidate = value.strip().lower()
    if not _HASH_RE.fullmatch(candidate):
        return False
    if length is not None and len(candidate) != length:
        return False
    return True


def is_email(value: str) -> bool:
    """Verdadeiro se a string parecer um e-mail válido."""
    return _EMAIL_RE.match(value.strip()) is not None


def is_url(value: str) -> bool:
    """Verdadeiro se a string for uma URL absoluta com scheme."""
    return _URL_RE.match(value.strip()) is not None


def is_hostname(value: str) -> bool:
    """Verdadeiro se a string for um hostname/FQDN plausível."""
    candidate = value.strip()
    if len(candidate) > 253:
        return False
    return _HOST_PATTERN.fullmatch(candidate) is not None


def in_range(value: Any, minimum: float, maximum: float) -> bool:
    """Verdadeiro se o valor numérico estiver dentro do intervalo (inclusive)."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return minimum <= number <= maximum


def is_non_empty(value: str | Sequence[Any] | Mapping[str, Any] | None) -> bool:
    """Verdadeiro se a coleção/string não for vazia e não ``None``."""
    if value is None:
        return False
    return len(value) > 0


def validate_uuid(value: str) -> bool:
    """Verdadeiro se a string for um UUID normalizado válido."""
    try:
        UUID(value.strip())
    except (ValueError, AttributeError):
        return False
    return True


__all__ = [
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
