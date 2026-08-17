"""Application Container do EDY SIEM.

Container unico que conecta todos os engines da plataforma:
- Ingestion (parsers + normalizer)
- Enrichment Engine
- Correlation Engine
- Detection Engine (Rule Engine + DSL)
- Alert Engine
- Incident Engine
- Case Engine (Investigation Workspace)

Usa o ``Container`` de DI do nucleo (singletons) e expoe accessors
tipados. O mesmo container alimenta a API e o CLI.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .alerts import AlertContext, AlertEngine, AlertRegistry
from .cases import CaseBuilder, CaseContext, CaseEngine, CaseRegistry
from .config import SiemConfig, load
from .correlation import (
    CorrelationContext,
    CorrelationEngine,
    CorrelationRegistry,
)
from .detection import (
    DetectionContext,
    DetectionEngine,
    DetectionRegistry,
    RuleEngine,
)
from .di import Container
from .enrichment import (
    EnrichmentContext,
    EnrichmentEngine,
    EnrichmentRegistry,
)
from .incidents import (
    GroupingEngine,
    IncidentContext,
    IncidentCorrelator,
    IncidentEngine,
    IncidentRegistry,
)
from .ingestion.metrics import MetricsRegistry
from .normalization import Registry as NormalizationRegistry
from .normalization import StrategyNormalizer, register_default_normalizers

if TYPE_CHECKING:
    from .persistence import AuditEngine, ConnectionManager, ShieldInboxRepository
    from .soc import SocPipeline, SocService


class ApplicationContainer:
    """Container que conecta todos os engines da plataforma.

    Todos os engines sao singletons registrados no ``Container`` de DI.
    Args:
        config: Configuracao (default: carrega do ambiente).
    """

    def __init__(self, config: SiemConfig | None = None) -> None:
        self._config = config if config is not None else load().unwrap()
        self._di = Container()
        self._metrics = MetricsRegistry()
        self._soc_service: SocService | None = None
        self._soc_pipeline: SocPipeline | None = None
        self._shield_inbox: ShieldInboxRepository | None = None
        self._audit_engine: AuditEngine | None = None
        self._shield_inbox_manager: ConnectionManager | None = None
        self._audit_manager: ConnectionManager | None = None
        self._build()

    def _build(self) -> None:
        """Registra todos os engines como singletons."""
        di = self._di

        # Observabilidade
        di.register_instance(MetricsRegistry, self._metrics)

        # --- Normalizacao (parsers + normalizer) ---
        self._normalizer_registry = NormalizationRegistry()
        register_default_normalizers(self._normalizer_registry)
        normalizer = StrategyNormalizer()
        for source_type, strategy in self._normalizer_registry.strategies().items():
            normalizer.register(source_type, strategy)
        di.register_instance(StrategyNormalizer, normalizer)

        # --- Enrichment ---
        enrichment_ctx = EnrichmentContext(metrics=self._metrics)
        enrichment_registry = EnrichmentRegistry()
        enrichment_engine = EnrichmentEngine(
            enrichment_registry, enrichment_ctx, metrics=self._metrics
        )
        di.register_instance(EnrichmentContext, enrichment_ctx)
        di.register_instance(EnrichmentRegistry, enrichment_registry)
        di.register_instance(EnrichmentEngine, enrichment_engine)

        # --- Correlation ---
        correlation_ctx = CorrelationContext()
        correlation_registry = CorrelationRegistry()
        correlation_engine = CorrelationEngine(
            correlation_registry, correlation_ctx, metrics=self._metrics
        )
        di.register_instance(CorrelationContext, correlation_ctx)
        di.register_instance(CorrelationRegistry, correlation_registry)
        di.register_instance(CorrelationEngine, correlation_engine)

        # --- Detection ---
        detection_ctx = DetectionContext()
        detection_registry = DetectionRegistry()
        rule_engine = RuleEngine(detection_registry, detection_ctx, metrics=self._metrics)
        detection_engine = DetectionEngine(rule_engine)
        di.register_instance(DetectionContext, detection_ctx)
        di.register_instance(DetectionRegistry, detection_registry)
        di.register_instance(RuleEngine, rule_engine)
        di.register_instance(DetectionEngine, detection_engine)

        # --- Alerts ---
        alert_ctx = AlertContext()
        alert_engine = AlertEngine(registry=AlertRegistry(), context=alert_ctx)
        di.register_instance(AlertContext, alert_ctx)
        di.register_instance(AlertEngine, alert_engine)

        # --- Incidents ---
        incident_ctx = IncidentContext()
        incident_engine = IncidentEngine(
            correlator=IncidentCorrelator(GroupingEngine(), incident_ctx),
            registry=IncidentRegistry(),
            context=incident_ctx,
        )
        di.register_instance(IncidentContext, incident_ctx)
        di.register_instance(IncidentEngine, incident_engine)

        # --- Cases ---
        case_ctx = CaseContext()
        case_engine = CaseEngine(
            builder=CaseBuilder(),
            registry=CaseRegistry(),
            context=case_ctx,
        )
        di.register_instance(CaseContext, case_ctx)
        di.register_instance(CaseEngine, case_engine)

    # --- Configuracao ------------------------------------------------------

    @property
    def config(self) -> SiemConfig:
        """Configuracao da aplicacao."""
        return self._config

    # --- Accessors tipados -------------------------------------------------

    @property
    def metrics(self) -> MetricsRegistry:
        """Registry de metricas da plataforma."""
        return self._metrics

    @property
    def di(self) -> Container:
        """Container DI subjacente."""
        return self._di

    @property
    def normalizer(self) -> StrategyNormalizer:
        """Normalizer (RawEvent -> CanonicalEvent)."""
        return self._di.resolve(StrategyNormalizer)

    @property
    def enrichment(self) -> EnrichmentEngine:
        """Enrichment Engine."""
        return self._di.resolve(EnrichmentEngine)

    @property
    def correlation(self) -> CorrelationEngine:
        """Correlation Engine."""
        return self._di.resolve(CorrelationEngine)

    @property
    def detection(self) -> DetectionEngine:
        """Detection Engine."""
        return self._di.resolve(DetectionEngine)

    @property
    def rule_engine(self) -> RuleEngine:
        """Rule Engine (execucao de DetectionRule)."""
        return self._di.resolve(RuleEngine)

    @property
    def alerts(self) -> AlertEngine:
        """Alert Engine."""
        return self._di.resolve(AlertEngine)

    @property
    def incidents(self) -> IncidentEngine:
        """Incident Engine."""
        return self._di.resolve(IncidentEngine)

    @property
    def cases(self) -> CaseEngine:
        """Case Engine (Investigation Workspace)."""
        return self._di.resolve(CaseEngine)

    # --- SOC (Sprint 2.15) -------------------------------------------------

    @property
    def soc_service(self) -> Any:
        """SocService (persistido) — construído sob demanda.

        Usa ``EDYSIEM_DB`` (default ``edysiem.db``) como arquivo SQLite.
        Engines do container são reutilizados (low coupling).
        """
        if self._soc_service is None:
            import os

            from .soc import SlaPolicy, SocService

            self._soc_service = SocService(
                alert_engine=self.alerts,
                incident_engine=self.incidents,
                case_engine=self.cases,
                version=self.version(),
                db_path=os.environ.get("EDYSIEM_DB") or "edysiem.db",
                sla=SlaPolicy(),
            )
        return self._soc_service

    @property
    def soc_pipeline(self) -> Any:
        """SocPipeline (orquestração E2E) — construído sob demanda."""
        if self._soc_pipeline is None:
            from .soc import SocPipeline

            self._soc_pipeline = SocPipeline(self.soc_service, container=self)
        return self._soc_pipeline

    @property
    def shield_inbox(self) -> ShieldInboxRepository:
        """Durable EDY Shield inbox, built lazily on the configured SIEM database."""

        if self._shield_inbox is None:
            import os

            from .persistence import (
                ALL_MIGRATIONS,
                ConnectionManager,
                MigrationRunner,
                ShieldInboxRepository,
            )

            manager = ConnectionManager(os.environ.get("EDYSIEM_DB") or "edysiem.db")
            MigrationRunner(ALL_MIGRATIONS).apply(manager)
            self._shield_inbox_manager = manager
            self._shield_inbox = ShieldInboxRepository(manager)
        return self._shield_inbox

    @property
    def audit_engine(self) -> AuditEngine:
        """Append-only audit trail over the configured SIEM database."""

        if self._audit_engine is None:
            import os
            from pathlib import Path

            from .persistence import (
                ALL_MIGRATIONS,
                AuditEngine,
                AuditRepository,
                ConnectionManager,
                MigrationRunner,
            )

            primary_path = os.environ.get("EDYSIEM_DB") or "edysiem.db"
            configured_audit_path = os.environ.get("EDYSIEM_AUDIT_DB", "").strip()
            if configured_audit_path:
                audit_path = configured_audit_path
            elif primary_path == ":memory:":
                audit_path = ":memory:"
            else:
                primary = Path(primary_path)
                audit_path = str(
                    primary.with_name(f"{primary.stem}.audit{primary.suffix or '.db'}")
                )
            manager = ConnectionManager(audit_path)
            MigrationRunner(ALL_MIGRATIONS).apply(manager)
            self._audit_manager = manager
            self._audit_engine = AuditEngine(AuditRepository(manager))
        return self._audit_engine

    def close_persistence(self) -> None:
        """Close lazy inbox/audit connections; safe to call repeatedly."""

        if self._shield_inbox_manager is not None:
            self._shield_inbox_manager.close_all()
        if self._audit_manager is not None:
            self._audit_manager.close_all()

    # --- Utilitarios -------------------------------------------------------

    def resolve(self, interface: type[Any]) -> Any:
        """Resolve uma interface registrada no container DI."""
        return self._di.resolve(interface)

    def version(self) -> str:
        """Versao da plataforma."""
        from . import __version__

        return __version__


__all__ = ["ApplicationContainer"]
