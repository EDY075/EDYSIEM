# Changelog
## [0.2.0] - 2026-08-06

### Finalização de release

- Identidade visual Echelon aplicada ao shell e às áreas operacionais, com temas escuro e claro, navegação refinada e componentes de alto contraste.
- Telas operacionais revisadas: Overview, War Room, Triage, Alertas, Incidentes, Investigação, Cases, Regras, Intelligence, Playbooks e Configurações.
- O detalhe de alertas deixou de mostrar eventos, evidências, correlações e históricos inventados; abas sem contrato de API agora comunicam a indisponibilidade de dados de forma explícita.
- Estabilizados testes de rate limiting e cobertos os caminhos de degradação do endpoint de saúde.
- Healthcheck agregado considera corretamente componentes `healthy` e `online`, evitando falso estado `degraded` quando todos os serviços estão operacionais.
- Saneado mojibake no serviço SOC, inclusive a mensagem retornada pelo simulador de regras.
- Seed `/soc/pipeline/demo` tornou-se idempotente após reinício: reutiliza alertas e incidentes pelo fingerprint e preserva o case associado, sem apagar dados persistidos.
- Validação final local: TypeScript, ruff, mypy e 801 testes automatizados.

Todas as mudanças notáveis do EDY SIEM serão documentadas neste arquivo.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
e o projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Não publicado]

### Sprint Final — Parte 2 (Backend Security)

- **Autenticação**: API Key **opt-in** (`EDYSIEM_API_KEY` → exige `X-API-Key`; sem env = dev aberto).
- **RBAC**: papéis `admin`/`analyst`/`viewer` + matriz de permissões (`require_permission`); aplicado a regras (rule:write), cases (case:write) e intel (intel:write).
- **Rate Limit**: janela deslizante em memória (`rate_limit`, 429) aplicado a `/pipeline/run`, `/soc/pipeline/run` e `/soc/simulator`.
- **Testes**: `test_security.py` (+7) — 401/403/429 e pass cases; suíte **95.07%**, mypy 0 (147), ruff limpo, tsc/build verdes.

## Sprint M4.3 — Live Preview + Browser Auto Open

- `edysiem run-dev` (e `dev`): inicia backend (uvicorn `--reload`) + frontend (vite HMR), verifica portas, abre o navegador **uma vez**, imprime URL.
- **Watchdog**: reinicia serviço que cair com limite (`MAX_RESTARTS=3`) e aborta com erro claro (sem loop infinito); cleanup obrigatório (taskkill /T no Windows).
- Swagger em `/docs`; WebSocket não existe (frontend usa polling 3s) — confirmado.

## Sprint UI/UX Polish

> Frontend apenas (sem features novas, sem alteração de backend/arquitetura).

- **Design System**: contraste elevado de `textMuted`/`textSecondary`; token `textSubtle`.
- **Tabelas (`DataTable`)**: cabeçalho sticky, hover por linha, EmptyCell discreto, `vertical-align`.
- **KPI Cards**: sparkline variada por card (seed `label+value`) — leitura menos "decorativa".
- **Drawer**: largura 460px, header sticky, sombra/backdrop refinados.
- **Detection Dashboard**: cards `Mini` com acento semântico por indicador (sem repetição).
- **Auditoria**: screenshots antes/depois em `UX_REVIEW/` (fora do versionamento).

## Sprint 2.17 — Detection Engineering + Threat Intelligence

> Capacidade de detectar/enriquecer/contextualizar eventos. Reutiliza `SocService`
> e a API `/soc/*` existentes — sem duplicar lógica, sem quebrar arquitetura.

#### Adicionado
- **SchemaV4** (+migração): tabelas `det_rules`, `iocs`, `assets` com índices.
- **Rule Engine gerenciável (SocService)**: catálogo persistido de regras
  (`register_rule`, `list_rules`, `set_rule_enabled`), contador de disparos
  (`fire_count`/`last_fired`) incrementado automaticamente em `persist_alert`.
- **Rule Simulator**: `simulate_rule(payload_json)` — retorna regra aplicada,
  severidade, score, motivo e `alert_generated`, **sem modificar a pipeline**.
- **IOC Intelligence**: `register_ioc`/`list_iocs`/`ioc_related` (IP/domínio/URL/
  hash/e-mail), reputação, first/last seen, hits, incidentes/casos relacionados.
- **Asset Inventory**: `register_asset`/`list_assets`/`asset_related` (hostname/IP/
  OS/criticidade/owner/status/last_seen) + relacionamento com incidentes/casos.
- **Detection Dashboard**: `detection_stats` — top rules, top MITRE, top IOCs,
  assets críticos, alertas por regra e tendência temporal (dados reais).
