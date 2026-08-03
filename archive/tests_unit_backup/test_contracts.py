"""Testes de contratos de plugins (verificação de Protocol via implementação concreta)."""

from datetime import datetime, timezone

from app.core.contracts import AnalyzerPlugin, CollectorPlugin, EnrichmentPlugin, ExporterPlugin, ParserPlugin
from app.core.models import CanonicalEvent, Severity
from app.core.result import Result, success

TS = datetime(2026, 1, 1, tzinfo=timezone.utc)


class SyslogParser(ParserPlugin):
    name = "syslog"
    source_types = ("syslog",)

    def parse(self, source_type: str, payload: str) -> Result[dict]:
        return success({"message": payload})


class FileCollector(CollectorPlugin):
    name = "file"

    def collect(self) -> Result[list[dict]]:
        return success([{"line": 1}])


class GeoEnricher(EnrichmentPlugin):
    name = "geo"

    def enrich(self, event: CanonicalEvent) -> Result[dict]:
        return success({"geo": "br"})


class EntropyAnalyzer(AnalyzerPlugin):
    name = "entropy"

    def analyze(self, event: CanonicalEvent) -> Result[dict]:
        return success({"score": 0.5})


class JsonExporter(ExporterPlugin):
    name = "json"
    formats = ("json",)

    def export(self, data: dict, fmt: str) -> Result[str]:
        return success("{}")


def test_parser_contract() -> None:
    p = SyslogParser()
    assert p.source_types == ("syslog",)
    r = p.parse("syslog", "hello")
    assert r.is_success


def test_collector_contract() -> None:
    c = FileCollector()
    r = c.collect()
    assert r.is_success and r.unwrap() == [{"line": 1}]


def test_enricher_contract() -> None:
    e = GeoEnricher()
    ev = CanonicalEvent(event_id="e", timestamp="t", source_type="s", source_host="h")
    r = e.enrich(ev)
    assert r.is_success and r.unwrap() == {"geo": "br"}


def test_analyzer_contract() -> None:
    a = EntropyAnalyzer()
    ev = CanonicalEvent(event_id="e", timestamp="t", source_type="s", source_host="h")
    r = a.analyze(ev)
    assert r.is_success


def test_exporter_contract() -> None:
    x = JsonExporter()
    assert x.formats == ("json",)
    r = x.export({}, "json")
    assert r.is_success


def test_event_severity_default() -> None:
    ev = CanonicalEvent(event_id="e", timestamp="t", source_type="s", source_host="h")
    assert ev.severity == Severity.INFO
