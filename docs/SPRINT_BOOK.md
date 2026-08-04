# EDY SIEM — Sprint Book

> Registro oficial de todas as sprints. **Toda sprint futura deve ser registrada aqui**
> antes de iniciar e revisada ao final (lições aprendidas).

## Formato obrigatório de registro

```markdown
## Sprint N.N — <Título>

- **Status:** Planejada | Em andamento | Concluída
- **Data:** ...
- **Objetivo:** ...
- **Escopo:** ...
- **Arquivos afetados:** ...
- **Resultado:** ...
- **Lições aprendidas:** ...
- **Pendências:** ...
```

## Histórico

### Sprint 0 — Fundação
- **Status:** Concluída
- **Objetivo:** visão, arquitetura, modelagem, UX, design system, estrutura.
- **Arquivos:** `docs/` completo (visão, arquitetura, ADRs, design, UX, wireframes), `README.md`, `PROJECT_MANIFESTO.md`.
- **Resultado:** fundação documental completa; zero funcionalidade.
- **Lições:** critério "daqui a um ano" em toda decisão; benchmark orientou direcionamentos.

### Sprint 0.1 — Manifesto
- **Status:** Concluída
- **Objetivo:** posicionamento Enterprise do produto.
- **Arquivos:** `PROJECT_MANIFESTO.md`.
- **Resultado:** missão, visão, valores, não-objetivos, compromisso.

### Sprint 0.2 — Benchmark
- **Status:** Concluída
- **Objetivo:** estudar 9 SIEMs comerciais.
- **Arquivos:** `docs/research/benchmark.md`.
- **Resultado:** tabela comparativa + direcionamentos (modelo canônico, MITRE, incident aggregator, entity-centric, risk score).
- **Lições:** inspiração, nunca cópia.

### Sprint 0.3 — Design System
- **Status:** Concluída
- **Objetivo:** design system completo criado do zero.
- **Arquivos:** `docs/design/{DESIGN_SYSTEM,COMPONENT_LIBRARY,DESIGN_GUIDE,UI_GUIDE}.md`.
- **Resultado:** tokens, componentes, padrões, DoR UI.

### Sprint 0.4 — Arquitetura
- **Status:** Concluída
- **Objetivo:** arquitetura completa + dataflow.
- **Arquivos:** `docs/{ARCHITECTURE,SYSTEM_DESIGN,DATAFLOW}.md`, ADR-007.
- **Resultado:** fluxo etapa por etapa, Clean Architecture, SOLID, DI, plugin system.

### Sprint 0.5 — UX Architecture
- **Status:** Concluída
- **Objetivo:** projetar toda experiência do usuário.
- **Arquivos:** `docs/design/{UX_ARCHITECTURE,SCREEN_MAP,USER_JOURNEY,UX_FLOW,WIREFRAMES}.md`.
- **Resultado:** 4 perguntas por tela, jornadas por perfil, wireframes ASCII.

### Sprint 0.6 — Enterprise Foundation
- **Status:** Concluída
- **Objetivo:** infraestrutura Enterprise (docs de convenções, qualidade, logging, eventos, banco, API, git).
- **Arquivos:** `docs/{PROJECT_STRUCTURE}.md`, `docs/guides/{CODING,GIT_WORKFLOW,QUALITY,LOGGING_DESIGN,EVENT_BUS}.md`, `docs/{DATABASE_DESIGN,API_DESIGN}.md`, `docs/SPRINT_BOOK.md`.
- **Resultado:** fundação Enterprise pronta para Sprint 1.
- **Lições:** documentação como produto; nada de código sem contrato.

### Sprint 1 — Foundation Core
- **Status:** Concluída
- **Data:** 2026-08-03
- **Objetivo:** núcleo do produto (config, events, domain, result, exceptions, logging, plugins, di, validation).
- **Arquivos:** `src/edysiem/**` (28 arquivos), `tests/` (110 testes), `pyproject.toml`, `conftest.py`, `SPRINT1_REPORT.md`.
- **Resultado:** 110 testes, cobertura 98.44%, mypy strict 0, ruff limpo. Commit `3876a74`, tag `v0.1.0`.
- **Lições:** dataclasses — obrigatórios antes de defaults; EventBus com Protocol; DI manual com detecção de ciclo.

### Sprint 2.1 — Foundation da Pipeline
- **Status:** Concluída
- **Data:** 2026-08-03
- **Objetivo:** saneamento técnico (dívidas da auditoria) + pipeline oficial (ADR-008) + modelos imutáveis.
- **Arquivos:** `src/edysiem/_utils.py`, `src/edysiem/domain/pipeline.py`, `tests/test_pipeline_models.py`, `examples/pipeline_models_demo.py`, contratos de plugins, docs de arquitetura (ARCHITECTURE, DATAFLOW, SYSTEM_DESIGN, DOMAIN_MODEL, ADR-008).
- **Resultado:** 142 testes, cobertura 98.53%, mypy strict 0, ruff check+format limpos.
- **Lições:** `dataclasses.replace` não deriva subclasse com campos novos (usar `asdict` + construção); `unable`→`enable` com erros consistentes; `TypeError` de override → `ConfigurationException` (contrato Result).