- **API `/soc/*`**: `GET/POST /soc/rules` + `enable`/`disable`, `POST /soc/simulator`,
  `GET/POST /soc/iocs` + `/soc/iocs/{value}/related`, `GET/POST /soc/assets` +
  `/soc/assets/{hostname}/related`, `GET /soc/detection`.
- **Frontend (real, sem mock)**: `IntelligencePage` (`/rules`, `/intel`) com abas
  Rules Manager, Rule Simulator, IOC e Assets; `DetectionDashboardPage` (`/detection`).

#### Métricas
- Backend: 771+ testes, cobertura **95.11%**, mypy strict 0 (145 arquivos), ruff limpo.
- Frontend: `tsc -b` exit 0, `npm run build` OK.

## Sprint 2.16 — Frontend Operacional

> Consome exclusivamente a API `/soc/*` real (sem novas engines, sem duplicar lógica).
> Nenhum dado mock restante no frontend.

#### Adicionado / Melhorado
- **Backend (WP1)**: `GET /soc/alerts` (+) e `GET /soc/alerts/{id}` (+SLA); `/soc/metrics` enriquecido com `events_per_second`, `events_last_24h`, `avg_risk_score` e `events_series` (60 pts/min, EventStore real).
- **Hooks reais (WP1)**: `useMetrics/useAlerts/useIncidents/useCases` reescritos sem mock, consumindo `GET /soc/*`, com loading/erro/refetch padronizado. `RecentAlert.mitre` adicionado.
- **Dashboard Vivo (WP6)**: série temporal real (sem gerador random); severidade por contagens reais; `usingMock`/banner demo removidos.
- **War Room Vivo (WP6)**: reescrita sem `DEMO_*` — KPIs/EPS/feed/MITRE/assets/severidade derivados de dados reais via hooks.
- **Incident UI (WP2)**: `IncidentCenterPage` — severidade/status/SLA/owner, assumir, transição e drawer.
- **Case Management UI (WP3)**: `CaseCenterPage` — timeline, evidências, contexto (IOC/MITRE/assets/users), comentar, anexar evidência, resolver e encerrar.
- **Investigation Workspace (WP4)**: `InvestigationPage` — cadeia navegável Eventos→Alerta→Incidente→Caso→MITRE→IOC→Asset→Usuário→Timeline.
- **Alert Center Enterprise (WP5)**: paginação (10/página), somando-se a filtros/pesquisa/ordenação/bulk/drawer + dados reais.
- **UX Enterprise (WP7)**: `ToastProvider`+`useToast` (feedback sucesso/erro/info), montado no App; toasts nas operações de incident/case.
- **Rotas**: `/incidents`, `/cases`, `/investigate` agora usam as telas reais (lazy).

#### Métricas
- Backend: 771 testes, cobertura **95.08%**, mypy strict 0 (145 arquivos), ruff limpo.
- Frontend: `tsc -b` exit 0, `npm run build` OK.

## Sprint 2.15 — SOC Investigation Pipeline

> Fluxo operacional: **Evento → Regra → Alerta → Incidente → Caso**, com
> persistência real (engines ↔ repos SQLite). Baixo acoplamento: nenhum engine
> existente foi modificado.

#### Adicionado
- **Pacote `src/edysiem/soc/`** (novo):
  - `sla.py` — `SlaPolicy` (prazos por severidade) + `compute_sla` (estados `ok/warning/overdue/met/missed`).
  - `service.py` — `SocService`: ponte engines → repos (transação atômica por operação), Incident Management (severidade/status/atribuição), Case Management (comentários, evidências, anexos, tarefas, resolução/encerramento), Investigation (pivôs alertas/IOCs/contexto via EventStore) e Dashboard KPIs reais (`metrics`).
  - `pipeline.py` — `SocPipeline`: `run_event` (pipeline de engines completa) e `run_demo` (4 alertas brute-force → 1 incidente → 1 caso).
- **Container**: `soc_service`/`soc_pipeline` lazy (`EDYSIEM_DB`, default `edysiem.db`).
- **API `/api/v1/soc`**: pipeline demo/run, incidentes (list/get/assign/transition), cases (list/get/investigate/comment/evidence/assign/resolve/close), metrics.
- **CLI**: comando `edysiem soc-run`.
- **Testes**: `test_soc_pipeline.py` (8) + `test_soc_api.py` (4) — fluxo completo até encerramento do caso.

#### Métricas
- 771 testes, cobertura **95.04%**, mypy strict 0 (145 arquivos), ruff check+format limpos.

## Sprint 2.14 — Qualidade UI Enterprise (WP1–WP9)

