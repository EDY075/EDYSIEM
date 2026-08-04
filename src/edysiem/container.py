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

from typing import Any

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

    # --- Utilitarios -------------------------------------------------------

    def resolve(self, interface: type[Any]) -> Any:
        """Resolve uma interface registrada no container DI."""
        return self._di.resolve(interface)

    def version(self) -> str:
        """Versao da plataforma."""
        from . import __version__

        return __version__


__all__ = ["ApplicationContainer"]
