# EDY SIEM — Database Design

> Modelagem completa do banco (implementação na Sprint 1). Base: `DATABASE.md` + ADR-002.
> Acesso exclusivo via `app/persistence`. SQLite na fundação, motor trocável via Protocol.

## 1. ERD

```mermaid
erDiagram
    EVENT ||--o{ ALERT : "evidência (evidence_ids)"
    ALERT }o--|| INCIDENT : "agrupado em"
    INCIDENT ||--o{ AUDIT_LOG : "ações"
    RULE ||--o{ ALERT : "gera"
    IOC ||--o{ EVENT : "correlaciona"
    ASSET ||--o{ EVENT : "contexto"
    USER ||--o{ AUDIT_LOG : "executa"

    EVENT {
        text event_id PK
        text timestamp
        text source_type
        text source_host
        text event_type
        text severity
        text user
        text process
        text ip_src
        text ip_dst
        text hostname
        text payload
        text raw
        text trace_id
        text normalized_at
    }
    ALERT {
        text alert_id PK
        text rule_id FK
        text severity
        text status
        text mitre_tactic
        text mitre_technique
        text entities
        text evidence
        text first_seen
        text last_seen
        text created_at
        text updated_at
    }
    INCIDENT {
        text incident_id PK
        text title
        text status
        text severity
        text created_at
        text updated_at
        text timeline
    }
    RULE {
        text rule_id PK
        text name
        text severity
        text mitre_tactic
        text mitre_technique
        text condition
        int timeframe
        int enabled
        int version
        text updated_at
    }
    IOC {
        text ioc_id PK
        text type
        text value
        text source
        text threat_type
        text created_at
    }
    ASSET {
        text asset_id PK
        text hostname
        text ip
        text os
        text criticality
        text tags
        text last_seen
    }
    USER {
        text user_id PK
        text username
        text role
        text created_at
    }
    AUDIT_LOG {
        int entry_id PK
        text actor
        text action
        text target
        text details
        text created_at
    }
```

## 2. Relacionamentos

| De | Para | Cardinalidade | Regra |
|---|---|---|---|
| Alert | Incident | N → 1 | alerta pertence a 0..1 incidente |
| Rule | Alert | 1 → N | regra gera vários alertas |
| Event | Alert | N → N | alerta referencia evidências (evidence_ids) |
| IOC | Event | N → N | IOC correlaciona eventos (match) |
| Asset | Event | 1 → N | asset é contexto de eventos |
| User | Audit | 1 → N | usuário executa ações |

## 3. Índices (consultas SOC)

| Tabela | Índice | Justificativa |
|---|---|---|
| events | `(timestamp)` | busca por janela |
| events | `(source_host, timestamp)` | contexto de host |
| events | `(ip_src)` | busca por IP |
| events | `(source_type, timestamp)` | filtro por fonte |
| alerts | `(severity, created_at)` | lista de prioridade |
| alerts | `(status)` | triagem |
| incidents | `(status)` | fila |
| iocs | `(type, value)` UNIQUE | dedupe |

## 4. Estratégias

- **Append-only** para events (nunca UPDATE/DELETE).
- **Soft-delete** para regras (enabled=0).
- **JSON** para payloads ricos (imutáveis); colunas para consulta frequente.
- **Migrações** versionadas em `scripts/migrations/` (apply na subida).
- **Retention/particionamento**: tema futuro (S3) via Protocol.
- **IDs**: prefixo por tipo (`evt_`, `alt_`, `inc_`, `rule_`, `ioc_`, `ast_`).
- **Timestamps**: ISO 8601 UTC (TEXT) — consistência e legibilidade.

## 5. Transações e concorrência

- Repositórios por agregado com transação atômica.
- Insert de evento não bloqueia leitura SOC (WAL mode).
- Regras/IOCs com UNIQUE + upsert.
- Idempotência: chave única permite re-insert seguro (replay).
