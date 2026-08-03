# Changelog

Todas as mudanças notáveis do EDY SIEM serão documentadas neste arquivo.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
e o projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Não publicado] — Sprint 2.1 (Foundation da Pipeline)

### Saneamento técnico
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