### Sprint 2.2 — Infraestrutura de Ingestão Enterprise
- **Status:** Concluída
- **Data:** 2026-08-03
- **Objetivo:** infraestrutura de ingestão reutilizável e desacoplada (ADR-009) — sem parsers reais.
- **Arquivos:** `src/edysiem/ingestion/` (collectors/base, queue, backpressure, retry, dead_letter, rate_limiter, health, metrics), `tests/test_ingestion_*.py` (8 arquivos), `docs/PIPELINE.md`, `docs/adr/ADR-009-ingestion-infrastructure.md`.
- **Resultado:** 254 testes, cobertura 98.26%, mypy strict 0 (40 arquivos), ruff check+format limpos.
- **Lições:** fila thread-safe + async-ready com `deque`+Lock+`asyncio.Event` lazy (single-loop); `put_nowait` não consulta backpressure (produtor síncrono usa `can_accept`); `ErrorCode.QUEUE_FULL` adicionado.

### Sprint 2.3 — Canonical Pipeline + Parser Enterprise
- **Status:** Concluída
- **Data:** 2026-08-03
- **Objetivo:** parsers reais + normalizer com Strategy pattern sobre a pipeline (ADR-008).
- **Arquivos:** `src/edysiem/parsers/` (syslog RFC3164, rfc5424), `src/edysiem/normalization/` (normalizer, registry), `src/edysiem/domain/pipeline.py` (CanonicalEvent v2), testes.
- **Resultado:** parsers e normalizer consolidados; 361 testes, cobertura 95.14%.

### Sprint 2.4 — Enrichment Engine (Arquitetura Enterprise)
- **Status:** Concluída
- **Data:** 2026-08-03
- **Objetivo:** framework de enrichment desacoplado e extensível, sem enriquecedores reais.
- **Arquivos:** `src/edysiem/enrichment/` (base, registry, engine, context, models, exceptions, plugins/README.md), 8 testes.
- **Resultado:** `EnrichmentPlugin` Protocol + Registry com ordenação topológica + Engine com isolamento de falhas/timeout; 361 testes, cobertura 95.14%, mypy strict 0.
- **Lições:** `EnrichmentMetrics` não pode ser frozen (muta em record_execution); dois tipos de `Enrichment` (domain vs models) exigem conversão explícita; `unwrap_err()` não existe na API do Result.

### Sprint 2.5 — Correlation Engine Framework
- **Status:** Concluída
- **Data:** 2026-08-03
- **Objetivo:** framework de correlacao desacoplado e extensível, com regras declarativas (sem hardcode).
- **Arquivos:** `src/edysiem/correlation/` (base, registry, engine, context, models, exceptions, plugins/), 5 testes de framework + demo.
- **Resultado:** `CorrelationRule` Protocol + Registry ordenado + Engine com janelas temporais (contexto), isolamento de falhas, timeout e métricas; regra DEMO `ThresholdByIpRule`; 435 testes, cobertura 95.19%, mypy strict 0.
- **Lições:** filtro de `required_fields` no engine deve pular regras que exigem campo AUSENTE (não presentes); janela temporal precisa ser robusta a inserções fora de ordem.

### Sprint 2.6 — Rule Engine + Detection Framework
- **Status:** Concluída
- **Data:** 2026-08-03
- **Objetivo:** camada de interpretação de regras de detecção sobre eventos correlacionados (sem regras reais, sem Sigma/MITRE).
- **Arquivos:** `src/edysiem/detection/` (base, registry, rule_engine, engine, context, models, dsl, exceptions, plugins/), 7 arquivos de teste.
- **Resultado:** `DetectionRule` Protocol + `RuleMetadata` (severidade, confiança, risco) + `RuleEngine` (carregar/registrar/validar/executar) + `DetectionEngine` (produz DetectionOutcome/DetectionDecision) + DSL declarativa (WHEN/AND/THEN); regra DEMO `LoginFailuresRule`; 538 testes, cobertura 95.08%, mypy strict 0.
- **Lições:** `RuleExpression.evaluate` precisa despachar entre RuleCondition (escalar) e RuleExpression (mapa); comparação de severidade exige rank ordinal (string não ordena); DSL de valores dinâmicos usa Any intencional.