> Foco em QUALIDADE visual/premium, não em quantidade. Zero mudança de backend.

#### Adicionado / Melhorado
- **WP1 → Performance**: code-splitting de rotas via `React.lazy` + Suspense (`routes.tsx`, barra de progresso). Chunk inicial de entrada **691 kB → 248 kB** (gzip 205 kB → 79.6 kB).
- **WP2 → Micro-interações**: spotlight `gradient-follow` (radial seguindo o cursor, CSS vars `--spot-x/--spot-y`, sem re-render) em `KpiCard` e `MetricCard`; ativo em `:hover`/`:focus-visible` e desativado em `prefers-reduced-motion`.
- **WP3 → Skeleton Loading / Empty**: `LoadingSkeleton` com variantes `lines` (larguras relativas) e `card` (blocos de painel) + efeito shimmer; `EmptyState` com ação `onRetry`/`retryLabel`.
- **WP4 → Activity Feed**: `ActivityItem.tone` (dot de severidade com glow), hover da linha e estado vazio (`digest do Timeline.tsx`).
- **WP5 → Charts interativos**: legend clicável (alternar séries) em Line/Area/Bar; estado vazio profissional em Line/Area/Bar/Donut/Heatmap.
- **WP6 → Dashboard Enterprise**: skeleton shimmer real no bloco de 6 KPIs durante load; `aria-busy`.
- **WP7 → Alert Center**: contador de resultados "X de Y alertas" no toolbar.
- **WP8 → War Room**: relógio de "última atualização" com tick (3s), dot de severidade no feed ao vivo, grids principais colapsam para 1 coluna em `<1280px`.
- **WP9 → Acessibilidade**: `:focus-visible` global (anel accent), `color-scheme: dark`, `box-sizing`, scrollbar enterprise, `prefers-reduced-motion` global.

## [2.13 / v0.2.0] - 2026-08-05 — Sprint 2.13 (Estabilização do Projeto)

> Objetivo da sprint: NÃO criar funcionalidade nova. Tornar o projeto consistente
> entre **código, Git e documentação** antes da Sprint 2.14.

#### Adicionado (formalização das entregas de UI que já estavam no código e não documentadas)
- **UI 4.0 — API Client central**: `frontend/src/api/client.ts` — base URL por env (`VITE_API_URL`), timeout (10s), retry (2×, backoff 300ms), erro estruturado e tipos TS alinhados aos schemas Pydantic do backend (`/health`, `/version`, `/metrics`, `/alerts`, `/incidents`, `/cases`).
- **UI 4.0 — Hooks de dados**: `frontend/src/hooks/` — `useMetrics`, `useAlerts`, `useIncidents`, `useCases`, `useHealth` (loading/error/usingMock/refetch).
- **UI 4.1 — Dashboard v0**: `frontend/src/pages/DashboardOverview.tsx` — visão geral do SOC (6 KPIs, série temporal de eventos, gráficos de severidade, tabela de alertas, saúde do sistema, empty states, aviso de API com retry). Conectado ao backend real via hooks.
- **UI 4.2 — War Room**: `frontend/src/pages/WarRoomPage.tsx` — tela única de comando operacional (KPIs, live event feed, MITRE top-5, top assets comprometidos, status dos coletores, saúde da pipeline, mapa geográfico, donut de severidade, resumo operacional). Dados demo rotulados quando a API não responde.
- **Charts**: `frontend/src/charts/` — wrappers Recharts (`SecurityAreaChart`, `SecurityDonutChart`).
- **Proxy de desenvolvimento**: `frontend/vite.config.ts` — `/api` → FastAPI (porta 8080), `VITE_API_URL` opcional.
- **Rota**: `/war-room` adicionada ao `routing/routes.tsx`.

#### Documentado (UI 3.3–3.9 — já presentes no HEAD, agora registradas)
- **UI 3.3 — Layout Enterprise**: Breadcrumb, Global Search, Theme Switch, User Menu, Notifications, Footer (`shell/`).
- **UI 3.4 — Biblioteca de componentes**: KPI Card + MiniSparkline (`cards.tsx`), DataTable Enterprise (`DataTable.tsx`), Toolbar/Empty State/Skeleton (`feedback.tsx`), componentes base (`primitives.tsx`), Activity Feed (`Timeline.tsx`).
- **UI 3.6/3.7 — Live Operations Bar + Global Search Universal**: `shell/LiveOperationsBar.tsx`, `shell/GlobalSearch.tsx`.
- **UI 3.8/3.9 — Alert Center + Detail Drawer**: `pages/AlertCenterPage.tsx`, `pages/AlertDetailDrawer.tsx`.

