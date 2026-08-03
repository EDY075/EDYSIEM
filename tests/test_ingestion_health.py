"""Testes do HealthMonitor e tipos de saúde."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest

from edysiem.ingestion.health import (
    CollectorHealth,
    ComponentStatus,
    HealthMonitor,
)


def _health(status: ComponentStatus) -> CollectorHealth:
    return CollectorHealth(
        status=status,
        uptime_seconds=10.0,
        last_event_at=datetime.now(UTC),
        throughput_events_per_sec=5.0,
        errors=0,
        queue_size=3,
        latency_ms=1.5,
    )


def test_component_status_values() -> None:
    assert ComponentStatus.ONLINE.value == "online"
    assert ComponentStatus.DEGRADED.value == "degraded"
    assert ComponentStatus.OFFLINE.value == "offline"


def test_register_initializes_offline_placeholder() -> None:
    monitor = HealthMonitor()
    monitor.register("syslog")
    snapshot = monitor.snapshot()
    assert "syslog" in snapshot
    assert snapshot["syslog"].status is ComponentStatus.OFFLINE


def test_register_rejects_empty_name() -> None:
    monitor = HealthMonitor()
    with pytest.raises(ValueError, match="name"):
        monitor.register("")
    with pytest.raises(ValueError, match="name"):
        monitor.register("   ")


def test_update_and_snapshot() -> None:
    monitor = HealthMonitor()
    monitor.register("syslog")
    monitor.update("syslog", _health(ComponentStatus.ONLINE))
    assert monitor.snapshot()["syslog"].status is ComponentStatus.ONLINE


def test_update_creates_unregistered_component() -> None:
    monitor = HealthMonitor()
    monitor.update("novo", _health(ComponentStatus.ONLINE))
    assert "novo" in monitor.snapshot()


def test_snapshot_is_a_copy() -> None:
    monitor = HealthMonitor()
    monitor.register("a")
    snapshot = monitor.snapshot()
    snapshot["a"] = _health(ComponentStatus.ONLINE)
    assert monitor.snapshot()["a"].status is ComponentStatus.OFFLINE


def test_aggregate_empty_monitor_is_online() -> None:
    monitor = HealthMonitor()
    assert monitor.aggregate() is ComponentStatus.ONLINE
    assert monitor.is_healthy() is True


def test_aggregate_all_online() -> None:
    monitor = HealthMonitor()
    monitor.update("a", _health(ComponentStatus.ONLINE))
    monitor.update("b", _health(ComponentStatus.ONLINE))
    assert monitor.aggregate() is ComponentStatus.ONLINE
    assert monitor.is_healthy() is True


def test_aggregate_degraded_wins_over_online() -> None:
    monitor = HealthMonitor()
    monitor.update("a", _health(ComponentStatus.ONLINE))
    monitor.update("b", _health(ComponentStatus.DEGRADED))
    assert monitor.aggregate() is ComponentStatus.DEGRADED
    assert monitor.is_healthy() is False


def test_aggregate_offline_wins_over_all() -> None:
    monitor = HealthMonitor()
    monitor.update("a", _health(ComponentStatus.ONLINE))
    monitor.update("b", _health(ComponentStatus.DEGRADED))
    monitor.update("c", _health(ComponentStatus.OFFLINE))
    assert monitor.aggregate() is ComponentStatus.OFFLINE


class FakeCollector:
    """Fake de collector para testar ``HealthMonitor.refresh``."""

    def __init__(self, health: CollectorHealth) -> None:
        self._health_value = health

    async def health(self) -> CollectorHealth:
        return self._health_value


def test_refresh_with_registered_collector() -> None:
    monitor = HealthMonitor()
    fake = FakeCollector(_health(ComponentStatus.DEGRADED))
    monitor.register("custom", collector=fake)  # type: ignore[arg-type]

    async def scenario() -> None:
        health = await monitor.refresh("custom")
        assert health is not None
        assert health.status is ComponentStatus.DEGRADED

    asyncio.run(scenario())
    assert monitor.snapshot()["custom"].status is ComponentStatus.DEGRADED


def test_refresh_without_collector_returns_none() -> None:
    monitor = HealthMonitor()
    monitor.register("sem-collector")

    async def scenario() -> None:
        assert await monitor.refresh("sem-collector") is None

    asyncio.run(scenario())
