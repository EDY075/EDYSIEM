# EDY SIEM — Observability

> Projeto de observabilidade: health checks, métricas, telemetria, tracing e logs.
> Complementa `LOGGING_DESIGN.md` e `PERFORMANCE_DESIGN.md`. Sem código — arquitetura.

---

## 1. Princípios

- **Tudo observável**: cada componente expõe estado e métricas.
- **Trace ID ponta a ponta** (ADR-006): um evento/alerta é rastreável do início ao fim.
- **Métricas simples**: contadores e timers por etapa — sem dependência externa na v1.
- **Health por componente**: online/degraded/offline por unidade.
- **Self monitoring**: o sistema observa a si mesmo (alerta quando degrade).

## 2. Health Checks

- `GET /api/v1/health` — estado agregado.
- Por componente: `collectors`, `ingestion`, `normalization`, `enrichment`,
  `correlation`, `detection`, `incident`, `persistence`, `api`, `workers`.
- Formato: `{"status": "online|degraded|offline", "components": {...}}`.
- Health check rápido (< 100ms) para LB/monitor.

## 3. Métricas (core)

| Grupo | Métricas |
|---|---|
| **Pipeline** | eventos_ingested, normalized, enriched, correlated, detected; erros por etapa |
| **Alerts** | alertas_created, deduplicados, por severidade, por regra |
| **Incidents** | incidentes_created, abertos, resolvidos |
| **API** | requests_total, latência (p50/p95), status 4xx/5xx |
| **Database** | queries_total, queries_lentas, conexões, tamanho |
| **Workers** | jobs_total, jobs_falhos, fila tamanho, tempo de job |
| **Plugins** | execuções, falhas, tempo |
| **System** | uptime, memória, CPU, disco, storage usado |

- Métricas expostas em `GET /api/v1/metrics` (JSON simples).

## 4. Telemetria e Tracing

- **trace_id** gerado na ingestão, propagado por todo o pipeline (contexto).
- Spans por etapa: `normalize`, `enrich`, `correlate`, `detect`, `persist` com duração.
- Logs e métricas carregam `trace_id`.
- Rastreio: dado um trace_id, obter todas as etapas/duração/erros.

## 5. Logs (reforço)

Ver `LOGGING_DESIGN.md`. Categorias: application, audit, security, access, debug, error.
Todos em JSON com `ts, level, logger, trace_id, message, context`.

## 6. Self Monitoring

- O sistema avalia continuamente a própria saúde.
- Degradação (fila cheia, erros altos, health offline) → **alerta interno** + log warning.
- Sem alarme falso: thresholds com janela (ex.: 5 erros/10s).
- Observabilidade alimenta o próprio SIEM (meta — dogfooding).

## 7. Dashboards de operação

### System Dashboard
- Uptime, CPU, memória, disco, storage.
- Estado por componente (health).

### Performance Dashboard
- Latência p50/p95 por etapa e API.
- Throughput eventos/s; fila tamanho.

### Pipeline Metrics
- Contadores por etapa; erros; deduplicação.

### Plugin Metrics
- Execuções por plugin; falhas; tempo.

### API Metrics
- Requests, latência, erros por rota.

### Database Metrics
- Queries lentas, conexões, tamanho.

### Workers Metrics
- Jobs, fila, falhas, duração.

### Alert Metrics
- Alertas por severidade/regra; tempo de triagem (futuro).

## 8. Uptime e Latência

- **Uptime**: segundos desde o start (exposto no health).
- **Latência**: p50/p95 por operação; monitorar regressões (bench gate).

## 9. Memória, CPU, Storage

- Métricas do processo (psutil-like, stdlib + /proc) e do storage (tamanho do DB).
- Limites: alertar quando memória > 80%, CPU > 85%, storage > 85%.
- Log de picos para diagnóstico.

## 10. Implementação (fases)

| Fase | Entrega | Sprint |
|---|---|---|
| V1 | Health + métricas JSON + trace_id + logs JSON | 1–3 |
| V1 | Endpoints `/health`, `/status`, `/metrics` | 1–7 |
| V1 | Dashboards de operação (UI) | 2 |
| V2 | Export Prometheus/OpenTelemetry | futura |

## 11. Alvos

- Health < 100ms; /metrics < 100ms.
- Impacto de observabilidade < 5% do throughput.
- Zero logs sem trace_id em pipeline.
