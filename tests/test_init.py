"""Testes do pacote raiz: versão e API pública."""

from __future__ import annotations

import edysiem


def test_version() -> None:
    assert edysiem.__version__ == "0.3.0"


def test_public_api_present() -> None:
    for name in (
        "Event",
        "EventBus",
        "Result",
        "Success",
        "Failure",
        "ErrorCode",
        "SiemConfig",
        "Container",
        "Lifetime",
        "ValidationEngine",
        "StructuredLogger",
        "Severity",
        "User",
        "ParserPlugin",
        "DomainException",
        "ingestion",
    ):
        assert hasattr(edysiem, name), f"falta API pública: {name}"