#### Limpeza / Estabilização
- Arquivos **experimentais/temporários removidos do versionamento** (sem produção): `frontend/build_log.txt`, `frontend/tsc_audit.txt`, `frontend/tsc_current.txt`, `frontend/tsc_current2.txt` → movidos para `archive/frontend_scratch/` (preservados, não versionados); `frontend/tsconfig.tsbuildinfo` removido do tracking (artefato de build incremental).
- `.gitignore` atualizado: `*.tsbuildinfo`, `frontend/build_log.txt`, `frontend/tsc_*.txt`, `archive/frontend_scratch/`.
- Nenhuma funcionalidade backend alterada nesta sprint.

#### Versionamento
- `0.1.0` → `0.2.0` em `pyproject.toml`, `src/edysiem/__init__.py` e `frontend/package.json`. Tag `v0.2.0`.

### Sprint UI 3.0/3.1/3.2 — UX Benchmark + Design System + React Shell

#### Adicionado
- `docs/ENTERPRISE_UX_BENCHMARK.md`: benchmark profundo de UX de 6 SIEMs (Splunk ES, Sentinel, Elastic, Falcon, Wazuh, QRadar) — layout, navegação, sidebar, topbar, dashboards, alert center, investigation, incident, cores, tipografia, espaçamento, métricas, gráficos, tabelas, filtros, experiência do analista + anti-patterns + decisões.
- `frontend/` (estrutura React, sem lógica):
  - `design-system/`: tokens (cores dark + severidade semântica, spacing 4px, typography Inter+JetBrains Mono, radii, shadows, motion) e componentes base (Button, Badge, Card, Input, Table)
  - `theme/ThemeProvider.tsx`: dark default + toggle
  - `state/AppState.tsx`: estado global (density, currentUser)
  - `shell/`: AppShell (3 zonas), Sidebar (workflow), Topbar (global search, time range, alert count)
  - `routing/routes.tsx`: rotas (Overview, Triage, Alertas, Incidentes, Investigar, Cases, Playbooks, Regras, Intel, Config)
  - `App.tsx`, `main.tsx`, `index.html`, `vite.config.ts`, `tsconfig.json`, `package.json`

### Sprint 2.11.4 — Search Engine

#### Adicionado
- `src/edysiem/persistence/search.py`: `SearchEngine` + `SearchResults` — busca desacoplada por Alert/Incident/Case com filtros (ioc/asset/user/hostname/ip/hash/mitre/rule/severity/status), paginação, ordenação, busca parcial (LIKE) e exata.
- `SchemaV3`: tabela `audit_entries` com índices.

### Sprint 2.11.5 — Audit Trail

#### Adicionado
- `src/edysiem/persistence/audit.py`: `AuditEngine` + `AuditEntry` + `AuditRepository` — registros automáticos para criação, atualização, delete lógico, mudança de status, owner, comentários, evidências, playbooks, attachments, tarefas, resolução e reabertura.
- `AuditAction` (StrEnum): CREATE, UPDATE, DELETE, STATUS_CHANGE, OWNER_CHANGE, COMMENT, EVIDENCE, PLAYBOOK, ATTACHMENT, TASK, RESOLUTION, REOPEN.
- Testes: `test_search_audit.py` (+13 casos).

### Sprint 2.11 — Persistence Foundation + Engine + Event Store

#### Adicionado
- Pacote `src/edysiem/persistence/` (100% stdlib, SQLite — ADR-002):
  - `connection.py`: `ConnectionManager` (WAL, foreign keys, pool por thread)
  - `migrations.py`: `Migration` + `MigrationRunner` (schema versionado via `schema_migrations`)
  - `schema.py`: `SchemaV1` (alerts/incidents/cases) + `SchemaV2` (events) com índices básicos
  - `query.py`: `QueryFilter`, `QueryOp`, `SortOrder`, `Page` (filtros declarativos sem SQL espalhado)
  - `repository.py`: `Repository` (Protocol) + `GenericRepository` (CRUD + paginação/ordenação/filtros)
  - `transactions.py`: `TransactionManager` + `UnitOfWork` (transações atômicas)
  - `event_store.py`: `EventStore`/`EventRepository` — persiste a pipeline (RawEvent, CanonicalEvent, EnrichedEvent, CorrelatedEvent, DetectionFinding, Alert, Incident, Case) com UUID, timestamp, correlation_id, pipeline_stage, version e source
  - `repos/`: `AlertRepository`, `IncidentRepository`, `CaseRepository` — CRUD completo + busca por id/fingerprint/status/severidade/data
- Testes: `test_persistence.py`, `test_persistence_engine.py`.
- ADR-002 atualizado com a implementação; docs sincronizados.

