# Changelog

Todas as mudanças notáveis do EDY SIEM serão documentadas neste arquivo.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
e o projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Não publicado] — Sprint 2.1 (Foundation da Pipeline)

### Saneamento técnico
- Removida duplicação de `_utcnow()`/`_new_id()` (extraído para helper compartilhado).
- Corrigida semântica de `published` no `EventBus` (falso quando não há handlers).
- Renomeado `EventRegistry.unable()` → `enable()` (API pública simétrica com `disable`).
- Removido dead code (`PluginVersion`, `PluginContract`, `_context_manager` vestigial).
- Corrigido vazamento de `TypeError` em `ConfigLoader._apply_overrides` (agora vira `ConfigurationException`).
- Sincronizada documentação com a estrutura real `src/edysiem/`.

### Modelos da pipeline (fundação)
- Adicionados modelos imutáveis do fluxo oficial:
  `RawEvent → ParsedEvent → CanonicalEvent → EnrichedEvent`.
- Contratos de plugins ajustados para os novos modelos de evento.
- Exemplos de uso + testes unitários.

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
