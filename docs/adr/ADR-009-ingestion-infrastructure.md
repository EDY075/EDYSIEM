# ADR-009 — Infraestrutura de Ingestão Enterprise

- **Status:** Aceito
- **Data:** 2026-08-03

## Contexto
O EDY SIEM precisa ingerir eventos de múltiplas fontes (syslog, arquivos, APIs)
com robustez de produção: filas com backpressure, retry, dead letter, rate limit
e observabilidade. A Sprint 2.1 definiu os modelos da pipeline (ADR-008); agora é
necessária a **infraestrutura de ingestão reutilizável**, desacoplada de qualquer
parser/coletor específico.

## Decisão
Criar o pacote `src/edysiem/ingestion/` **totalmente desacoplado** (depende apenas
de `domain`, `result`, `exceptions`, `logging` opcional e stdlib):

| Componente | Responsabilidade |
|---|---|
| `collectors/base.py` | Protocolo `CollectorPlugin` Enterprise: `start/stop/read/health/metadata/capabilities` |
| `queue.py` | `RawEventQueue` FIFO thread-safe e async-ready, com drop policy e timeout |
| `backpressure.py` | `BackpressureController` com HIGH/LOW water marks e estados NORMAL/PAUSED |
| `retry.py` | `RetryPolicy` com backoff exponencial, jitter e exceções retryable |
| `dead_letter.py` | `DeadLetterQueue` — eventos inválidos nunca são descartados em silêncio |
| `rate_limiter.py` | `TokenBucketRateLimiter` por collector (events/sec + burst) |
| `health.py` | `HealthMonitor` + `CollectorHealth` por collector (status/uptime/throughput/fila) |
| `metrics.py` | `MetricsRegistry` (contadores/gauges/timers) sem dependência externa |

O contrato oficial de coletores passa a viver em `ingestion.collectors.base`;
`plugins/contracts.py` re-exporta o novo `CollectorPlugin` (o protocolo antigo com
`setup/shutdown/collect/meta` foi substituído). **Nenhum collector conhece parser.**

## Consequências
- (+) Infraestrutura reutilizável para qualquer fonte futura (syslog, Windows, Zeek...).
- (+) Eventos inválidos são auditáveis via DeadLetter (nunca perdidos em silêncio).
- (+) Backpressure e rate limit protegem o pipeline de picos (ADR-003).
- (+) Observabilidade nativa: métricas e health por collector (ADR-006).
- (-) Fila é single-loop asyncio (multi-loop exigiria worker dedicado — documento).
- (-) DeadLetter é in-memory na v1 (persistência SQLite em sprint futura).
- Manutenção em 1 ano: novo coletor = implementar `CollectorPlugin` + configurar fila,
  sem tocar no pipeline.

## Critério "daqui a um ano"
Adicionar uma nova fonte de eventos exige apenas um `CollectorPlugin` e config,
reutilizando fila, backpressure, retry, dead letter e rate limit prontos.
