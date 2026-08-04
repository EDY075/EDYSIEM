"""Testes do CorrelationContext (janelas temporais)."""

from __future__ import annotations

import time

import pytest

from edysiem.correlation import CorrelationContext


def test_context_creation() -> None:
    context = CorrelationContext()
    assert context.state_size == 0
    assert context.total_entries() == 0
    assert context.default_ttl_seconds > 0


def test_context_add_and_get_window() -> None:
    context = CorrelationContext()
    context.add_event("rule-1", "10.0.0.1", "evt-1")
    context.add_event("rule-1", "10.0.0.1", "evt-2")
    context.add_event("rule-1", "10.0.0.2", "evt-3")

    window = context.get_window("rule-1", "10.0.0.1", 300.0)
    assert set(window) == {"evt-1", "evt-2"}
    assert "evt-3" not in window

    assert context.state_size == 2  # duas chaves
    assert context.total_entries() == 3


def test_context_window_expiry() -> None:
    context = CorrelationContext()
    now = time.monotonic()

    # evt-1 dentro da janela, evt-2 fora
    context.add_event("rule-1", "ip-1", "evt-1", timestamp=now)
    context.add_event("rule-1", "ip-1", "evt-2", timestamp=now - 600)

    window = context.get_window("rule-1", "ip-1", 300.0, now=now)
    assert window == ("evt-1",)


def test_context_empty_window_removed() -> None:
    context = CorrelationContext()
    now = time.monotonic()

    context.add_event("rule-1", "ip-1", "evt-1", timestamp=now - 600)
    window = context.get_window("rule-1", "ip-1", 300.0, now=now)
    assert window == ()
    # Janela vazia deve ser removida
    assert context.state_size == 0


def test_context_window_size() -> None:
    context = CorrelationContext()
    context.add_event("rule-1", "ip-1", "evt-1")
    context.add_event("rule-1", "ip-1", "evt-2")
    context.add_event("rule-1", "ip-1", "evt-3")

    assert context.window_size("rule-1", "ip-1", 300.0) == 3


def test_context_expire() -> None:
    context = CorrelationContext()
    now = time.monotonic()
    context.add_event("rule-1", "ip-1", "evt-1", timestamp=now)
    context.add_event("rule-1", "ip-1", "evt-2", timestamp=now - 600)

    remaining = context.expire("rule-1", "ip-1", 300.0, now=now)
    assert remaining == 1


def test_context_clear_all() -> None:
    context = CorrelationContext()
    context.add_event("rule-1", "ip-1", "evt-1")
    context.add_event("rule-2", "ip-2", "evt-2")

    context.clear()
    assert context.state_size == 0


def test_context_clear_by_rule() -> None:
    context = CorrelationContext()
    context.add_event("rule-1", "ip-1", "evt-1")
    context.add_event("rule-2", "ip-2", "evt-2")

    context.clear(rule_id="rule-1")
    assert context.state_size == 1


def test_context_clear_by_rule_and_key() -> None:
    context = CorrelationContext()
    context.add_event("rule-1", "ip-1", "evt-1")
    context.add_event("rule-1", "ip-2", "evt-2")

    context.clear(rule_id="rule-1", identity_key="ip-1")
    assert context.state_size == 1


def test_context_add_event_validates() -> None:
    context = CorrelationContext()
    with pytest.raises(ValueError, match="rule_id nao pode ser vazio"):
        context.add_event("", "ip-1", "evt-1")
    with pytest.raises(ValueError, match="identity_key nao pode ser vazio"):
        context.add_event("rule-1", "", "evt-1")


def test_context_get_window_validates() -> None:
    context = CorrelationContext()
    with pytest.raises(ValueError, match="window_seconds deve ser > 0"):
        context.get_window("rule-1", "ip-1", 0)


def test_context_snapshot() -> None:
    context = CorrelationContext()
    context.add_event("rule-1", "ip-1", "evt-1")

    snap = context.snapshot()
    assert snap["windows_active"] == 1
    assert snap["total_entries"] == 1