### Sprint 2.10 — API v1 + CLI + Health

#### Adicionado
- `src/edysiem/container.py`: `ApplicationContainer` — container DI único conectando todos os engines (normalizer, enrichment, correlation, detection, alerts, incidents, cases).
- `src/edysiem/bootstrap.py`: carregamento de config + build do container + logging.
- `src/edysiem/api/`: FastAPI v1:
  - Rotas: `GET /health`, `GET /version`, `GET /metrics`, `POST /pipeline/run`, `POST /alerts`, `POST /incidents`, `POST /cases`
  - `middleware.py`: RequestID (`X-Request-ID`) + HTTP logging
  - `errors.py`: error handler global + validation handler (422) + handlers de domínio
  - `schemas.py`: modelos Pydantic de request/response
  - `app.py`: factory com lifespan (startup/shutdown), OpenAPI/Swagger (`/docs`) e ReDoc (`/redoc`)
- `src/edysiem/cli/main.py`: CLI Enterprise (`health`, `version`, `config`, `validate-config`, `run-pipeline`, `ingest`, `demo`).
- `[project.scripts] edysiem` entry point + optional-deps `api` (fastapi/uvicorn/pydantic).
- Testes: `test_container.py`, `test_api.py`, `test_cli.py`.
- Docs sincronizados: ARCHITECTURE, DATAFLOW, ROADMAP, SPRINT_BOOK, README, CHANGELOG.

#### Corrigido
- `StrategyNormalizer.register` aceitava apenas `Result[CanonicalEvent]`; relaxado para `Result[object]` (estratégias do registry retornam `Result[object]`).
- `EnrichmentEngine.enrich` é async — `await` nos fluxos da API/CLI.

### Sprint 2.9 — Investigation Workspace + Case Engine

#### Adicionado
- Pacote `src/edysiem/cases/` (workspace do analista SOC):
  - `models.py`: `Case` (id, title, description, owner, status, severity, priority, risk_score, incident_id, alerts, assets, users, iocs, mitre, timeline, comments, attachments, tasks, evidences, playbook, resolution), `CaseStatus` (OPEN→IN_PROGRESS→ON_HOLD→RESOLVED→CLOSED→REOPENED), `CaseEvidence`/`CaseEvidenceKind` (9 tipos), `CaseComment`, `CaseTask`, `CaseAttachment`, `CaseOwner`, `Playbook`/`PlaybookStep`, `CaseMetrics`
  - `timeline.py`: `TimelineEngine` — auto-registro append-only (criado, alerta, status, comentário, anexo, tarefa, owner, resolução, reabertura)
  - `evidence.py`: `EvidenceEngine` — logs/hashes/IPs/domains/arquivos/prints/JSON/IOC/links
  - `notes.py`: `CommentEngine` — notas markdown com autor/data
  - `tasks.py`: `TaskEngine` — criar/concluir/reabrir, prioridade, responsável, prazo
  - `owners.py`: `OwnerEngine` — transferência de responsável (registrada na timeline)
  - `attachments.py`: `AttachmentEngine` — anexos
  - `builder.py`: `CaseBuilder` — Case a partir de Incident
  - `engine.py`: `CaseEngine` — orquestra todos os sub-engines + métricas
  - `registry.py`, `context.py`, `exceptions.py`, `base.py`, `README.md`
- Testes: 4 arquivos, +41 casos (models, sub-engines, workspace completo).
- Docs sincronizados: ARCHITECTURE, DATAFLOW, ROADMAP, SPRINT_BOOK, README, CHANGELOG.

### Sprint 2.8 — Incident Engine Enterprise

#### Adicionado
- Pacote `src/edysiem/incidents/` (agrupamento de Alertas em Incidentes):
  - `models.py`: `Incident` (id, title, description, severity, priority, risk_score, confidence, status, first_seen, last_seen, closed_at, occurrences, alerts, assets, users, iocs, mitre, tactics, techniques, tags, timeline, owner, fingerprint, reason, evidence), `IncidentStatus` (OPEN→TRIAGE→INVESTIGATING→CONTAINED→RESOLVED→CLOSED→REOPENED), `IncidentSeverity`, `IncidentPriority`, `IncidentFingerprint`, `IncidentEvidence`, `IncidentReason`, `IncidentMetrics`
  - `grouping.py`: `GroupingConfig` + `GroupingEngine` — critérios configuráveis (asset, user, ioc, rule, fingerprint, janela temporal, MITRE) com pesos e pontuação mínima
  - `correlator.py`: `IncidentCorrelator` — decisão NEW/DEDUP/NO_GROUP
  - `builder.py`: `IncidentBuilder` — agrega múltiplos Alert em um Incident
  - `lifecycle.py`: `IncidentLifecycleManager` — transições validadas
  - `engine.py`: `IncidentEngine` — orquestra correlator→builder→dedup→lifecycle
  - `registry.py`, `context.py`, `exceptions.py`, `base.py`, `README.md`
