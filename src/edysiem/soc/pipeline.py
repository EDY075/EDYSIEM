"""SocPipeline — orquestração E2E Evento → Regra → Alerta → Incidente → Caso.

Alto nível: reutiliza os engines existentes (via container) e persiste o
resultado através do ``SocService``. Nenhum engine é modificado — baixo
acoplamento e componentes reutilizáveis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

from ..alerts import Alert
from ..domain import CanonicalEvent, EnrichedEvent, ParsedEvent, RawEvent
from ..parsers import parse_rfc5424, parse_syslog
from ..persistence import PipelineStage
from ..result import Failure
from .service import SocService

if TYPE_CHECKING:
    from ..container import ApplicationContainer


@dataclass(frozen=True, slots=True)
class SocFlowResult:
    """Resumo do fluxo E2E executado.

    Attributes:
        correlation_id: ID de correlação do fluxo.
        alert_ids: IDs dos alertas criados.
        incident_id: ID do incidente (None se não houve agrupamento).
        case_id: ID do caso criado a partir do incidente (None se sem incidente).
        stages: Contagem de estágios percorridos.
    """

    correlation_id: str
    alert_ids: tuple[str, ...] = ()
    incident_id: str | None = None
    case_id: str | None = None
    stages: dict[str, int] = field(default_factory=dict)


def _finding(
    *,
    rule_id: str,
    severity: str,
    reason: str,
    event_ids: tuple[str, ...],
    tags: frozenset[str] = frozenset(),
    mitre: tuple[str, ...] = (),
    asset_id: str | None = None,
    user: str | None = None,
    ioc_ids: tuple[str, ...] = (),
) -> SimpleNamespace:
    """Finding mínimo compatível com o ``AlertBuilder`` (acessado via getattr)."""
    return SimpleNamespace(
        rule_id=rule_id,
        severity=severity,
        confidence=1.0,
        risk_score=None,
        reason=reason,
        event_ids=event_ids,
        tags=tags,
        mitre=mitre,
        asset_id=asset_id,
        user=user,
        ioc_ids=ioc_ids,
    )


class SocPipeline:
    """Orquestra o fluxo operacional completo e persiste o resultado."""

    def __init__(self, service: SocService, container: ApplicationContainer | None = None) -> None:
        self._service = service
        self._container = container

    @property
    def service(self) -> SocService:
        """SocService subjacente."""
        return self._service

    async def run_event(
        self,
        raw: RawEvent,
        *,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Executa um evento bruto pela pipeline de engines e persiste alertas.

        Fluxo: parse → normalize → enrich → correlate → detect → alert.
        Requer o ``container`` de engines (passado na construção).
        """
        if self._container is None:
            raise ValueError("SocPipeline.run_event exige o container de engines")
        service = self._service
        c = self._container
        cid = correlation_id or raw.event_id

        parsed = self._parse(raw)
        if not parsed.fields:
            raise ValueError("formato de log não reconhecido")
        canonical_result = c.normalizer.normalize(parsed)
        if isinstance(canonical_result, Failure):
            raise ValueError(f"normalização falhou: {canonical_result.error.message}")
        canonical: CanonicalEvent = canonical_result.unwrap()
        enriched: EnrichedEvent = (await c.enrichment.enrich(canonical)).unwrap()
        correlated = await c.correlation.process(enriched)
        outcome = await c.detection.process(correlated)

        alert_ids: list[str] = []
        for finding in outcome.findings:
            result = await service.alert_engine.process_finding(finding, source_event=enriched)
            service.persist_alert(result.alert)
            alert_ids.append(result.alert.id)

        service.event_store.record(
            stage=PipelineStage.CANONICAL,
            correlation_id=cid,
            source="pipeline",
            event_type=type(canonical).__name__,
            payload={"event_id": canonical.event_id},
        )

        return {
            "correlation_id": cid,
            "event_id": canonical.event_id,
            "category": canonical.event_category or "system",
            "action": canonical.event_action or "info",
            "severity": canonical.severity.value,
            "finding_count": len(outcome.findings),
            "detected_rule_ids": list(outcome.detected_rule_ids),
            "alert_ids": alert_ids,
        }

    async def run_demo(self) -> SocFlowResult:
        """Executa o fluxo E2E garantido (alerta → incidente → caso) e persiste."""
        service = self._service

        # 1) Gerar 4 alertas de brute-force (rule demo)
        alerts: list[Alert] = []
        targets = [
            ("web-01", "admin", "10.0.0.14"),
            ("db-01", "svc_backup", "10.0.0.27"),
            ("web-02", "admin", "10.0.0.66"),
            ("vpn-gw", "alex", "10.0.0.99"),
        ]
        for i, (host, user, ip) in enumerate(targets):
            finding = _finding(
                rule_id="brute-force-ssh",
                severity="critical" if i == 0 else "high",
                reason=f"{ip} tentou 12 acessos SSH sem sucesso em {host}",
                event_ids=(f"ev-{i}",),
                tags=frozenset({"brute-force"}),
                mitre=("T1110",),
                asset_id=host,
                user=user,
                ioc_ids=(ip,),
            )
            result = await service.alert_engine.process_finding(
                finding,
                identity={"user": user, "asset": host},
            )
            alerts.append(service.persist_alert(result.alert))

        # 2) Incidente a partir dos alertas
        incident = await service.create_incident_from_alerts(
            alerts, title="Brute Force SSH em múltiplos ativos"
        )
        if incident is None:
            return SocFlowResult(
                correlation_id="demo",
                alert_ids=tuple(a.id for a in alerts),
                stages={"alerts": len(alerts)},
            )

        # 3) Caso a partir do incidente
        case = await service.create_case_from_incident(incident, owner="analista.soc")

        return SocFlowResult(
            correlation_id=incident.id,
            alert_ids=tuple(a.id for a in alerts),
            incident_id=incident.id,
            case_id=case.id,
            stages={
                "alerts": len(alerts),
                "incident": 1,
                "case": 1,
                "persisted_events": service.event_store.repository.count(),
            },
        )

    @staticmethod
    def _parse(raw: RawEvent) -> ParsedEvent:
        """Parseia (RFC5424 → RFC3164) e cria um ``ParsedEvent``."""
        result = parse_rfc5424(raw)
        if not result.is_ok():
            result = parse_syslog(raw)
        fields = result.unwrap() if result.is_ok() else {}
        return ParsedEvent(
            event_id=raw.event_id,
            timestamp=raw.received_at,
            source_type=raw.source_type,
            source_host=raw.source_host,
            event_category=str(fields.get("event_category", "system")),
            event_action=str(fields.get("event_action", "info")),
            fields=fields,
            raw=raw.raw_payload,
            trace_id=raw.event_id,
        )


__all__ = ["SocFlowResult", "SocPipeline"]
