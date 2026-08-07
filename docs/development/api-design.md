# EDY SIEM — API Design

> Projeto completo da API (implementação na Sprint 1). Contratos, padrões,
> versionamento, erros e respostas. Base: `API_GUIDE.md` + `CODING_GUIDE.md` §11-12.

## 1. Princípios

- Contratos estáveis e versionados (`/api/v1`).
- Envelope consistente (`data`/`error`).
- Nunca endpoint sem contrato documentado.
- RESTful: recursos + ações via sub-resource.

## 2. Endpoints (v1)

### Events
| Método | Rota | Descrição |
|---|---|---|
| GET | `/events` | Busca (filtros: severity, status, source, host, ip, since, until, q, limit, offset) |
| GET | `/events/{id}` | Detalhe |
| POST | `/events/ingest` | Ingestão manual |

### Alerts
| Método | Rota | Descrição |
|---|---|---|
| GET | `/alerts` | Lista (severity, status, mitre, since, limit, offset) |
| GET | `/alerts/{id}` | Detalhe |
| POST | `/alerts/{id}/ack` | Reconhecer |
| POST | `/alerts/{id}/resolve` | Resolver |
| POST | `/alerts/{id}/suppress` | Suprimir |
| POST | `/alerts/{id}/reopen` | Reabrir |
| POST | `/alerts/batch` | Ações em lote |
| GET | `/alerts/{id}/export` | Exportar (json/md) |

### Incidents
| Método | Rota | Descrição |
|---|---|---|
| GET | `/incidents` | Lista |
| GET | `/incidents/{id}` | Detalhe + timeline |
| POST | `/incidents` | Criar (agrupa alertas) |
| POST | `/incidents/{id}/notes` | Adicionar nota |
| POST | `/incidents/{id}/status` | Mudar status |
| GET | `/incidents/{id}/export` | Exportar |

### Rules
| Método | Rota | Descrição |
|---|---|---|
| GET | `/rules/detection` | Listar |
| POST | `/rules/detection` | Criar |
| GET | `/rules/detection/{id}` | Detalhe |
| PUT | `/rules/detection/{id}` | Atualizar |
| DELETE | `/rules/detection/{id}` | Desabilitar (soft) |
| POST | `/rules/detection/{id}/test` | Testar com eventos de exemplo |
| GET/POST | `/rules/correlation` | Análogo |

### Intelligence
| Método | Rota | Descrição |
|---|---|---|
| GET | `/iocs` | Lista |
| POST | `/iocs` | Criar |
| POST | `/iocs/import` | Importar lista |
| GET | `/assets` | Lista |

### System
| Método | Rota | Descrição |
|---|---|---|
| GET | `/health` | Status por componente |
| GET | `/status` | Métricas do pipeline |

## 3. Padrões

### Paginação
```
GET /alerts?limit=25&offset=50
→ {"data": [...], "meta": {"total": 248, "limit": 25, "offset": 50}}
```

### Filtros
- Query params: `severity`, `status`, `source`, `host`, `ip`, `since`, `until`, `q`.
- Datas: ISO 8601 UTC.

### Erros
```json
{"error": {"code": "rule_not_found", "message": "Regra não encontrada", "trace_id": "tr_..."}}
```

Códigos HTTP: 200, 201, 204, 400, 401, 403, 404, 409, 422, 500.

### Idempotência
- POSTs críticos aceitam `Idempotency-Key`; replay retorna resultado original.

### Autenticação
- `Authorization: Bearer <token>`; papel (analyst/admin).
- Rate limiting por token/IP (futuro OAuth).

## 4. Versionamento

- Mudança quebradora → `/api/v2` (clientes v1 intactos).
- Campos novos aditivos (não quebram).
- Deprecação anunciada com `Deprecation` header.

## 5. Exemplo de contrato (Alert)

```json
{
  "data": {
    "alert_id": "alt_001",
    "rule_id": "det_login_bruteforce",
    "severity": "high",
    "status": "OPEN",
    "mitre": {"tactic": "credential-access", "technique": "T1110"},
    "entities": {"host": "web-01", "user": "admin", "ip_src": "10.0.0.5"},
    "evidence_count": 24,
    "first_seen": "2026-08-03T10:00:00Z",
    "last_seen": "2026-08-03T10:05:00Z"
  }
}
```

## 6. Regras

- Nunca expor IDs internos/erros de stack.
- Validação de entrada por schema (400/422 com campo).
- Rate limiting em toda rota.
- Logs de acesso (Access Log) em toda requisição.
- Contratos documentados antes da implementação.
