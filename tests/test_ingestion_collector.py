"""Testes do contrato Enterprise de coletores (CollectorPlugin)."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import pytest

from edysiem.domain import RawEvent
from edysiem.ingestion.collectors.base import (
    CollectorCapability,
    CollectorMetadata,
    CollectorPlugin,
)
from edysiem.ingestion.health import CollectorHealth, ComponentStatus


def test_capability_values() -> None:
    assert CollectorCapability.STREAMING.value == "streaming"
    assert CollectorCapability.BATCH.value == "batch"
    assert CollectorCapability.RECONNECT.value == "reconnect"
    assert CollectorCapability.BACKPRESSURE.value == "backpressure"
    assert CollectorCapability.RATE_LIMIT.value == "rate_limit"


def test_metadata_defaults_and_fields() -> None:
    caps = frozenset({CollectorCapability.STREAMING, CollectorCapability.RECONNECT})
    metadata = CollectorMetadata(
        name="syslog",
        version="1.0.0",
        source_type="syslog",
        description="Coletor syslog",
        capabilities=caps,
    )
    assert metadata.name == "syslog"
    assert metadata.version == "1.0.0"
    assert metadata.source_type == "syslog"
    assert metadata.description == "Coletor syslog"
    assert metadata.capabilities == caps
    assert isinstance(metadata.capabilities, frozenset)


def test_metadata_is_frozen_and_slotted() -> None:
    metadata = CollectorMetadata(name="a", version="1", source_type="b")
    with pytest.raises(AttributeError):
        metadata.name = "outro"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("name", "version", "source_type"),
    [
        ("", "1.0.0", "syslog"),
        ("syslog", "", "syslog"),
        ("syslog", "1.0.0", ""),
        ("   ", "1.0.0", "syslog"),
    ],
)
def test_metadata_validation(name: str, version: str, source_type: str) -> None:
    with pytest.raises(ValueError, match="não pode ser vazio"):
        CollectorMetadata(name=name, version=version, source_type=source_type)


class FakeCollector:
    """Implementação de teste do contrato Enterprise."""

    def __init__(self, events: tuple[RawEvent, ...]) -> None:
        self._events = events
        self.started = False
        self.stopped = False

    @property
    def metadata(self) -> CollectorMetadata:
        return CollectorMetadata(
            name="fake",
            version="1.0.0",
            source_type="custom",
            capabilities=frozenset({CollectorCapability.STREAMING}),
        )

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.stopped = True

    def read(self) -> AsyncIterator[RawEvent]:
        async def _inner() -> AsyncIterator[RawEvent]:
            for event in self._events:
                yield event

        return _inner()

    async def health(self) -> CollectorHealth:
        return CollectorHealth(
            status=ComponentStatus.ONLINE,
            uptime_seconds=1.0,
            last_event_at=None,
            throughput_events_per_sec=1.0,
            errors=0,
            queue_size=0,
        )

    def capabilities(self) -> frozenset[CollectorCapability]:
        return frozenset({CollectorCapability.STREAMING})


class IncompleteCollector:
    """Implementação que NÃO implementa o protocolo Enterprise."""

    @property
    def metadata(self) -> CollectorMetadata:
        return CollectorMetadata(name="x", version="1", source_type="x")

    async def start(self) -> None:
        return None

    async def stop(self) -> None:
        return None

    # read() ausente de propósito.


def test_runtime_checkable_accepts_complete_implementation() -> None:
    collector = FakeCollector(())
    assert isinstance(collector, CollectorPlugin)


def test_runtime_checkable_rejects_incomplete_implementation() -> None:
    collector = IncompleteCollector()
    assert not isinstance(collector, CollectorPlugin)


def test_fake_collector_contract_lifecycle() -> None:
    event = RawEvent(source_type="custom", source_host="h", raw_payload=b"d")
    collector = FakeCollector((event,))

    async def scenario() -> None:
        await collector.start()
        collected = [e async for e in collector.read()]
        health = await collector.health()
        await collector.stop()
        return collected, health

    collected, health = asyncio.run(scenario())
    assert collector.started is True
    assert collector.stopped is True
    assert len(collected) == 1
    assert collected[0].event_id == event.event_id
    assert health.status is ComponentStatus.ONLINE
    assert collector.metadata.name == "fake"
    assert collector.capabilities() == frozenset({CollectorCapability.STREAMING})
