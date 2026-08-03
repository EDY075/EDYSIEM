# EDY SIEM — Database

> Modelo de dados. Acesso exclusivo pela camada `persistence` (ver ADR-002).
> Cada agregado é uma tabela com repositório próprio.

## 1. Entidades

### events
- `event_id` TEXT PK
- `timestamp` TEXT (ISO UTC)
- `source_type` TEXT (syslog, apache, windows, custom)
- `source_host` TEXT
- `event_type` TEXT
- `severity` TEXT (info|low|medium|high|critical)
- `user` TEXT NULL
- `process` TEXT NULL
- `ip_src` TEXT NULL
- `ip_dst` TEXT NULL
- `hostname` TEXT NULL
- `payload` TEXT (JSON enriquecido)
- `raw` TEXT (payload original)
- `trace_id` TEXT
- `normalized_at` TEXT

Índices: `(timestamp)`, `(source_host, timestamp)`, `(source_type, timestamp)`, `(ip_src)`.

### alerts
- `alert_id` TEXT PK
- `rule_id` TEXT
- `severity` TEXT
- `status` TEXT (OPEN|TRIAGE|INVESTIGATING|RESOLVED|FALSE_POSITIVE)
- `mitre_tactic`, `mitre_technique` TEXT
- `entities` TEXT (JSON)
- `evidence` TEXT (JSON - ids de eventos)
- `first_seen`, `last_seen` TEXT
- `created_at`, `updated_at` TEXT

### incidents
- `incident_id` TEXT PK
- `title` TEXT
- `status` TEXT (OPEN|INVESTIGATING|RESOLVED|FALSE_POSITIVE)
- `severity` TEXT
- `created_at`, `updated_at` TEXT
- `timeline` TEXT (JSON de eventos de ação)

### detection_rules / correlation_rules
- `rule_id` TEXT PK
- `name` TEXT
- `severity` TEXT
- `mitre_tactic`, `mitre_technique` TEXT
- `condition` TEXT (JSON/YAML)
- `timeframe` INTEGER (segundos)
- `enabled` INTEGER (0/1)
- `version` INTEGER
- `updated_at` TEXT

### iocs
- `ioc_id` TEXT PK
- `type` TEXT (ip|domain|url|hash|email)
- `value` TEXT
- `source` TEXT
- `threat_type` TEXT
- `created_at` TEXT
- UNIQUE (type, value)

### assets
- `asset_id` TEXT PK
- `hostname` TEXT
- `ip` TEXT
- `os` TEXT
- `criticality` TEXT (low|medium|high|critical)
- `tags` TEXT (JSON)
- `last_seen` TEXT

### users
- `user_id` TEXT PK
- `username` TEXT UNIQUE
- `role` TEXT (analyst|admin)
- `created_at` TEXT

### audit_log
- `entry_id` INTEGER PK AUTOINCREMENT
- `actor` TEXT
- `action` TEXT
- `target` TEXT
- `details` TEXT (JSON)
- `created_at` TEXT

## 2. Modelagem

- IDs: prefixo por tipo (`evt_`, `alt_`, `inc_`, `rule_`, `ioc_`, `ast_`).
- Payloads ricos como JSON (imutáveis); campos de consulta como colunas.
- Eventos são **append-only** (nunca UPDATE/DELETE).
- Soft-delete para regras (enabled=0) em vez de remoção.
- Migration: `scripts/migrations/` versionado, aplicado na subida.

## 3. Consultas SOC típicas (índices justificados)

- "Alertas críticos nas últimas 24h" → alerts(severity, created_at).
- "Eventos do host X na janela Y" → events(source_host, timestamp).
- "IP suspeito em eventos" → events(ip_src).
