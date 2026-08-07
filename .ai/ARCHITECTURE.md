# ARCHITECTURE.md — Arquitetura do EDY SIEM

> Visão estrutural para agentes: **onde está cada coisa**. Referências completas em `docs/`.

## Visão de alto nível

```
Event Sources → Collectors → RawEvent → Parser → ParsedEvent
        → Normalizer → CanonicalEvent → Enrichment → EnrichedEvent
        → Correlation → Detection → Incident → Persistence
        → REST API → Dashboard / CLI
```

## Backend (`src/edysiem/`) — Clean Architecture
Dependências apontam para o **domínio**. Core 100% stdlib (ADR-001).

| Módulo | Responsabilidade pura |
|---|---|
| `domain/` | Entidades e enums (dataclasses puras, sem infra) |
| `result/` | `Result[T]` estilo Rust (Success/Failure/ErrorCode, nunca `None`) |
| `exceptions/` | Hierarquia Domain/Validation/Infrastructure/Plugin/Configuration/Security |
| `config/` | Config tipada, env-driven, defaults e validação |
| `events/` | Event Bus async-ready (publisher/subscriber, registry, cancelamento) |
| `di/` | Container DI manual (Singleton/Scoped/Transient) + detecção de ciclo |
| `validation/` | Motor declarativo + validadores (IP, email, URL, hash, UUID) |
| `logging/` | Logger estruturado JSON + correlation/request/session ID + saneamento |
| `plugins/` | 7 contratos (Parser, Collector, Analyzer, Enrichment, Exporter, Notification, Base) |
| `ingestion/` | Ingestão de eventos |
| `parsers/` | Parsers (syslog RFC3164/RFC5424 etc.) |
| `normalization/` | Normalização → evento canônico |
| `enrichment/` | Enriquecimento (asset/geo/intel) |
| `correlation/` | Correlation Engine (regras declarativas + janelas) |
| `detection/` | Rule Engine + DSL (`DetectionRule`) |
| `alerts/` | Alert Engine (risk/fingerprint/dedup/lifecycle) |
| `incidents/` | Incident Engine (grouping/correlator/lifecycle) |
| `cases/` | Case Engine (investigação, evidências, comentários) |
| `persistence/` | Repositórios SQLite + migrações + audit + search + transaction |
| `soc/` | Orquestra o fluxo SOC (pipeline + service + SLA) |
| `api/` | FastAPI v1 (ver abaixo) |
| `cli/` | CLI `edysiem` + runner de dev (`dev.py`) |
| `container.py` | Composição do container (bootstrap) |

## API — FastAPI (`src/edysiem/api/`)
- **Factory:** `create_app(container)` em `app.py`.
- **Prefixos:** todos sob `/api/v1`.
- **Middlewares:** RequestID + HTTP logging. Auth **opt-in** via `X-API-Key` (se `EDYSIEM_API_KEY` definida).
- **Docs:** OpenAPI `/openapi.json`, Swagger `/docs`, ReDoc `/redoc`.
- **Rotas:** `health` · `pipeline` · `alerts` · `incidents` · `cases` · `soc`.
- **Contratos SOC (persistidos):** `/soc/alerts|incidents|cases|rules|iocs|assets`, `/soc/pipeline/run|demo`.

## Frontend (`frontend/`) — React/TS
| Caminho | Conteúdo |
|---|---|
| `src/api/client.ts` | API client central (timeout, retry, tipos) |
| `src/hooks/` | useMetrics, useIncidents, useCases, useHealth, useAlerts |
| `src/design-system/` | tokens (colors, typography, spacing, density, radii, elevation, motion) + componentes |
| `src/shell/` | AppShell, Sidebar, Topbar, GlobalSearch, ThemeSwitch, UserMenu, LiveOperationsBar, Breadcrumb, Footer |
| `src/pages/` | Dashboard, WarRoom, Triage, Alerts, Incidents, Investigation, Cases, Rules, Intel, Detection, Playbooks, Settings |
| `src/routing/routes.tsx` | Rotas com React.lazy + Suspense |
| `src/state/` | Toast + contexto de app |
| `src/theme/` | ThemeProvider (dark/light) |

### Rotas principais (frontend)
`/` (Dashboard) · `/war-room` · `/triage` · `/alerts` · `/incidents` · `/investigate` · `/cases` ·
`/playbooks` · `/rules` · `/intel` · `/detection` · `/settings`.

## Decisões relevantes
- **ADR-001** stack (core stdlib); **ADR-002** persistência (SQLite); **ADR-003/008** pipeline;
  **ADR-005** frontend; **ADR-009** ingestion infra; ver **[DECISIONS.md](./DECISIONS.md)**.

## Documentação de referência
`docs/ARCHITECTURE.md` · `docs/SYSTEM_DESIGN.md` · `docs/DATABASE.md` · `docs/PIPELINE.md` ·
`docs/API_DESIGN.md` · `docs/SECURITY_ARCHITECTURE.md` · `docs/PERFORMANCE_DESIGN.md` · `docs/OBSERVABILITY.md`.
Todo ADR: `docs/adr/`.