"""Demonstração dos modelos da pipeline oficial do EDY SIEM.

Jornada: Collector → RawEvent → Parser → ParsedEvent → Normalizer →
CanonicalEvent → Enrichment → EnrichedEvent.

Este exemplo não depende de nenhuma biblioteca externa e apenas ilustra a
criação e o encadeamento dos modelos imutáveis (``frozen=True``). A execução
da pipeline real (parsers, normalizer, enrichment) acontece em sprints
futuros — aqui o foco é o contrato de dados.
"""

from __future__ import annotations

from datetime import UTC, datetime

from edysiem.domain import (
    CanonicalEvent,
    EnrichedEvent,
    Enrichment,
    ParsedEvent,
    RawEvent,
    Severity,
)


def _utcnow() -> datetime:
    return datetime.now(UTC)


def demo() -> None:
    # 1) Collector -> RawEvent (payload bruto, sem interpretação).
    raw = RawEvent(
        source_type="syslog",
        source_host="fw-01",
        raw_payload=b"<13>Aug  3 12:00:00 fw-01 sshd[123]: Accepted password for admin",
        tags=frozenset({"network", "ssh"}),
    )
    print("RawEvent:")
    print(f"  source={raw.source_type}/{raw.source_host} payload={raw.raw_payload!r}")

    # 2) Parser -> ParsedEvent (campos estruturados extraídos).
    parsed = ParsedEvent(
        event_id=raw.event_id,
        timestamp=raw.received_at,
        source_type=raw.source_type,
        source_host=raw.source_host,
        event_type="logon",
        fields={"user": "admin", "protocol": "ssh", "port": 22},
        raw=raw.raw_payload,
        trace_id="trace-001",
    )
    print("\nParsedEvent:")
    print(f"  event_type={parsed.event_type} fields={parsed.fields}")

    # 3) Normalizer -> CanonicalEvent (modelo canônico).
    canonical = CanonicalEvent(
        event_id=parsed.event_id,
        timestamp=parsed.timestamp,
        source_type=parsed.source_type,
        source_host=parsed.source_host,
        event_type=parsed.event_type,
        severity=Severity.MEDIUM,
        user=parsed.fields["user"],
        ip_src="10.0.0.5",
        hostname="wks-01.corp",
        payload=parsed.fields,
        raw=parsed.raw if isinstance(parsed.raw, str) else parsed.raw.decode("utf-8", "replace"),
        trace_id=parsed.trace_id,
    )
    print("\nCanonicalEvent:")
    print(f"  severity={canonical.severity.value} user={canonical.user} ip_src={canonical.ip_src}")

    # 4) Enrichment -> EnrichedEvent (contexto anexado, sem mutação).
    asset_info = Enrichment(
        kind="asset",
        provider="asset-db",
        data={"owner": "soc", "criticality": "high"},
    )
    geo_info = Enrichment(
        kind="geo",
        provider="maxmind",
        data={"country": "BR", "asn": "AS27699"},
    )
    enriched = EnrichedEvent(
        **{field: getattr(canonical, field) for field in canonical.__match_args__},
        enrichments=(asset_info, geo_info),
    )
    print("\nEnrichedEvent:")
    print(f"  event_id={enriched.event_id} enrichments={[e.kind for e in enriched.enrichments]}")

    # Modelos são imutáveis: tentar alterar um atributo levanta FrozenInstanceError.
    print("\nImutabilidade: tentando alterar enriched.severity ...")
    try:
        enriched.severity = Severity.CRITICAL  # type: ignore[misc]
    except Exception as exc:  # pragma: no cover - caminho de erro didático
        print(f"  -> {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    demo()
