# Changelog

Todas as mudanças notáveis do EDY SIEM serão documentadas neste arquivo.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
e o projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Não publicado]

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
