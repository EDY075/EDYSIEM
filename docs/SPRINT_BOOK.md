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

## Próximas sprints (planejadas)

- **Sprint 2.3** — Ingestão e Normalização: parser syslog (RFC 3164/5424) + normalizer real + testes de integração.
- **Sprint 2.4** — Enrichment: enricher base + asset/intel + testes.
- **Sprint 2.5** — Correlation/Detection: rule engine + MITRE + testes.
- **Sprint 2.6** — Incident engine + ciclo de vida.
- **Sprint 2.7** — API v1 + CLI + health.
- **Sprint 2.8** — UI v0: shell + tokens + tela Events/Alerts.