- Testes: 4 arquivos, +56 casos (inclui DEMO: 5 alertas de brute force → 1 incidente).
- Docs sincronizados: ARCHITECTURE, DATAFLOW, ROADMAP, SPRINT_BOOK, README, CHANGELOG.

#### Corrigido
- `IncidentCorrelator.__init__` usava `context or IncidentContext()` (mesmo bug do Sprint 2.7 com `__len__`). Corrigido para `context if context is not None else IncidentContext()`.

### Sprint 2.7 — Alert Engine Enterprise

#### Adicionado
- Pacote `src/edysiem/alerts/` (ciclo de vida completo de alertas SOC):
  - `models.py`: `Alert` (id, title, description, severity, priority, risk_score, confidence, first_seen, last_seen, occurrences, status, source, rule, mitre, asset, user, ioc, tags, timeline, fingerprint), `AlertSeverity`, `AlertPriority`, `AlertLifecycle` (state machine), `AlertFingerprint`, `AlertReason`, `AlertTimelineEntry`, `AlertMetrics`
  - `risk.py`: `RiskEngine` + `RiskFactor` (severidade, confiança, asset criticality, threat intel)
  - `fingerprint.py`: `FingerprintEngine` — hash SHA-256 determinístico de campos-chave
  - `builder.py`: `AlertBuilder` — DetectionFinding → Alert
  - `dedupe.py`: `DedupEngine` + `DedupDecision` — occurrences+1 / last_seen atualizado
  - `lifecycle.py`: `LifecycleManager` — OPEN→TRIAGE→INVESTIGATING→RESOLVED/FALSE_POSITIVE
  - `registry.py`: `AlertRegistry` — hooks on_created/on_updated/on_status_changed
  - `context.py`: `AlertContext` — storage in-memory + índice de fingerprints
  - `engine.py`: `AlertEngine` — orquestra Risk→Fingerprint→Builder→Dedup→Lifecycle
  - `exceptions.py`, `base.py`, `README.md`
- Testes: 5 arquivos, +52 casos.
- Docs sincronizados: ARCHITECTURE, DATAFLOW, ROADMAP, SPRINT_BOOK, README, CHANGELOG.

#### Corrigido
- `AlertContext.__len__` torna instância vazia falsy — `context or AlertContext()` criava contexto novo. Corrigido para `context if context is not None else AlertContext()`.
- Enum `AlertLifecycle` não expõe atributo dict interno — mapa de transições movido para nível de módulo.

### Sprint 2.6 — Rule Engine + Detection Framework

#### Adicionado
- Pacote `src/edysiem/detection/` (camada de interpretação de regras sobre CorrelatedEvents):
  - `base.py`: `DetectionRule` (Protocol) + `RuleMetadata` + `DetectionPriority` + `DetectionFinding` + `DetectionReason` + `DetectionDecision`
  - `dsl.py`: `RuleCondition`, `RuleExpression`, `RuleOperator`, `RuleLogicalOp` + parser mínimo (`WHEN ... AND ... THEN`) + `evaluate_expression`
  - `registry.py`: `DetectionRegistry` — ordenação topológica por prioridade + dependências, detecção de ciclos
  - `rule_engine.py`: `RuleEngine` — carregar/registrar/validar/executar regras, isolamento de falhas, timeout, prioridade, métricas
  - `engine.py`: `DetectionEngine` + `DetectionOutcome` + `DetectionSummary` (sem Alert ainda)
  - `context.py`: `DetectionContext` — buffers temporais + cache compartilhado
  - `models.py`: `DetectionResult`, `DetectionOutcome`, `DetectionMetrics`
  - `exceptions.py`: hierarquia de erros
  - `plugins/demo.py`: **regra DEMO** `LoginFailuresRule` (mais de N falhas de login em X minutos)
  - `plugins/README.md`: guia de desenvolvimento de regras
- Testes: 7 arquivos, +103 casos (DSL, base, registry, rule_engine, detection engine, demo, coverage).
- Docs sincronizados: ARCHITECTURE, DATAFLOW, ROADMAP, SPRINT_BOOK, README, CHANGELOG.

#### Corrigido
- `RuleExpression.evaluate` passa a despachar corretamente entre `RuleCondition` (valor escalar) e `RuleExpression` (mapa field→valor).
- Comparação de severidade na DSL usa rank ordinal (info<low<medium<high<critical) em vez de comparação de string.

