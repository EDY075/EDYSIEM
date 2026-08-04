"""Testes dos providers do EnrichmentContext."""

from __future__ import annotations

import pytest

from edysiem.enrichment import EnrichmentContext
from edysiem.enrichment.context import AssetInfo, GeoInfo, ThreatIntelInfo, UserInfo


class MockAssetDB:
    def __init__(self, asset: AssetInfo | None = None) -> None:
        self._asset = asset

    async def find_by_ip(self, ip: str) -> AssetInfo | None:
        if self._asset and ip in self._asset.ip_addresses:
            return self._asset
        return None

    async def find_by_hostname(self, hostname: str) -> AssetInfo | None:
        if self._asset and hostname == self._asset.hostname:
            return self._asset
        return None


class MockGeoProvider:
    def __init__(self, geo: GeoInfo | None = None) -> None:
        self._geo = geo

    async def lookup(self, ip: str) -> GeoInfo | None:
        if self._geo and ip == self._geo.ip:
            return self._geo
        return None


class MockIntelProvider:
    def __init__(self, intel: ThreatIntelInfo | None = None) -> None:
        self._intel = intel

    async def check(self, indicator: str, indicator_type: str) -> ThreatIntelInfo | None:
        if self._intel and indicator == self._intel.indicator:
            return self._intel
        return None


class MockUserDirectory:
    def __init__(self, user: UserInfo | None = None) -> None:
        self._user = user

    async def get_user(self, username: str) -> UserInfo | None:
        if self._user and username == self._user.username:
            return self._user
        return None


@pytest.mark.asyncio
async def test_context_asset_by_ip() -> None:
    asset = AssetInfo(
        asset_id="asset-1",
        hostname="wks-01",
        ip_addresses=frozenset({"10.0.0.5"}),
        asset_type="workstation",
    )
    context = EnrichmentContext(asset_db=MockAssetDB(asset))

    result = await context.get_asset_by_ip("10.0.0.5")
    assert result is not None
    assert result.asset_id == "asset-1"
    assert result.hostname == "wks-01"


@pytest.mark.asyncio
async def test_context_asset_miss() -> None:
    asset = AssetInfo(
        asset_id="asset-1",
        hostname="wks-01",
        ip_addresses=frozenset({"10.0.0.5"}),
    )
    context = EnrichmentContext(asset_db=MockAssetDB(asset))

    result = await context.get_asset_by_ip("10.0.0.99")
    assert result is None


@pytest.mark.asyncio
async def test_context_asset_by_hostname() -> None:
    asset = AssetInfo(
        asset_id="asset-1",
        hostname="wks-01",
        ip_addresses=frozenset({"10.0.0.5"}),
    )
    context = EnrichmentContext(asset_db=MockAssetDB(asset))

    result = await context.get_asset_by_hostname("wks-01")
    assert result is not None
    assert result.asset_id == "asset-1"


@pytest.mark.asyncio
async def test_context_asset_no_db() -> None:
    context = EnrichmentContext()
    result = await context.get_asset_by_ip("10.0.0.5")
    assert result is None


@pytest.mark.asyncio
async def test_context_geo_lookup() -> None:
    geo = GeoInfo(
        ip="8.8.8.8",
        country="US",
        country_code="US",
        city="Mountain View",
        is_vpn=False,
    )
    context = EnrichmentContext(geo_provider=MockGeoProvider(geo))

    result = await context.get_geo_info("8.8.8.8")
    assert result is not None
    assert result.country == "US"
    assert result.city == "Mountain View"


@pytest.mark.asyncio
async def test_context_geo_no_provider() -> None:
    context = EnrichmentContext()
    result = await context.get_geo_info("8.8.8.8")
    assert result is None


@pytest.mark.asyncio
async def test_context_threat_intel() -> None:
    intel = ThreatIntelInfo(
        indicator="1.2.3.4",
        indicator_type="ip",
        malicious=True,
        confidence=90,
        severity="high",
    )
    context = EnrichmentContext(intel_provider=MockIntelProvider(intel))

    result = await context.check_threat_intel("1.2.3.4", "ip")
    assert result is not None
    assert result.malicious is True
    assert result.confidence == 90


@pytest.mark.asyncio
async def test_context_threat_intel_no_provider() -> None:
    context = EnrichmentContext()
    result = await context.check_threat_intel("1.2.3.4", "ip")
    assert result is None


@pytest.mark.asyncio
async def test_context_user_lookup() -> None:
    user = UserInfo(
        username="admin",
        email="admin@corp.com",
        department="IT",
        is_privileged=True,
    )
    context = EnrichmentContext(user_directory=MockUserDirectory(user))

    result = await context.get_user_info("admin")
    assert result is not None
    assert result.email == "admin@corp.com"
    assert result.is_privileged is True


@pytest.mark.asyncio
async def test_context_user_no_directory() -> None:
    context = EnrichmentContext()
    result = await context.get_user_info("admin")
    assert result is None


@pytest.mark.asyncio
async def test_context_cache_hit_miss_metrics() -> None:
    asset = AssetInfo(
        asset_id="asset-1",
        hostname="wks-01",
        ip_addresses=frozenset({"10.0.0.5"}),
    )
    context = EnrichmentContext(asset_db=MockAssetDB(asset))

    # First call = miss
    result1 = await context.get_asset_by_ip("10.0.0.5")
    assert result1 is not None

    # Second call = hit (cached)
    result2 = await context.get_asset_by_ip("10.0.0.5")
    assert result2 is not None

    assert context.metrics.get("enrichment.asset.cache_hit") == 1
    assert context.metrics.get("enrichment.asset.cache_miss") == 1


@pytest.mark.asyncio
async def test_context_health_check_no_providers() -> None:
    context = EnrichmentContext()
    health = await context.health_check()
    assert health["status"] == "healthy"
    assert "cache" in health


@pytest.mark.asyncio
async def test_context_health_check_with_providers() -> None:
    context = EnrichmentContext(
        asset_db=MockAssetDB(),
        geo_provider=MockGeoProvider(),
    )
    health = await context.health_check()
    assert "asset_db" in health["components"]
    assert "geo_provider" in health["components"]
