"""Testes dos modelos de enriquecimento."""

from __future__ import annotations

import pytest

from edysiem.enrichment.models import (
    CachePolicy,
    Enrichment,
    EnrichmentKind,
    EnrichmentResult,
)


def test_enrichment_creation() -> None:
    enrichment = Enrichment(
        kind=EnrichmentKind.ASSET,
        provider="asset-db",
        data={"owner": "sec", "criticality": 90},
    )
    assert enrichment.kind == EnrichmentKind.ASSET
    assert enrichment.provider == "asset-db"
    assert enrichment.data == {"owner": "sec", "criticality": 90}
    assert enrichment.cache_policy == CachePolicy.NONE


def test_enrichment_with_cache_policy() -> None:
    enrichment = Enrichment(
        kind=EnrichmentKind.GEO,
        provider="maxmind",
        data={"country": "BR"},
        cache_policy=CachePolicy.TTL,
        ttl_seconds=3600,
    )
    assert enrichment.cache_policy == CachePolicy.TTL
    assert enrichment.ttl_seconds == 3600


def test_enrichment_ttl_required_for_ttl_policy() -> None:
    with pytest.raises(ValueError, match="TTL deve ser > 0"):
        Enrichment(
            kind=EnrichmentKind.GEO,
            provider="maxmind",
            data={},
            cache_policy=CachePolicy.TTL,
            ttl_seconds=0,
        )

    with pytest.raises(ValueError, match="TTL deve ser > 0"):
        Enrichment(
            kind=EnrichmentKind.GEO,
            provider="maxmind",
            data={},
            cache_policy=CachePolicy.TTL,
            ttl_seconds=-1,
        )


def test_enrichment_requires_kind() -> None:
    with pytest.raises(ValueError, match="kind não pode ser vazio"):
        Enrichment(kind=None, provider="test", data={})  # type: ignore


def test_enrichment_requires_provider() -> None:
    with pytest.raises(ValueError, match="provider não pode ser vazio"):
        Enrichment(kind=EnrichmentKind.ASSET, provider="", data={})


def test_enrichment_result_ok() -> None:
    enrichment = Enrichment(kind=EnrichmentKind.ASSET, provider="test", data={})
    result = EnrichmentResult.ok(
        enrichments=(enrichment,),
        duration_ms=10.5,
        plugin_name="test-plugin",
    )
    assert result.success is True
    assert result.enrichments == (enrichment,)
    assert result.duration_ms == 10.5
    assert result.plugin_name == "test-plugin"
    assert result.error is None


def test_enrichment_result_fail() -> None:
    result = EnrichmentResult.fail(
        error="timeout",
        duration_ms=5000.0,
        plugin_name="slow-plugin",
    )
    assert result.success is False
    assert result.enrichments == ()
    assert result.error == "timeout"
    assert result.duration_ms == 5000.0
    assert result.plugin_name == "slow-plugin"


def test_enrichment_kind_enum() -> None:
    assert EnrichmentKind.ASSET.value == "asset"
    assert EnrichmentKind.GEO.value == "geo"
    assert EnrichmentKind.THREAT_INTEL.value == "threat_intel"
    assert EnrichmentKind.USER.value == "user"
    assert EnrichmentKind.PROCESS.value == "process"
    assert EnrichmentKind.NETWORK.value == "network"
    assert EnrichmentKind.CUSTOM.value == "custom"


def test_cache_policy_enum() -> None:
    assert CachePolicy.NONE.value == "none"
    assert CachePolicy.TTL.value == "ttl"
    assert CachePolicy.ETERNAL.value == "eternal"