### Sprint 2.5 — Correlation Engine Framework

#### Adicionado
- Pacote `src/edysiem/correlation/` **desacoplado e extensível** (framework de regras, sem regras hardcoded):
  - `base.py`: `CorrelationRule` (Protocol) + `CorrelationMetadata` + `CorrelationPriority` + `CorrelationMatch` + `CorrelationReason` + `CorrelationDecision`
  - `registry.py`: `CorrelationRegistry` — ordenação topológica por prioridade + dependências, detecção de ciclos
  - `engine.py`: `CorrelationEngine` + `CorrelationMetrics` — execução por prioridade, isolamento de falhas, timeout por regra, métricas
  - `context.py`: `CorrelationContext` — janelas temporais por `(rule_id, identity_key)` com TTL
  - `models.py`: `CorrelationResult`, `CorrelatedEvent`, `CorrelationMetrics`
  - `exceptions.py`: hierarquia de erros do framework
  - `plugins/README.md`: guia de desenvolvimento de regras
  - `plugins/demo.py`: **regra DEMO** `ThresholdByIpRule` (mesmo IP gerou N eventos em X minutos)
- Testes: 5 arquivos, +74 casos (base, context, registry, engine, plugins demo, coverage).
- Docs sincronizados: ARCHITECTURE, DATAFLOW, ROADMAP, SPRINT_BOOK, CHANGELOG.

#### Corrigido
- Filtro de `required_fields` no engine: regra é pulada quando o evento **não tem** o campo exigido (lógica invertida).
- Janela temporal do `CorrelationContext` robusta a inserções fora de ordem.

### Sprint 2.4 — Enrichment Engine (Arquitetura Enterprise)

#### Adicionado
- Pacote `src/edysiem/enrichment/` **desacoplado e extensível** (framework, sem enriquecedores reais):
  - `base.py`: `EnrichmentPlugin` (Protocol) + `PluginMetadata` + `PluginPriority` + `PluginResult`
  - `registry.py`: `EnrichmentRegistry` — ordenação topológica por prioridade + dependências, detecção de ciclos
  - `engine.py`: `EnrichmentEngine` + `EnrichmentMetrics` — timeout por plugin, isolamento de falhas, batch, health
  - `context.py`: `EnrichmentContext` — asset/geo/intel/user providers, cache TTL, métricas hit/miss
  - `models.py`: `Enrichment`, `EnrichmentKind`, `CachePolicy`, `EnrichmentResult`
  - `exceptions.py`: hierarquia de erros do framework
  - `plugins/README.md`: guia de desenvolvimento de plugins
- Testes: 8 arquivos, +82 casos (metadados, registry, context, providers, engine, modelos).
- Suporte `pytest-asyncio` (asyncio_mode=auto) adicionado ao `pyproject.toml`.

### Sprint 2.3 — Canonical Pipeline + Parser Enterprise

#### Adicionado
- `src/edysiem/parsers/`: Syslog RFC3164 + RFC5424 (structured-data) — parsers puros que retornam `Result`.
- `src/edysiem/normalization/`: `StrategyNormalizer` + `Registry` (Strategy pattern + plugin discovery).
- `CanonicalEvent` v2: campos `event_category`/`event_action`, `command_line`, `vendor`, `product`,
  `event_original`, `normalized_fields`, `confidence`, `metadata`, `schema_version`.
- Testes: parsers (19), normalizer (10), pipeline models atualizados.

### Sprint 2.2 — Infraestrutura de Ingestão Enterprise (ADR-009)

#### Adicionado
- Pacote `src/edysiem/ingestion/` **desacoplado e reutilizável**:
  - `collectors/base.py`: `CollectorPlugin` Enterprise (start/stop/read/health/metadata/capabilities)
  - `queue.py`: `RawEventQueue` FIFO thread-safe e async-ready (drop policy + timeout)
  - `backpressure.py`: `BackpressureController` (HIGH/LOW water marks, NORMAL/PAUSED)
  - `retry.py`: `RetryPolicy` (backoff exponencial + jitter) + `run_with_retry`
  - `dead_letter.py`: `DeadLetterQueue` — eventos inválidos nunca descartados em silêncio
  - `rate_limiter.py`: `TokenBucketRateLimiter` (events/sec + burst)
  - `health.py`: `HealthMonitor` + `CollectorHealth` por collector
  - `metrics.py`: `MetricsRegistry` (contadores/gauges/timers, sem dependência externa)
