# EDY SIEM — Performance Design

> Arquitetura de performance (projeto, sem código). Alvo: operação SOC responsiva e
> pipeline escalável. Complementa `OBSERVABILITY.md` (como medir) e `QUALITY_GUIDE.md` (gate).

---

## 1. Estratégia geral

- **Pipeline com backpressure** (ADR-003): entrada nunca sobrecarrega o processamento.
- **Consultas SOC otimizadas por índice** (ver DATABASE_DESIGN).
- **Cache** para dados de leitura quente; **streaming** para listas grandes.
- **Workers assíncronos** para jobs (enriquecimento, exportação, notificação).

## 2. Caching

| Camada | Cache | TTL | Invalidação |
|---|---|---|---|
| API (leitura) | resultados de consulta frequente | 5–30s | on write |
| Enrichment | asset/intel lookups | 5min–1h | on update |
| Regras | regras compiladas/validadas | on change | `rule.changed` |
| Config | config tipada | on change | — |

- Memória limitada; eviction LRU.
- Cache nunca contém dados sensíveis em claro além do necessário.

## 3. Queues e Workers

- Fila interna de ingestão com **tamanho máximo** (backpressure).
- **Workers assíncronos** para: enriquecimento lento, correlação pesada, exportação, notificação.
- Nº de workers configurável; worker com timeout e retry.
- Falha de worker → log + retry (dead-letter opcional).

> **Implementado (Sprint 2.2, ADR-009):** `RawEventQueue` (FIFO thread-safe e
> async-ready, drop policy, timeout), `BackpressureController` (HIGH/LOW water
> marks com histerese), `RetryPolicy` (backoff exponencial + jitter),
> `DeadLetterQueue` (eventos nunca descartados em silêncio). Ver `docs/architecture/pipeline.md`.

## 4. Async Jobs

| Job | Gatilho | Pode falhar? |
|---|---|---|
| Ingestão em lote | POST ingest | retry |
| Enriquecimento externo | evento | degrada (sem intel) |
| Exportação (MD/JSON) | ação | retry |
| Notificação (email/webhook) | alerta/case | retry |

- Jobs idempotentes; resultado cacheado; progresso observável.

## 5. Índices (reforço)

- `events(timestamp)`, `events(source_host, timestamp)`, `events(ip_src)`.
- `alerts(severity, created_at)`, `alerts(status)`.
- `incidents(status)`, `iocs(type, value)` UNIQUE.
- Índices revisados com plano de execução em consultas lentas.

## 6. Connection Pool

- SQLite: pool simples (WAL + conexões limitadas; escrita serializada).
- Futuro PostgreSQL: pool de conexões configurável.
- Nunca abrir conexão por request; reutilizar pool.

## 7. Compression e Pagination

- Respostas JSON com `Content-Encoding: gzip` quando aplicável.
- Paginação obrigatória (`limit`/`offset` + `meta`) em listas.
- Limites por endpoint; scroll/cursor para volumes grandes (futuro).

## 8. Streaming

- Exportações grandes em **stream** (não carregar tudo em memória).
- Leitura de eventos em lotes (batch) para processamento.
- UI: virtualização de tabelas grandes (quando implementar).

## 9. Memory e CPU Limits

- Workers com limites: `max_concurrent`, timeout, tamanho de lote.
- Cache com `max_memory` configurável.
- Parsing/regras com timeouts para evitar CPU runaway.
- Monitorar pico de memória (ver OBSERVABILITY).

## 10. Rate Limiting (performance)

- Protege API e ingestão de picos abusivos.
- Token bucket por IP/api key.
- Resposta `429` + `Retry-After`.

> **Ingestão (Sprint 2.2, ADR-009):** `TokenBucketRateLimiter` — token bucket
> thread-safe por collector (events/sec + burst). Cada coletor pode ser limitado
> de forma independente antes de enfileirar.

## 11. Performance Targets (v1)

| Operação | Alvo |
|---|---|
| Lista de alertas (filtrada, 25 itens) | < 500ms |
| Busca de eventos (janela 24h, indexado) | < 1s |
| Detalhe de alerta + evidências | < 300ms |
| Ingestão de 1000 eventos | < 5s (batch) |
| Exportação de case (1000 evidências) | < 3s |
| Health check | < 100ms |
| UI: interação de triagem | < 100ms de resposta visual |

## 12. Benchmark Plan

1. **Fixture**: dataset sintético em `examples/events/` (100k eventos, múltiplas fontes).
2. **Cenários**: ingestão batch, busca indexada, correlação janela, detecção, exportação.
3. **Ferramenta**: script em `tools/dev/bench.py` (sem dependência externa).
4. **Métricas**: latência p50/p95, throughput eventos/s, memória, CPU.
5. **Gate**: comparar contra targets; regressão → bloquear merge.

## 13. Escalabilidade (fases)

- **V1 (single process)**: pipeline assíncrono + fila interna; suficiente para estudo/SOC pequeno.
- **V2 (workers)**: processos/workers separados; fila externa plugável (Kafka) via contrato (ADR-003).
- **V3 (storage)**: PostgreSQL via Protocol; particionamento/retention.
- **V4 (cluster)**: ingestão distribuída; busca horizontal (futuro, se necessário).

Regra: cada salto de escala respeita os contratos existentes (não refatora pipeline).
