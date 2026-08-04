"""Testes do EnrichmentContext."""

from __future__ import annotations

from edysiem.enrichment import EnrichmentContext
from edysiem.ingestion.metrics import MetricsRegistry


def test_context_creation() -> None:
    context = EnrichmentContext()
    assert context is not None
    assert context._cache_ttl == 300


def test_context_custom_ttl() -> None:
    context = EnrichmentContext(cache_ttl_seconds=600)
    assert context._cache_ttl == 600


def test_context_cache_operations() -> None:
    context = EnrichmentContext(cache_ttl_seconds=10)

    # Set and get
    context._set_cache("key1", "value1")
    assert context._get_from_cache("key1") == "value1"

    # Miss
    assert context._get_from_cache("nonexistent") is None


def test_context_cache_expiration() -> None:
    import time

    context = EnrichmentContext(cache_ttl_seconds=1)

    context._set_cache("key1", "value1")
    assert context._get_from_cache("key1") == "value1"

    time.sleep(1.1)
    assert context._get_from_cache("key1") is None


def test_context_cache_ttl_override() -> None:
    context = EnrichmentContext(cache_ttl_seconds=10)
    context._set_cache("key1", "value1", ttl=100)

    # Should still be there after default TTL would expire
    import time

    time.sleep(0.1)
    assert context._get_from_cache("key1") == "value1"


def test_context_clear_cache() -> None:
    context = EnrichmentContext()
    context._set_cache("key1", "value1")
    context._set_cache("key2", "value2")

    context.clear_cache()
    assert context._get_from_cache("key1") is None
    assert context._get_from_cache("key2") is None


def test_context_cache_stats() -> None:
    context = EnrichmentContext(cache_ttl_seconds=10)
    context._set_cache("key1", "value1")
    context._set_cache("key2", "value2")

    stats = context.get_cache_stats()
    assert stats["total_entries"] == 2
    assert stats["valid_entries"] == 2
    assert stats["expired_entries"] == 0


def test_context_settings() -> None:
    context = EnrichmentContext()
    context.set_setting("custom_key", "custom_value")
    assert context.get_setting("custom_key") == "custom_value"
    assert context.get_setting("nonexistent", "default") == "default"


def test_context_metrics() -> None:
    context = EnrichmentContext()
    assert isinstance(context.metrics, MetricsRegistry)