- `ErrorCode.QUEUE_FULL` adicionado ao `result` (contrato da fila).
- `plugins/contracts.py` re-exporta o novo `CollectorPlugin` (protocolo antigo substituído).
- Docs: `PIPELINE.md` criado; ARCHITECTURE, OBSERVABILITY, PERFORMANCE_DESIGN, SPRINT_BOOK atualizados; ADR-009.

#### Melhorado
- Testes: 254 (cobertura 98.26%), mypy strict 0 (40 arquivos), ruff check+format limpos.

### Sprint 2.1 — Foundation da Pipeline

#### Saneamento técnico
- Removida duplicação de `_utcnow()`/`_new_id()` (extraído para `src/edysiem/_utils.py`).
- Corrigida semântica de `published` no `EventBus` (falso quando não há handlers executados;
  `_finish` respeita handlers já executados antes de cancelamento).
- Renomeado `EventRegistry.unable()` → `enable()` — API simétrica com `disable`,
  erros consistentes (`PluginException` p/ não encontrado, `DomainException` p/ já habilitado).
- Removido dead code: `PluginVersion`, `PluginContract`, `_context_manager` vestigial,
  `StructuredFormatter._to_dict` (pass-through), campo `LoggingConfig.format` sem consumidor.
- Corrigido vazamento de `TypeError` em `ConfigLoader._apply_overrides` — override inválido
  agora vira `ConfigurationException` (honra o contrato "sempre Result, nunca exceção").

### Modelos da pipeline (fundação) — ADR-008
- Adicionados modelos imutáveis em `src/edysiem/domain/pipeline.py`:
  `RawEvent → ParsedEvent → CanonicalEvent → EnrichedEvent` (+ value object `Enrichment`).
- Pipeline oficial documentada: `Collector → RawEvent → Parser → ParsedEvent → Normalizer →
  CanonicalEvent → Enrichment → EnrichedEvent → Correlation → Detection → Alert → Incident → Case`.
- Contratos de plugins evoluídos: `ParserPlugin.parse(RawEvent) → Result[list[ParsedEvent]]`,
  `EnrichmentPlugin.enrich(CanonicalEvent) → Result[EnrichedEvent]`,
  `AnalyzerPlugin.analyze(EnrichedEvent) → Result[list[Alert]]`,
  `ExporterPlugin.export(list[CanonicalEvent])`.
- Exemplo de uso: `examples/pipeline_models_demo.py`; testes unitários `tests/test_pipeline_models.py`.
- Docs de arquitetura sincronizadas: ARCHITECTURE, DATAFLOW, SYSTEM_DESIGN, DOMAIN_MODEL,
  ADR-008, PROJECT_STRUCTURE, BACKEND_GUIDE, SPRINT_BOOK.

## [0.1.0] - 2026-08-03 — Foundation Core (Sprint 1)

### Sprint 1 — Foundation Core

#### Adicionado
- `config/`: configuração central tipada, env-driven, com defaults e validação.
- `events/`: Event Bus async-ready (publisher/subscriber, registry, prioridade, cancelamento).
- `domain/`: 11 entidades + 12 enums (dataclasses puras, sem infraestrutura).
- `result/`: `Result[T]` estilo Rust — Success/Failure, ErrorCode, nunca `None`.
- `exceptions/`: hierarquia Domain, Validation, Infrastructure, Plugin, Configuration, Security.
- `logging/`: logger estruturado JSON + correlation/request/session ID + saneamento sensível.
- `plugins/`: 7 contratos (Parser, Collector, Analyzer, Enrichment, Exporter, Notification, Base).
- `di/`: container DI manual (Singleton, Scoped, Transient) + detecção de ciclo.
- `validation/`: motor declarativo de validação + validadores (IP, email, URL, hash, UUID).
- Testes: 110 casos, cobertura 98.44%, mypy strict 0 erros, ruff limpo.
- Infraestrutura: `pyproject.toml` (hatchling, src-layout), `conftest.py`, `.gitignore`.

#### Corrigido (durante a Sprint 1)
- `events/base.py`: `CancellationToken` referenciado mas não definido.
- `events/bus.py`: rota de cancelamento chamava `_finalize()` inexistente.
- `domain/entities.py`: dataclasses com `non-default follows default` (módulo quebrado).
- `logging/filters.py`: indentação quebrada no método `filter()`.
- `src/edysiem` sem `__init__.py` raiz → namespace quebrado (sem `__version__`).

### Sprint 0 — Fundação

#### Adicionado
- 52+ documentos: visão de produto, arquitetura, design system, UX, ADRs 001–007,
  benchmark de SIEMs (Sentinel, Splunk ES, QRadar, Elastic, Wazuh, Graylog,
  Chronicle, Exabeam, Securonix), guias de estudo e qualidade.
