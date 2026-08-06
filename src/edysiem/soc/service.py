"""SocService Ã¢â‚¬â€ orquestraÃƒÂ§ÃƒÂ£o SOC persistida (Sprint 2.15).

Ponte de **baixo acoplamento** entre os engines (Alert/Incident/Case) e a
camada de persistÃƒÂªncia SQLite. Os engines seguem operando como working set
in-memory; este serviÃƒÂ§o persiste cada entidade nos repositÃƒÂ³rios e oferece as
operaÃƒÂ§ÃƒÂµes operacionais do SOC:

- Pipeline E2E (evento Ã¢â€ â€™ alerta Ã¢â€ â€™ incidente Ã¢â€ â€™ caso) via ``SocPipeline``
- Incident Management (severidade/status/atribuiÃƒÂ§ÃƒÂ£o/SLA)
- Case Management (comentÃƒÂ¡rios, evidÃƒÂªncias, anexos, tarefas, encerramento)
- Investigation (pivÃƒÂ´s entre alertas, IOCs, contexto enriquecido)
- Dashboard KPIs alimentados por dados reais (``metrics``)
"""

from __future__ import annotations

import sqlite3

# ruff: noqa: RUF002 RUF003 E501
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any

from .._utils import utcnow as _utcnow
from ..alerts import Alert, AlertEngine
from ..cases import Case, CaseEngine, CaseEvidenceKind, CaseStatus
from ..incidents import Incident, IncidentEngine, IncidentStatus
from ..persistence import (
    ALL_MIGRATIONS,
    ConnectionManager,
    EventRepository,
    EventStore,
    MigrationRunner,
    PipelineStage,
    Transaction,
)
from ..persistence.repos import AlertRepository, CaseRepository, IncidentRepository
from .sla import SlaPolicy, SlaSnapshot, compute_sla