### Sprint 2.7 — Alert Engine Enterprise
- **Status:** Concluída
- **Data:** 2026-08-03
- **Objetivo:** ciclo de vida completo de um alerta SOC (Risk, Fingerprint, Builder, Dedup, Lifecycle) - sem Cases/Dashboard.
- **Arquivos:** `src/edysiem/alerts/` (base, models, risk, fingerprint, builder, dedupe, lifecycle, registry, context, engine, exceptions, README), 5 arquivos de teste.
- **Resultado:** `Alert` operacional (id, titulo, severidade, prioridade, risco, confianca, occurrences, timeline, fingerprint) + `RiskEngine` (fatores) + `FingerprintEngine` (SHA-256 deterministico) + `DedupEngine` (occurrences+1) + `LifecycleManager` (OPEN->TRIAGE->INVESTIGATING->RESOLVED/FALSE_POSITIVE) + `AlertEngine`; 590 testes, cobertura 95.13%, mypy strict 0.
- **Lições:** `AlertContext.__len__` torna instancia vazia falsy - usar `context if context is not None else AlertContext()` (NUNCA `or`); Enum não expõe atributo dict interno (`_TRANSITIONS`) - mover mapa para nivel de modulo.

### Sprint 2.8 — Incident Engine Enterprise
- **Status:** Concluída
- **Data:** 2026-08-03
- **Objetivo:** agrupar Alertas relacionados em Incidentes (sem Case Management/Dashboard).
- **Arquivos:** `src/edysiem/incidents/` (models, grouping, correlator, builder, lifecycle, registry, context, engine, exceptions, base, README), 4 arquivos de teste.
- **Resultado:** `Incident` (id, titulo, severidade, prioridade, risco, status, occurrences, alerts, assets, users, iocs, mitre, timeline, owner, fingerprint) + `GroupingEngine` (criterios configuraveis: asset/user/ioc/rule/fingerprint/janela/MITRE) + `IncidentBuilder` (agrega alertas) + `IncidentCorrelator` (NEW/DEDUP/NO_GROUP) + `LifecycleManager` (OPEN->TRIAGE->INVESTIGATING->CONTAINED->RESOLVED->CLOSED->REOPENED); 646 testes, cobertura 95.09%, mypy strict 0.
- **Lições:** repetido o bug do Sprint 2.7 (`context or Default()` com `__len__`) no `IncidentCorrelator` - corrigido; criterios de agrupamento com pesos (RULE/ASSET/USER/IOC/FINGERPRINT/TIME/MITRE) normalizados 0-100 com min_score configuravel.

### Sprint 2.9 — Investigation Workspace + Case Engine
- **Status:** Concluída
- **Data:** 2026-08-03
- **Objetivo:** workspace operacional do analista SOC (timeline, evidencias, notas, tarefas, ownership, anexos, playbook).
- **Arquivos:** `src/edysiem/cases/` (models, timeline, evidence, notes, tasks, owners, attachments, builder, engine, registry, context, exceptions, base, README), 4 arquivos de teste.
- **Resultado:** `Case` (workspace completo) + `TimelineEngine` (append-only auto-registro) + `EvidenceEngine` (9 tipos de evidencia) + `CommentEngine` (markdown) + `TaskEngine` (criar/concluir/reabrir) + `OwnerEngine` (transferencia) + `AttachmentEngine` + `Playbook` (estrutura); 687 testes, cobertura 95.39%, mypy strict 0.
- **Lições:** sub-engines compartilham um `TimelineEngine` unico para auto-registro; `dataclasses.replace` para reconstruir Case imutavel; hooks de registry com isolamento (S112 intencional).

### Sprint 2.10 — API v1 + CLI + Health
- **Status:** Concluída
- **Data:** 2026-08-03
- **Objetivo:** transformar os engines em plataforma utilização (API REST, CLI, health, metrics, version) - sem Dashboard.
- **Arquivos:** `src/edysiem/container.py` (ApplicationContainer), `src/edysiem/bootstrap.py`, `src/edysiem/api/` (app, routes, middleware, errors, schemas, deps), `src/edysiem/cli/` (main), testes.
- **Resultado:** FastAPI v1 (GET /health, /version, /metrics; POST /pipeline/run, /alerts, /incidents, /cases) + OpenAPI/Swagger + RequestID + HTTP logging + error handlers + CLI (`health`, `version`, `config`, `validate-config`, `run-pipeline`, `ingest`, `demo`); 713 testes, cobertura 95.27%, mypy strict 0.
- **Lições:** container unico (DI) alimenta API e CLI; lifespan inicializa engines; `container` no app.state para TestClient; Depends() no argument default e padrao FastAPI (B008 ignorado).

## Próximas sprints (planejadas)

- **Sprint 2.11** — Persistência (SQLite) para Alert/Incident/Case contexts.
- **Sprint 2.12** — Dashboard v0 (KPIs, alertas criticos).
- **Sprint 2.8** — API v1 + CLI + health.
- **Sprint 2.9** — UI v0: shell + tokens + tela Events/Alerts.
- **Sprint 2.7** — API v1 + CLI + health.
- **Sprint 2.8** — UI v0: shell + tokens + tela Events/Alerts.
