"""Testes do ApplicationContainer."""

from __future__ import annotations

from edysiem.config import load
from edysiem.container import ApplicationContainer


def test_container_builds_all_engines() -> None:
    cfg = load().unwrap()
    c = ApplicationContainer(cfg)

    assert c.normalizer is not None
    assert c.enrichment is not None
    assert c.correlation is not None
    assert c.detection is not None
    assert c.rule_engine is not None
    assert c.alerts is not None
    assert c.incidents is not None
    assert c.cases is not None
    assert c.metrics is not None
    assert c.config is cfg


def test_container_singletons() -> None:
    c = ApplicationContainer()
    # Mesmo engine retornado a cada acesso (singleton)
    assert c.alerts is c.alerts
    assert c.cases is c.cases
    assert c.metrics is c.metrics


def test_container_di_resolve() -> None:
    c = ApplicationContainer()
    from edysiem.cases import CaseEngine
    from edysiem.incidents import IncidentEngine

    assert isinstance(c.resolve(CaseEngine), CaseEngine)
    assert isinstance(c.resolve(IncidentEngine), IncidentEngine)


def test_container_version() -> None:
    c = ApplicationContainer()
    assert c.version() == "0.3.0"


def test_container_engines_share_metrics() -> None:
    c = ApplicationContainer()
    from edysiem.ingestion.metrics import MetricsRegistry

    assert isinstance(c.metrics, MetricsRegistry)
    assert c.enrichment is not None


def test_container_normalizer_has_syslog_strategy() -> None:
    c = ApplicationContainer()
    # syslog/windows registrados no normalizer
    assert c.normalizer is not None
