# EDY SIEM — Contratos para Triage e Playbooks

Este documento define a superfície mínima para tornar as duas interfaces operacionais. Nenhum endpoint foi implementado nesta sprint.

## Convenções

- Base: `/api/v1`.
- Datas: ISO-8601 UTC.
- Paginação: `limit` (1–100), `cursor` opcional e `next_cursor` na resposta.
- Toda mutação deve registrar `actor_id`, `request_id` e evento de auditoria.
- Resposta de erro: `{ "detail": "mensagem", "code": "CODIGO" }`.

## Triage

### `GET /soc/triage/alerts`

Consulta a fila de triagem. Filtros: `severity`, `source`, `rule_id`, `host`, `from`, `to`, `triage_status`, `assignee_id`, `limit`, `cursor`.

```json
{
  "items": [{
    "alert_id": "alt_01",
    "title": "Brute Force SSH",
    "severity": "critical",
    "source": "waf-01",
    "host": "srv-auth-01",
    "rule_id": "brute-force-ssh",
    "first_seen": "2026-08-06T12:00:00Z",
    "risk_score": 97,
    "mitre": ["T1110"],
    "triage_status": "pending",
    "sla": { "state": "at_risk", "due_at": "2026-08-06T12:15:00Z" },
    "assignee": { "id": "usr_01", "display_name": "Analyst SOC" }
  }],
  "total": 1,
  "next_cursor": null
}
```

Valores: `triage_status`: `pending | classified | assigned | escalated | closed`; `sla.state`: `on_track | at_risk | breached | unavailable`.

### `POST /soc/triage/alerts/{alert_id}/classify`

```json
{ "classification": "true_positive", "notes": "Tentativas distribuídas no mesmo host." }
```

`classification`: `true_positive | benign_positive | false_positive | duplicate`.

### `POST /soc/triage/alerts/{alert_id}/assign`

```json
{ "assignee_id": "usr_01" }
```

### `POST /soc/triage/alerts/{alert_id}/escalate`

```json
{ "target": "incident", "reason": "Risco confirmado acima do limiar." }
```

`target`: `incident | case | war_room`.

### `POST /soc/triage/alerts/{alert_id}/close`

```json
{ "resolution": "false_positive", "notes": "Atividade autorizada." }
```

Resposta de todas as mutações: item de triagem atualizado no mesmo formato de `GET`.

## Playbooks

### `GET /soc/playbooks`

Filtros: `status`, `trigger`, `category`, `query`, `limit`, `cursor`.

```json
{
  "items": [{
    "playbook_id": "pb_01",
    "name": "Contain compromised endpoint",
    "description": "Isola o endpoint e cria evidências.",
    "trigger": "alert.severity:critical",
    "category": "containment",
    "version": "1.4.0",
    "status": "enabled",
    "last_execution": "2026-08-06T12:00:00Z",
    "execution_summary": { "total": 32, "successful": 30, "failed": 2, "success_rate": 93.75 }
  }],
  "total": 1,
  "next_cursor": null
}
```

### `GET /soc/playbooks/{playbook_id}`

Retorna o item acima acrescido de `inputs_schema`, `steps`, `required_permissions`, `created_at`, `updated_at`, `created_by` e `updated_by`.

### `GET /soc/playbooks/{playbook_id}/executions`

Filtros: `status`, `from`, `to`, `limit`, `cursor`.

```json
{
  "items": [{
    "execution_id": "run_01",
    "status": "succeeded",
    "triggered_by": { "type": "alert", "id": "alt_01" },
    "started_at": "2026-08-06T12:00:00Z",
    "finished_at": "2026-08-06T12:01:20Z",
    "summary": "Endpoint isolado com sucesso.",
    "steps": [{ "step_id": "isolate", "status": "succeeded", "started_at": "...", "finished_at": "..." }]
  }],
  "total": 1,
  "next_cursor": null
}
```

### `POST /soc/playbooks/{playbook_id}/executions`

```json
{ "trigger": { "type": "manual", "source_id": null }, "inputs": {} }
```

Retorna `202` com `{ "execution_id": "run_01", "status": "queued" }`.

### `PATCH /soc/playbooks/{playbook_id}`

Permite atualizar `name`, `description`, `trigger`, `category`, `inputs_schema` e `steps`. Deve devolver o playbook atualizado com nova `version` semântica.

### `POST /soc/playbooks/{playbook_id}/duplicate`

```json
{ "name": "Contain compromised endpoint — copy" }
```

Retorna `201` com o novo playbook.

### `PATCH /soc/playbooks/{playbook_id}/status`

```json
{ "status": "enabled" }
```

Valores: `enabled | disabled`.

## Métricas de Playbooks

`GET /soc/playbooks/metrics?from=&to=` deve retornar:

```json
{ "available": 12, "enabled": 9, "recent_executions": 34, "success_rate": 94.12 }
```

## Segurança e auditoria

As mutações exigem RBAC: `triage.write`, `playbook.execute`, `playbook.write` e `playbook.manage`. Executar, editar, duplicar, habilitar/desabilitar e as quatro ações de triagem precisam publicar um registro de auditoria com estado anterior, estado posterior e `actor_id`.