class SocService:
    """Orquestrador SOC persistido construÃƒÂ­do sobre os engines da plataforma."""

    def __init__(
        self,
        *,
        alert_engine: AlertEngine | None = None,
        incident_engine: IncidentEngine | None = None,
        case_engine: CaseEngine | None = None,
        version: str = "0.2.0",
        db_path: str = ":memory:",
        sla: SlaPolicy | None = None,
    ) -> None:
        self._alert_engine = alert_engine or AlertEngine()
        self._incident_engine = incident_engine or IncidentEngine()
        self._case_engine = case_engine or CaseEngine()
        self._version = version
        self._sla = sla or SlaPolicy()

        self._manager = ConnectionManager(db_path)
        MigrationRunner(ALL_MIGRATIONS).apply(self._manager)
        self._alerts = AlertRepository(self._manager)
        self._incidents = IncidentRepository(self._manager)
        self._cases = CaseRepository(self._manager)
        self._event_store = EventStore(EventRepository(self._manager), version=version)

    # --- Engines -----------------------------------------------------------

    @property
    def alert_engine(self) -> AlertEngine:
        """Alert Engine (working set in-memory)."""
        return self._alert_engine

    @property
    def incident_engine(self) -> IncidentEngine:
        """Incident Engine."""
        return self._incident_engine

    @property
    def case_engine(self) -> CaseEngine:
        """Case Engine."""
        return self._case_engine

    @property
    def event_store(self) -> EventStore:
        """Event Store da pipeline."""
        return self._event_store

    # --- Detection Engineering + Threat Intel (Sprint 2.17) -----------------

    def register_rule(
        self,
        *,
        rule_id: str,
        name: str = "",
        severity: str = "medium",
        category: str = "",
        mitre: tuple[str, ...] = (),
        tags: tuple[str, ...] = (),
        description: str = "",
        enabled: bool = True,
    ) -> dict[str, Any]:
        """Registra/atualiza uma regra no catÃƒÂ¡logo persistido."""
        conn = self._manager.connect()
        import json as _json

        with Transaction(conn):
            conn.execute(
                "INSERT INTO det_rules (rule_id, name, severity, category, mitre, tags, description, enabled) "
                "VALUES (?,?,?,?,?,?,?,?) "
                "ON CONFLICT(rule_id) DO UPDATE SET name=excluded.name, severity=excluded.severity, "
                "category=excluded.category, mitre=excluded.mitre, tags=excluded.tags, description=excluded.description, enabled=excluded.enabled",
                (
                    rule_id,
                    name,
                    severity,
                    category,
                    _json.dumps(list(mitre)),
                    _json.dumps(list(tags)),
                    description,
                    1 if enabled else 0,
                ),
            )
        return self.get_rule(rule_id) or {}

    def get_rule(self, rule_id: str) -> dict[str, Any] | None:
        conn = self._manager.connect()
        row = conn.execute("SELECT * FROM det_rules WHERE rule_id = ?", (rule_id,)).fetchone()
        return self._rule_row(row) if row else None

    def list_rules(self) -> list[dict[str, Any]]:
        conn = self._manager.connect()
        rows = conn.execute("SELECT * FROM det_rules ORDER BY rule_id").fetchall()
        return [self._rule_row(r) for r in rows]

    def set_rule_enabled(self, rule_id: str, enabled: bool) -> dict[str, Any] | None:
        conn = self._manager.connect()
        with Transaction(conn):
            conn.execute(
                "UPDATE det_rules SET enabled=? WHERE rule_id=?", (1 if enabled else 0, rule_id)
            )
        return self.get_rule(rule_id)

    def rule_apply(self, rule_id: str, fired_at: datetime | None = None) -> None:
        """Incrementa o contador de disparos de uma regra."""
        conn = self._manager.connect()
        with Transaction(conn):
            conn.execute(
                "UPDATE det_rules SET fire_count = fire_count + 1, last_fired = ? WHERE rule_id = ?",
                ((fired_at or _utcnow()).isoformat(), rule_id),
            )

    def simulate_rule(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Simula a aplicaÃƒÂ§ÃƒÂ£o de regras sobre um evento JSON (sem tocar a pipeline)."""
        payload_lower = {k.strip().lower(): v for k, v in payload.items()}
        text = " ".join(str(v).lower() for v in payload.values())
        results: list[dict[str, Any]] = []
        for rule in self.list_rules():
            if not rule.get("enabled", True):
                continue
            matched = False
            reason = "sem correspondÃƒÂªncia"
            if payload_lower.get("rule_id") and rule["rule_id"] in str(payload_lower["rule_id"]):
                matched = True
                reason = "payload cita a regra"
            if rule.get("category") and rule["category"].lower() in text:
                matched = True
                reason = f"categoria '{rule['category']}' detectada"
            if any(tag.lower() in text for tag in (rule.get("tags") or [])):
                matched = True
                reason = "tag correspondente"
            if matched:
                score = {"critical": 90, "high": 75, "medium": 50, "low": 25}.get(
                    rule["severity"], 50
                )
                results.append(
                    {
                        "rule_id": rule["rule_id"],
                        "applied": True,
                        "severity": rule["severity"],
                        "score": score,
                        "reason": reason,
                        "alert_generated": True,
                    }
                )
        return results

    @staticmethod
    def _rule_row(row: sqlite3.Row) -> dict[str, Any]:
        import json as _json

        return {
            "rule_id": row["rule_id"],
            "name": row["name"],
            "severity": row["severity"],
            "category": row["category"],
            "mitre": _json.loads(row["mitre"]),
            "tags": _json.loads(row["tags"]),
            "description": row["description"],
            "enabled": bool(row["enabled"]),
            "fire_count": row["fire_count"],
            "last_fired": row["last_fired"],
        }

    # --- IOC Intelligence ----------------------------------------------------

    def register_ioc(
        self,
        value: str,
        ioc_type: str,
        *,
        reputation: str = "unknown",
        source: str = "analyst",
        labels: tuple[str, ...] = (),
    ) -> dict[str, Any]:
        """Registra/atualiza um IOC (IP/domÃƒÂ­nio/URL/hash/e-mail)."""
        conn = self._manager.connect()
        import json as _json

        now = _utcnow().isoformat()
        with Transaction(conn):
            conn.execute(
                "INSERT INTO iocs (value, ioc_type, reputation, source, first_seen, last_seen, hits, labels) "
                "VALUES (?,?,?,?,?,?,1,?) "
                "ON CONFLICT(value) DO UPDATE SET reputation=excluded.reputation, source=excluded.source, "
                "last_seen=excluded.last_seen, hits=iocs.hits+1, labels=excluded.labels",
                (value, ioc_type, reputation, source, now, now, _json.dumps(list(labels))),
            )
        return self.get_ioc(value) or {}

    def get_ioc(self, value: str) -> dict[str, Any] | None:
        conn = self._manager.connect()
        row = conn.execute("SELECT * FROM iocs WHERE value = ?", (value,)).fetchone()
        return self._ioc_row(row) if row else None

    def list_iocs(self, *, ioc_type: str | None = None) -> list[dict[str, Any]]:
        conn = self._manager.connect()
        sql = "SELECT * FROM iocs"
        params: tuple[Any, ...] = ()
        if ioc_type:
            sql += " WHERE ioc_type = ?"
            params = (ioc_type,)
        rows = conn.execute(sql + " ORDER BY last_seen DESC", params).fetchall()
        return [self._ioc_row(r) for r in rows]

    def ioc_related(self, value: str) -> dict[str, Any]:
        """Incidentes e casos relacionados a um IOC."""
        cases = [c for c in self.list_cases(limit=10000) if value in c.iocs]
        incidents = [i for i in self.list_incidents(limit=10000) if value in i.iocs]
        return {
            "incidents": [
                {"incident_id": i.id, "title": i.title, "severity": i.severity.value}
                for i in incidents
            ],
            "cases": [{"case_id": c.id, "title": c.title, "status": c.status.value} for c in cases],
        }

    @staticmethod
    def _ioc_row(row: sqlite3.Row) -> dict[str, Any]:
        import json as _json

        return {
            "value": row["value"],
            "ioc_type": row["ioc_type"],
            "reputation": row["reputation"],
            "source": row["source"],
            "first_seen": row["first_seen"],
            "last_seen": row["last_seen"],
            "hits": row["hits"],
            "labels": _json.loads(row["labels"]),
        }

    # --- Asset Inventory ------------------------------------------------------

    def register_asset(
        self,
        hostname: str,
        *,
        ip: str = "",
        os_name: str = "",
        criticality: str = "medium",
        owner: str = "",
        status: str = "active",
        now: datetime | None = None,
    ) -> dict[str, Any]:
        """Registra/atualiza um asset do inventÃƒÂ¡rio."""
        conn = self._manager.connect()
        last_seen = (now or _utcnow()).isoformat()
        with Transaction(conn):
            conn.execute(
                "INSERT INTO assets (hostname, ip, os, criticality, owner, status, last_seen) VALUES (?,?,?,?,?,?,?) "
                "ON CONFLICT(hostname) DO UPDATE SET ip=excluded.ip, os=excluded.os, "
                "criticality=excluded.criticality, owner=excluded.owner, status=excluded.status, last_seen=excluded.last_seen",
                (hostname, ip, os_name, criticality, owner, status, last_seen),
            )
        return self.get_asset(hostname) or {}

    def get_asset(self, hostname: str) -> dict[str, Any] | None:
        conn = self._manager.connect()
        row = conn.execute("SELECT * FROM assets WHERE hostname = ?", (hostname,)).fetchone()
        return self._asset_row(row) if row else None

    def list_assets(self, *, criticality: str | None = None) -> list[dict[str, Any]]:
        conn = self._manager.connect()
        sql = "SELECT * FROM assets"
        params: tuple[Any, ...] = ()
        if criticality:
            sql += " WHERE criticality = ?"
            params = (criticality,)
        rows = conn.execute(sql + " ORDER BY hostname", params).fetchall()
        return [self._asset_row(r) for r in rows]

    def asset_related(self, hostname: str) -> dict[str, Any]:
        """Incidentes e casos que citam o asset."""
        incidents = [i for i in self.list_incidents(limit=10000) if hostname in i.assets]
        cases = [c for c in self.list_cases(limit=10000) if hostname in c.assets]
        return {
            "incidents": [{"incident_id": i.id, "title": i.title} for i in incidents],
            "cases": [{"case_id": c.id, "title": c.title, "status": c.status.value} for c in cases],
        }

    @staticmethod
    def _asset_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "hostname": row["hostname"],
            "ip": row["ip"],
            "os": row["os"],
            "criticality": row["criticality"],
            "owner": row["owner"],
            "status": row["status"],
            "last_seen": row["last_seen"],
        }

    # --- Detection Dashboard ---------------------------------------------------

    def detection_stats(self) -> dict[str, Any]:
        """AgregaÃƒÂ§ÃƒÂµes para o Detection Dashboard (dados reais)."""
        alerts = self.list_alerts(limit=10000)
        rules = self.list_rules()

        alerts_by_rule: dict[str, int] = {}
        mitre: dict[str, int] = {}
        iocs: dict[str, int] = {}
        for a in alerts:
            alerts_by_rule[a.rule_id] = alerts_by_rule.get(a.rule_id, 0) + 1
            for m in a.mitre:
                mitre[m] = mitre.get(m, 0) + 1
            for ioc in a.ioc_ids:
                iocs[ioc] = iocs.get(ioc, 0) + 1

        return {
            "top_rules": [
                {"rule_id": k, "count": v}
                for k, v in sorted(alerts_by_rule.items(), key=lambda x: -x[1])[:10]
            ],
            "rules_total": len(rules),
            "rules_enabled": sum(1 for r in rules if r["enabled"]),
            "top_mitre": [
                {"mitre": k, "count": v} for k, v in sorted(mitre.items(), key=lambda x: -x[1])[:10]
            ],
            "top_iocs": [
                {"value": k, "count": v} for k, v in sorted(iocs.items(), key=lambda x: -x[1])[:10]
            ],
            "critical_assets": [a["hostname"] for a in self.list_assets(criticality="critical")],
            "alerts_by_rule": alerts_by_rule,
            "trend": [
                {"time": p["time"], "events": p["events"]}
                for p in self.metrics()["metrics"]["events_series"]
            ],
        }

    # --- Persistencia (ponte engines -> repos) ------------------------------

    def persist_alert(self, alert: Alert) -> Alert:
        """Insere ou atualiza um alerta no repositÃƒÂ³rio (transaÃƒÂ§ÃƒÂ£o atÃƒÂ´mica)."""
        with Transaction(self._manager.connect()):
            if self._alerts.get(alert.id) is None:
                self._alerts.add(alert)
            else:
                self._alerts.update(alert)
            self._event_store.record_event(PipelineStage.ALERT, alert, alert.id)
            self._manager.connect().execute(
                "UPDATE det_rules SET fire_count = fire_count + 1, last_fired = ? WHERE rule_id = ?",
                (_utcnow().isoformat(), alert.rule_id),
            )
        return alert

    def persist_incident(self, incident: Incident) -> Incident:
        """Insere ou atualiza um incidente no repositÃƒÂ³rio (transaÃƒÂ§ÃƒÂ£o atÃƒÂ´mica)."""
        with Transaction(self._manager.connect()):
            if self._incidents.get(incident.id) is None:
                self._incidents.add(incident)
            else:
                self._incidents.update(incident)
            self._event_store.record_event(
                PipelineStage.INCIDENT, incident, correlation_id=incident.id
            )
        return incident

    def persist_case(self, case: Case) -> Case:
        """Insere ou atualiza um caso no repositÃƒÂ³rio (transaÃƒÂ§ÃƒÂ£o atÃƒÂ´mica)."""
        with Transaction(self._manager.connect()):
            if self._cases.get(case.id) is None:
                self._cases.add(case)
            else:
                self._cases.update(case)
            self._event_store.record_event(
                PipelineStage.CASE, case, correlation_id=case.incident_id or case.id
            )
        return case

    # --- Pipeline de criaÃƒÂ§ÃƒÂ£o -----------------------------------------------

    async def create_incident_from_alerts(
        self,
        alerts: list[Alert],
        *,
        title: str | None = None,
    ) -> Incident | None:
        """Agrupa alertas em um incidente via Incident Engine e persiste."""
        result = await self._incident_engine.process_alerts(alerts, title=title)
        if result.incident is None:
            return None
        return self.persist_incident(result.incident)

    async def create_case_from_incident(
        self,
        incident: Incident,
        *,
        title: str | None = None,
        owner: str | None = None,
    ) -> Case:
        """Cria um caso a partir de um incidente via Case Engine e persiste."""
        result = await self._case_engine.create_from_incident(incident, title=title, owner=owner)
        return self.persist_case(result.case)

    # --- Consulta ----------------------------------------------------------

    def get_alert(self, alert_id: str) -> Alert | None:
        """Busca alerta persistido."""
        return self._alerts.get(alert_id)

    def get_incident(self, incident_id: str) -> Incident | None:
        """Busca incidente persistido."""
        return self._incidents.get(incident_id)

    def get_case(self, case_id: str) -> Case | None:
        """Busca caso persistido."""
        return self._cases.get(case_id)

    def list_alerts(self, *, limit: int = 50, offset: int = 0) -> list[Alert]:
        """Lista alertas persistidos (mais recentes primeiro)."""
        return list(self._alerts.query(limit=limit, offset=offset).items)

    def list_incidents(self, *, limit: int = 50, offset: int = 0) -> list[Incident]:
        """Lista incidentes persistidos."""
        return list(self._incidents.query(limit=limit, offset=offset).items)

    def list_cases(self, *, limit: int = 50, offset: int = 0) -> list[Case]:
        """Lista casos persistidos."""
        return list(self._cases.query(limit=limit, offset=offset).items)

    # --- Incident Management ------------------------------------------------

    def transition_incident(
        self,
        incident_id: str,
        target: IncidentStatus,
        *,
        actor: str = "system",
    ) -> Incident:
        """Aplica transiÃƒÂ§ÃƒÂ£o de estado (validada) a um incidente persistido."""
        incident = self._require_incident(incident_id)
        if not incident.status.can_transition_to(target):
            from ..incidents import IncidentInvalidStateTransition

            raise IncidentInvalidStateTransition(incident.status.value, target.value)
        updated = replace(incident, status=target)
        # mantÃƒÂ©m o working set do engine em sincronia
        self._incident_engine.context.save(updated)
        return self.persist_incident(updated)

    def assign_incident_analyst(
        self, incident_id: str, analyst: str, *, actor: str = "system"
    ) -> Incident:
        """Atribui um analista responsÃƒÂ¡vel ao incidente."""
        incident = self._require_incident(incident_id)
        updated = replace(incident, owner=analyst)
        self._incident_engine.context.save(updated)
        return self.persist_incident(updated)

    # --- Case Management ----------------------------------------------------

    def add_case_comment(self, case_id: str, body: str, author: str) -> Case:
        """Adiciona um comentÃƒÂ¡rio/nota ao caso."""
        case = self._apply_case_op(
            case_id,
            lambda c: self._case_engine.comments.add(c, body, author),
        )
        return self.persist_case(case)

    def add_case_evidence(
        self,
        case_id: str,
        kind: CaseEvidenceKind,
        value: str,
        *,
        label: str = "",
        source: str = "analyst",
    ) -> Case:
        """Anexa uma evidÃƒÂªncia ao caso."""
        case = self._apply_case_op(
            case_id,
            lambda c: self._case_engine.evidence.add(c, kind, value, label=label, source=source),
        )
        return self.persist_case(case)

    def add_case_attachment(
        self,
        case_id: str,
        name: str,
        *,
        content_type: str = "",
        size: int = 0,
        url: str = "",
        added_by: str = "system",
    ) -> Case:
        """Anexa um arquivo/URL ao caso."""
        case = self._apply_case_op(
            case_id,
            lambda c: self._case_engine.attachments.add(
                c, name, content_type=content_type, size=size, url=url, added_by=added_by
            ),
        )
        return self.persist_case(case)

    def assign_case_owner(self, case_id: str, owner: str, *, assigned_by: str = "system") -> Case:
        """Transfere o responsÃƒÂ¡vel do caso."""
        case = self._apply_case_op(
            case_id, lambda c: self._case_engine.owners.transfer(c, owner, assigned_by=assigned_by)
        )
        return self.persist_case(case)

    def resolve_case(self, case_id: str, resolution: str, *, actor: str = "system") -> Case:
        """Resolve um caso registrando a resoluÃƒÂ§ÃƒÂ£o."""
        case = self._apply_case_op(case_id, lambda c: replace(c, resolution=resolution))
        updated = self._case_engine.timeline.record_resolution(case, actor=actor)
        return self.persist_case(updated)

    def close_case(
        self, case_id: str, resolution: str | None = None, *, actor: str = "system"
    ) -> Case:
        """Encerra um caso (RESOLVED -> CLOSED), registrando resoluÃƒÂ§ÃƒÂ£o e data."""
        case = self._require_case(case_id)
        if not case.status.can_transition_to(CaseStatus.CLOSED):
            from ..cases import CaseInvalidStateTransition

            raise CaseInvalidStateTransition(case.status.value, CaseStatus.CLOSED.value)
        updated = replace(case, status=CaseStatus.CLOSED, closed_at=_utcnow())
        if resolution:
            updated = replace(updated, resolution=resolution)
        updated = self._case_engine.timeline.record_status_change(
            updated, case.status, CaseStatus.CLOSED, actor=actor
        )
        self._case_engine.context.save(updated)
        return self.persist_case(updated)

    def _require_incident(self, incident_id: str) -> Incident:
        incident = self.get_incident(incident_id)
        if incident is None:
            from ..persistence import RecordNotFoundError

            raise RecordNotFoundError(kind="incident", record_id=incident_id)
        return incident

    def _require_case(self, case_id: str) -> Case:
        case = self.get_case(case_id)
        if case is None:
            from ..persistence import RecordNotFoundError

            raise RecordNotFoundError(kind="case", record_id=case_id)
        return case

    def _apply_case_op(self, case_id: str, op: Callable[[Case], Case]) -> Case:
        """Aplica uma operaÃƒÂ§ÃƒÂ£o engine sobre um caso persistido (sincronizando contexto)."""
        case = self._require_case(case_id)
        self._case_engine.context.save(case)
        return op(case)

    # --- Investigation ------------------------------------------------------

    def investigate(self, case_id: str) -> dict[str, Any]:
        """PivÃƒÂ´s de investigaÃƒÂ§ÃƒÂ£o de um caso: alertas/IOCs/assets/contexto."""
        case = self._require_case(case_id)
        related_alerts = [
            self._alert_summary(a)
            for a in (self._alerts.get(i) for i in case.alerts)
            if a is not None
        ]
        trail = (
            self._event_store.repository.by_correlation(case.incident_id)
            if case.incident_id
            else []
        )
        return {
            "case_id": case.id,
            "title": case.title,
            "status": case.status.value,
            "owner": case.owner,
            "severity": case.severity.value,
            "related_alerts": related_alerts,
            "iocs": list(case.iocs),
            "assets": list(case.assets),
            "users": list(case.users),
            "mitre": list(case.mitre),
            "timeline": [
                {
                    "action": e.action,
                    "detail": e.detail,
                    "actor": e.actor,
                    "created_at": e.created_at.isoformat(),
                }
                for e in case.timeline
            ],
            "evidence": [
                {"kind": e.kind.value, "value": e.value, "label": e.label} for e in case.evidences
            ],
            "pipeline_trail": [
                {
                    "stage": ev.pipeline_stage,
                    "event_type": ev.event_type,
                    "timestamp": ev.timestamp.isoformat(),
                }
                for ev in trail
            ],
        }

    def _alert_summary(self, alert: Alert) -> dict[str, Any]:
        return {
            "alert_id": alert.id,
            "title": alert.title,
            "rule_id": alert.rule_id,
            "severity": alert.severity.value,
            "risk_score": alert.risk_score.value,
            "status": alert.status.value,
            "host": alert.source,
        }

    # --- SLA -----------------------------------------------------------------

    def sla_of(self, entity: Alert | Incident | Case) -> SlaSnapshot:
        """SLA de uma entidade (por severidade e datas de criaÃƒÂ§ÃƒÂ£o/encerramento)."""
        if isinstance(entity, Alert):
            closed_at: datetime | None = None
        else:
            closed_at = entity.closed_at
        return compute_sla(
            str(entity.severity.value),
            created_at=entity.created_at,
            closed_at=closed_at,
            policy=self._sla,
        )

    # --- MÃƒÂ©tricas reais (dashboard) ------------------------------------------

    def metrics(self) -> dict[str, Any]:
        """KPIs do dashboard alimentados por dados reais da persistÃƒÂªncia."""
        alerts = self.list_alerts(limit=10000)
        incidents = self.list_incidents(limit=10000)
        cases = self.list_cases(limit=10000)

        def _count(severity: str) -> int:
            return sum(1 for a in alerts if a.severity.value == severity)

        open_cases = [c for c in cases if c.status.value not in ("closed", "resolved")]
        closed_cases = [c for c in cases if c.closed_at is not None]
        mttr_seconds = (
            int(
                sum(
                    (c.closed_at - c.created_at).total_seconds() if c.closed_at else 0
                    for c in closed_cases
                )
                / len(closed_cases)
            )
            if closed_cases
            else 0
        )
        avg_risk = round(sum(a.risk_score.value for a in alerts) / len(alerts)) if alerts else 0

        # SÃƒÂ©rie temporal real (eventos por minuto, ÃƒÂºltimos 60 min) Ã¢â‚¬â€ Dashboard Vivo
        events = self._event_store.repository.query(limit=20000).items
        now = _utcnow()
        minute_now = int(now.timestamp() // 60)
        buckets: dict[int, int] = {}
        for ev in events:
            minute = int(ev.timestamp.timestamp() // 60)
            if minute <= minute_now and minute_now - minute < 60:
                buckets[minute] = buckets.get(minute, 0) + 1
        series: list[dict[str, Any]] = []
        for offset in range(59, -1, -1):
            minute = minute_now - offset
            dt = datetime.fromtimestamp(minute * 60, tz=UTC)
            series.append({"time": dt.strftime("%H:%M"), "events": buckets.get(minute, 0)})

        recent_window = sum(buckets.get(minute_now - offset, 0) for offset in range(5))
        eps = round(recent_window / 300, 2) if events else 0.0
        events_last_24h = sum(1 for ev in events if ev.timestamp >= now - timedelta(hours=24))

        return {
            "metrics": {
                "events_per_second": eps,
                "events_per_minute": float(self._event_store.repository.count()),
                "events_last_24h": events_last_24h,
                "active_alerts": sum(1 for a in alerts if a.status.value != "resolved"),
                "open_cases": len(open_cases),
                "mttr_seconds": mttr_seconds,
                "mtta_seconds": 0,
                "avg_risk_score": avg_risk,
                "events_series": series,
            },
            "components": {
                "total_alerts": len(alerts),
                "alerts_open": sum(1 for a in alerts if a.status.value == "open"),
                "alerts_by_severity": {
                    "critical": _count("critical"),
                    "high": _count("high"),
                    "medium": _count("medium"),
                    "low": _count("low"),
                },
                "total_incidents": len(incidents),
                "incidents_open": sum(1 for i in incidents if i.status.value != "closed"),
                "incidents_critical": sum(1 for i in incidents if i.severity.value == "critical"),
                "total_cases": len(cases),
                "cases_open": len(open_cases),
                "cases_closed": len(closed_cases),
                "avg_risk_score": avg_risk,
                "sla_policy_hours": {
                    "critical": self._sla.critical_hours,
                    "high": self._sla.high_hours,
                    "medium": self._sla.medium_hours,
                    "low": self._sla.low_hours,
                },
            },
        }


__all__ = ["SocService"]
