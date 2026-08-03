# EDY SIEM — API Guide

> Contratos da API. **Nunca criar endpoint sem contrato documentado.**
> Base URL: `/api/v1` (versionada desde o início).

## 1. Convenções

- JSON em todas as respostas; `Content-Type: application/json; charset=utf-8`.
- Erros: `{"error": {"code": "...", "message": "...", "trace_id": "..."}}`.
- Timestamps em ISO 8601 (UTC).
- Paginação: `?limit=&offset=` + cabeçalho/metadata `{"total": n, "page": {...}}`.
- Idempotência: POSTs sensíveis aceitam `Idempotency-Key`.

## 2. Endpoints planejados (contratos)

### Events
- `GET /api/v1/events` — busca de eventos (filtros: source, host, severity, time_range, q).
- `GET /api/v1/events/{event_id}` — detalhe do evento.
- `POST /api/v1/events/ingest` — ingestão manual (estudo/offline).

### Alerts
- `GET /api/v1/alerts` — lista alertas (severity, status, mitre, time_range).
- `GET /api/v1/alerts/{alert_id}` — detalhe (entidades, evidências, MITRE).
- `POST /api/v1/alerts/{alert_id}/ack|resolve|suppress|reopen` — ciclo de vida.
- `GET /api/v1/alerts/{alert_id}/export` — exportar (json|md).

### Incidents
- `GET /api/v1/incidents` — lista incidentes (status, severity).
- `GET /api/v1/incidents/{incident_id}` — detalhe + timeline.
- `POST /api/v1/incidents/{incident_id}/notes` — adicionar nota.
- `POST /api/v1/incidents/{incident_id}/status` — mudar status.

### Rules
- `GET/POST /api/v1/rules/detection` — listar/criar detection rules.
- `GET/PUT/DELETE /api/v1/rules/detection/{rule_id}` — gerir regra.
- `GET/POST /api/v1/rules/correlation` — correlação análoga.

### Intelligence
- `GET/POST /api/v1/iocs` — gerir IOCs.
- `GET/POST /api/v1/assets` — gerir assets.

### System
- `GET /api/v1/health` — status por componente (ver ADR-006).
- `GET /api/v1/status` — métricas do pipeline (events/s, fila, erros).

## 3. Exemplo de resposta de alerta

```json
{
  "alert_id": "alt_...",
  "rule_id": "det_login_bruteforce",
  "severity": "high",
  "status": "OPEN",
  "mitre": {"tactic": "credential-access", "technique": "T1110"},
  "entities": {"host": "web-01", "user": "admin", "ip_src": "10.0.0.5"},
  "evidence_count": 24,
  "first_seen": "2026-08-03T10:00:00Z",
  "last_seen": "2026-08-03T10:05:00Z"
}
```

## 4. Evolução

- Mudanças quebradas exigem bump de versão (`/api/v2`) e ADR.
- Campos novos são aditivos (não quebram clientes).
