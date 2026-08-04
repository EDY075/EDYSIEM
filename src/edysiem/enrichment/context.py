"""Contexto de Enriquecimento do EDY SIEM.

O ``EnrichmentContext`` é o objeto passado a todos os plugins durante
o enriquecimento. Contém referências a fontes de dados externas:

- Asset Database (inventário de ativos)
- GeoIP (localização por IP)
- Threat Intelligence (IOCs, reputação)
- User Directory (identidades)
- Cache compartilhado entre plugins
- Configurações globais

Design:
- Thread-safe para acesso concorrente
- Lazy loading de conexões pesadas
- Cache com TTL configurável
- Métricas de hit/miss por fonte
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, cast

from ..ingestion.metrics import MetricsRegistry


@dataclass(frozen=True, slots=True)
class AssetInfo:
    """Informações de um ativo do inventário."""

    asset_id: str
    hostname: str | None = None
    fqdn: str | None = None
    ip_addresses: frozenset[str] = frozenset()
    mac_addresses: frozenset[str] = frozenset()
    asset_type: str = "unknown"
    owner: str | None = None
    department: str | None = None
    criticality: int = 0  # 0-100
    tags: frozenset[str] = frozenset()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class GeoInfo:
    """Informações geográficas de um IP."""

    ip: str
    country: str | None = None
    country_code: str | None = None
    region: str | None = None
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    asn: str | None = None
    isp: str | None = None
    is_vpn: bool = False
    is_proxy: bool = False
    is_tor: bool = False


@dataclass(frozen=True, slots=True)
class ThreatIntelInfo:
    """Informações de Threat Intelligence sobre um indicador."""

    indicator: str
    indicator_type: str  # ip, domain, hash, url, email
    malicious: bool = False
    confidence: int = 0  # 0-100
    severity: str = "info"
    tags: frozenset[str] = frozenset()
    sources: frozenset[str] = frozenset()
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class UserInfo:
    """Informações de identidade de usuário."""

    username: str
    email: str | None = None
    display_name: str | None = None
    department: str | None = None
    groups: frozenset[str] = frozenset()
    roles: frozenset[str] = frozenset()
    is_privileged: bool = False
    is_service_account: bool = False
    last_login: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class EnrichmentContext:
    """Contexto compartilhado para enriquecimento de eventos.

    Fornece acesso unificado a:
    - Asset Database
    - GeoIP
    - Threat Intelligence
    - User Directory
    - Cache compartilhado

    Thread-safe para uso concorrente por múltiplos plugins.
    """

    def __init__(
        self,
        *,
        asset_db: Any | None = None,
        geo_provider: Any | None = None,
        intel_provider: Any | None = None,
        user_directory: Any | None = None,
        cache_ttl_seconds: int = 300,
        metrics: MetricsRegistry | None = None,
    ) -> None:
        self._asset_db = asset_db
        self._geo_provider = geo_provider
        self._intel_provider = intel_provider
        self._user_directory = user_directory
        self._cache_ttl = cache_ttl_seconds
        self._metrics = metrics or MetricsRegistry()

        # Cache simples em memória com TTL
        self._cache: dict[str, tuple[Any, float]] = {}
        self._cache_lock = threading.RLock()

        # Configurações
        self._settings: dict[str, Any] = {}

    # --- Asset Database ---

    async def get_asset_by_ip(self, ip: str) -> AssetInfo | None:
        """Busca ativo por endereço IP."""
        return await self._lookup_asset(ip=ip)

    async def get_asset_by_hostname(self, hostname: str) -> AssetInfo | None:
        """Busca ativo por hostname."""
        return await self._lookup_asset(hostname=hostname)

    async def get_asset_by_fqdn(self, fqdn: str) -> AssetInfo | None:
        """Busca ativo por FQDN."""
        return await self._lookup_asset(fqdn=fqdn)

    async def get_asset_by_mac(self, mac: str) -> AssetInfo | None:
        """Busca ativo por endereço MAC."""
        return await self._lookup_asset(mac=mac)

    async def _lookup_asset(
        self,
        ip: str | None = None,
        hostname: str | None = None,
        fqdn: str | None = None,
        mac: str | None = None,
    ) -> AssetInfo | None:
        if self._asset_db is None:
            return None

        cache_key = f"asset:{ip or hostname or fqdn or mac}"
        cached = self._get_from_cache(cache_key)
        if cached:
            self._metrics.increment("enrichment.asset.cache_hit")
            return cast(AssetInfo | None, cached)

        self._metrics.increment("enrichment.asset.cache_miss")
        try:
            # Delega para o adapter do asset_db (implementação específica)
            if hasattr(self._asset_db, "find_by_ip") and ip:
                asset = await self._asset_db.find_by_ip(ip)
            elif hasattr(self._asset_db, "find_by_hostname") and hostname:
                asset = await self._asset_db.find_by_hostname(hostname)
            elif hasattr(self._asset_db, "find_by_fqdn") and fqdn:
                asset = await self._asset_db.find_by_fqdn(fqdn)
            elif hasattr(self._asset_db, "find_by_mac") and mac:
                asset = await self._asset_db.find_by_mac(mac)
            else:
                asset = None

            if asset:
                self._set_cache(cache_key, asset)
                return asset if isinstance(asset, AssetInfo) else None
            return None
        except Exception:
            return None

    # --- GeoIP ---

    async def get_geo_info(self, ip: str) -> GeoInfo | None:
        """Obtém informações geográficas de um IP."""
        if self._geo_provider is None:
            return None

        cache_key = f"geo:{ip}"
        cached = self._get_from_cache(cache_key)
        if cached:
            self._metrics.increment("enrichment.geo.cache_hit")
            return cast(GeoInfo | None, cached)

        self._metrics.increment("enrichment.geo.cache_miss")
        try:
            if hasattr(self._geo_provider, "lookup"):
                raw = await self._geo_provider.lookup(ip)
                geo: GeoInfo | None = cast(GeoInfo | None, raw)
                if geo:
                    self._set_cache(cache_key, geo)
                return geo
        except Exception:
            pass
        return None

    # --- Threat Intelligence ---

    async def check_threat_intel(
        self, indicator: str, indicator_type: str
    ) -> ThreatIntelInfo | None:
        """Verifica indicador em bases de Threat Intelligence."""
        if self._intel_provider is None:
            return None

        cache_key = f"intel:{indicator_type}:{indicator}"
        cached = self._get_from_cache(cache_key)
        if cached:
            self._metrics.increment("enrichment.intel.cache_hit")
            return cast(ThreatIntelInfo | None, cached)

        self._metrics.increment("enrichment.intel.cache_miss")
        try:
            if hasattr(self._intel_provider, "check"):
                raw = await self._intel_provider.check(indicator, indicator_type)
                intel: ThreatIntelInfo | None = cast(ThreatIntelInfo | None, raw)
                if intel:
                    self._set_cache(cache_key, intel)
                return intel
        except Exception:
            pass
        return None

    # --- User Directory ---

    async def get_user_info(self, username: str) -> UserInfo | None:
        """Obtém informações de usuário."""
        if self._user_directory is None:
            return None

        cache_key = f"user:{username}"
        cached = self._get_from_cache(cache_key)
        if cached:
            self._metrics.increment("enrichment.user.cache_hit")
            return cast(UserInfo | None, cached)

        self._metrics.increment("enrichment.user.cache_miss")
        try:
            if hasattr(self._user_directory, "get_user"):
                raw = await self._user_directory.get_user(username)
                user: UserInfo | None = cast(UserInfo | None, raw)
                if user:
                    self._set_cache(cache_key, user)
                return user
        except Exception:
            pass
        return None

    # --- Cache Management ---

    def _get_from_cache(self, key: str) -> Any | None:
        """Recupera item do cache se não expirado."""
        with self._cache_lock:
            if key in self._cache:
                value, expires_at = self._cache[key]
                if time.time() < expires_at:
                    return value
                else:
                    del self._cache[key]
        return None

    def _set_cache(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Armazena item no cache com TTL."""
        ttl = ttl or self._cache_ttl
        expires_at = time.time() + ttl
        with self._cache_lock:
            self._cache[key] = (value, expires_at)

    def clear_cache(self) -> None:
        """Limpa todo o cache."""
        with self._cache_lock:
            self._cache.clear()

    def get_cache_stats(self) -> dict[str, Any]:
        """Retorna estatísticas do cache."""
        with self._cache_lock:
            now = time.time()
            valid = sum(1 for _, exp in self._cache.values() if exp > now)
            expired = len(self._cache) - valid
            return {
                "total_entries": len(self._cache),
                "valid_entries": valid,
                "expired_entries": expired,
                "ttl_seconds": self._cache_ttl,
            }

    # --- Settings ---

    def set_setting(self, key: str, value: Any) -> None:
        """Define uma configuração global do contexto."""
        self._settings[key] = value

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Obtém uma configuração global."""
        return self._settings.get(key, default)

    # --- Metrics ---

    @property
    def metrics(self) -> MetricsRegistry:
        """Registry de métricas do contexto."""
        return self._metrics

    async def health_check(self) -> dict[str, Any]:
        """Verifica saúde dos provedores configurados."""
        checks = {}

        if self._asset_db:
            try:
                checks["asset_db"] = "ok" if hasattr(self._asset_db, "health") else "unknown"
            except Exception:
                checks["asset_db"] = "error"

        if self._geo_provider:
            try:
                checks["geo_provider"] = (
                    "ok" if hasattr(self._geo_provider, "health") else "unknown"
                )
            except Exception:
                checks["geo_provider"] = "error"

        if self._intel_provider:
            try:
                checks["intel_provider"] = (
                    "ok" if hasattr(self._intel_provider, "health") else "unknown"
                )
            except Exception:
                checks["intel_provider"] = "error"

        if self._user_directory:
            try:
                checks["user_directory"] = (
                    "ok" if hasattr(self._user_directory, "health") else "unknown"
                )
            except Exception:
                checks["user_directory"] = "error"

        return {
            "status": "healthy" if all(v == "ok" for v in checks.values()) else "degraded",
            "components": checks,
            "cache": self.get_cache_stats(),
        }


__all__ = [
    "AssetInfo",
    "EnrichmentContext",
    "GeoInfo",
    "ThreatIntelInfo",
    "UserInfo",
]
