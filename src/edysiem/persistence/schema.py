"""Schema SQL v1 da persistencia.

Tabelas: alerts, incidents, cases. Colunas JSON para estruturas aninhadas
(timeline, evidences, comments, tasks, etc.). Indices basicos para consultas SOC.
"""

from __future__ import annotations

import sqlite3

from .migrations import Migration

_CREATE_ALERTS = """
CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    severity TEXT NOT NULL,
    priority TEXT NOT NULL,
    risk_score INTEGER NOT NULL,
    confidence REAL NOT NULL,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    occurrences INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'detection',
    rule_id TEXT NOT NULL DEFAULT '',
    fingerprint_hash TEXT,
    fingerprint_key TEXT,
    event_ids TEXT NOT NULL DEFAULT '[]',
    tags TEXT NOT NULL DEFAULT '[]',
    mitre TEXT NOT NULL DEFAULT '[]',
    asset_id TEXT,
    user TEXT,
    ioc_ids TEXT NOT NULL DEFAULT '[]',
    timeline TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_alerts_rule ON alerts(rule_id);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts(created_at);
CREATE UNIQUE INDEX IF NOT EXISTS idx_alerts_fingerprint ON alerts(fingerprint_hash);
"""

_CREATE_INCIDENTS = """
CREATE TABLE IF NOT EXISTS incidents (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    severity TEXT NOT NULL,
    priority TEXT NOT NULL,
    risk_score INTEGER NOT NULL,
    confidence REAL NOT NULL,
    status TEXT NOT NULL,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    closed_at TEXT,
    occurrences INTEGER NOT NULL DEFAULT 1,
    alerts TEXT NOT NULL DEFAULT '[]',
    assets TEXT NOT NULL DEFAULT '[]',
    users TEXT NOT NULL DEFAULT '[]',
    iocs TEXT NOT NULL DEFAULT '[]',
    mitre TEXT NOT NULL DEFAULT '[]',
    tactics TEXT NOT NULL DEFAULT '[]',
    techniques TEXT NOT NULL DEFAULT '[]',
    tags TEXT NOT NULL DEFAULT '[]',
    timeline TEXT NOT NULL DEFAULT '[]',
    owner TEXT,
    fingerprint_hash TEXT,
    fingerprint_key TEXT,
    reason TEXT NOT NULL DEFAULT '{}',
    evidence TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);
CREATE INDEX IF NOT EXISTS idx_incidents_severity ON incidents(severity);
CREATE INDEX IF NOT EXISTS idx_incidents_created ON incidents(created_at);
"""

_CREATE_CASES = """
CREATE TABLE IF NOT EXISTS cases (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    owner TEXT,
    status TEXT NOT NULL,
    severity TEXT NOT NULL,
    priority TEXT NOT NULL,
    risk_score INTEGER NOT NULL,
    incident_id TEXT,
    alerts TEXT NOT NULL DEFAULT '[]',
    assets TEXT NOT NULL DEFAULT '[]',
    users TEXT NOT NULL DEFAULT '[]',
    iocs TEXT NOT NULL DEFAULT '[]',
    mitre TEXT NOT NULL DEFAULT '[]',
    timeline TEXT NOT NULL DEFAULT '[]',
    comments TEXT NOT NULL DEFAULT '[]',
    attachments TEXT NOT NULL DEFAULT '[]',
    tasks TEXT NOT NULL DEFAULT '[]',
    evidences TEXT NOT NULL DEFAULT '[]',
    playbook TEXT,
    resolution TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    closed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(status);
CREATE INDEX IF NOT EXISTS idx_cases_incident ON cases(incident_id);
CREATE INDEX IF NOT EXISTS idx_cases_created ON cases(created_at);
"""


_CREATE_EVENTS = """
CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    pipeline_stage TEXT NOT NULL,
    version TEXT NOT NULL,
    source TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_correlation ON events(correlation_id);
CREATE INDEX IF NOT EXISTS idx_events_stage ON events(pipeline_stage);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
"""


class SchemaV1(Migration):
    """Versao 1 do schema: alerts, incidents, cases."""

    version = 1
    description = "tabelas iniciais: alerts, incidents, cases"

    def up(self, conn: sqlite3.Connection) -> None:
        conn.executescript(_CREATE_ALERTS)
        conn.executescript(_CREATE_INCIDENTS)
        conn.executescript(_CREATE_CASES)


class SchemaV2(Migration):
    """Versao 2 do schema: tabela de eventos (Event Store)."""

    version = 2
    description = "event store: tabela events"

    def up(self, conn: sqlite3.Connection) -> None:
        conn.executescript(_CREATE_EVENTS)


ALL_MIGRATIONS: list[Migration] = [SchemaV1(), SchemaV2()]

__all__ = ["ALL_MIGRATIONS", "SchemaV1", "SchemaV2"]
