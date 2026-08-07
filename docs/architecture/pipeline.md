# EDY SIEM — Pipeline

> Documento da pipeline de eventos. Descreve a infraestrutura de ingestão
> (Sprint 2.2, ADR-009) e como o fluxo ponta a ponta se conecta aos modelos
> da Sprint 2.1 (ADR-008). Complementa `ARCHITECTURE.md` e `DATAFLOW.md`.

## 1. Visão ponta a ponta

```
Sources ──► Collectors ──► RawEventQueue ──► Parser ──► ParsedEvent
                                                │
                                                ▼
                                        Normalizer ──► CanonicalEvent
                                                │
                                                ▼
                                        Enrichment ──► EnrichedEvent
                                                │
                                                ▼
                                        Correlation ──► Detection ──► Alert
                                                │
                                                ▼
                                        Incident ──► Case
```

## 2. Infraestrutura de ingestão (`src/edysiem/ingestion/`)

```
                    ┌────────────────────────────────────────────────┐
                    │               INFRAESTRUTURA                    │
  Sources           │                                                │
  ──────► Collector ──► [Rate Limiter] ──► [RawEventQueue]            │
                    │       │                      │                  │
                    │       │              [Backpressure]            │
                    │       │                      │                  │
                    │   [HealthMonitor]      (cheia / PAUSED)         │
                    │       │                      │                  │
                    │       ▼                      ▼                  │
                    │  [MetricsRegistry]   [Retry] → [DeadLetterQueue]│
                    └────────────────────────────────────────────────┘
                                    │
                                    ▼
                              RawEvent (p/ Parser)
```

### 2.1 Fluxo de um RawEvent na ingestão
1. `CollectorPlugin.read()` produz `RawEvent` (stream assíncrono).
2. Opcionalmente passa pelo `TokenBucketRateLimiter` (controle por collector).
3. `RawEventQueue.put()` enfileira (FIFO) respeitando `BackpressureController`
   e `DropPolicy` (BLOCK/DISCARD/DEAD_LETTER).
4. Falhas no processamento seguem para `RetryPolicy` (backoff + jitter).
5. Eventos que excedem tentativas ou são inválidos vão para `DeadLetterQueue`
   (nunca descartados em silêncio).
6. `HealthMonitor` e `MetricsRegistry` expõem estado por collector.

### 2.2 Componentes

| Componente | API principal | Comportamento |
|---|---|---|
| `CollectorPlugin` | `start/stop/read/health/metadata/capabilities` | Contrato Enterprise; não conhece parser |
| `RawEventQueue` | `put/put_nowait/get/get_nowait/qsize` | FIFO, thread-safe, async-ready, drop policy, timeout |
| `BackpressureController` | `report_size/pause/resume/wait_until_resumed` | HIGH/LOW water marks, histerese |
| `RetryPolicy` | `should_retry/delay_for` + `run_with_retry` | Backoff exponencial, jitter, exceções retryable |
| `DeadLetterQueue` | `submit/records/drain/len` | Auditoria de eventos mortos (in-memory v1) |
| `TokenBucketRateLimiter` | `acquire/try_acquire/tokens` | events/sec + burst por collector |
| `HealthMonitor` | `register/update/snapshot/aggregate` | Status ONLINE/DEGRADED/OFFLINE por collector |
| `MetricsRegistry` | `increment/set_gauge/observe/snapshot` | queue_size, throughput, drops, retries, dead_letters, latency |

## 3. Contratos de plugins (evolução ADR-008/ADR-009)

| Plugin | Assinatura |
|---|---|
| `CollectorPlugin` | `read() -> AsyncIterator[RawEvent]` + `health()` |
| `ParserPlugin` | `parse(RawEvent) -> Result[list[ParsedEvent]]` |
| `EnrichmentPlugin` | `enrich(CanonicalEvent, context) -> Result[EnrichedEvent]` |
| `AnalyzerPlugin` | `analyze(EnrichedEvent) -> Result[list[Alert]]` |
| `ExporterPlugin` | `export(list[CanonicalEvent]) -> ExportResult` |

## 4. Observabilidade da ingestão

Métricas padronizadas (`MetricsRegistry`):
`queue_size`, `throughput`, `processing_time_ms`, `drops`, `retries`,
`dead_letters`, `latency_ms`, `errors`.

Health por collector (`CollectorHealth`):
`status`, `uptime_seconds`, `last_event_at`, `throughput_events_per_sec`,
`errors`, `queue_size`, `latency_ms`.

Detalhes: `docs/OBSERVABILITY.md` e `docs/PERFORMANCE_DESIGN.md`.

## 5. Fora de escopo nesta sprint

Syslog parser, Windows Events, Suricata, Zeek, JSON parser e Sigma serão
implementados em sprints futuras sobre esta infraestrutura.
