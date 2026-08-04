# EDY SIEM — Roadmap

> Planejamento por sprints. **Regra Nº 1: arquitetura aprovada antes de funcionalidade.**
> Toda sprint de feature exige: docs → ADR (se preciso) → contrato → código → testes → docs.

## Fase 0 — Fundação (atual)

| Sprint | Entrega | Status |
|---|---|---|
| S0.1 | Visão do Produto | ✅ `PRODUCT_VISION.md` |
| S0.2 | Arquitetura | ✅ `ARCHITECTURE.md` + ADRs |
| S0.3 | Modelagem | ✅ `DATABASE.md` + `SYSTEM_DESIGN.md` |
| S0.4 | UX | 📋 fluxos e wireframes (próxima) |
| S0.5 | Design System | 📋 tokens + componentes (próxima) |
| S0.6 | Estrutura do Projeto | 📋 bootstrap do repo |

## Fase 1 — Núcleo

- S1.1 `core`: modelos, erros, contratos (tipados) + testes.
- S1.2 `persistence`: repositórios SQLite + migrações + testes.
- S1.3 `ingestion` + `normalization`: ingestão manual + parser syslog + testes.
- S1.4 `enrichment`: asset + geo/intel básicos.
- S1.5 `correlation` + `detection`: rule engine declarativo + regras iniciais + MITRE.
- S1.6 `incident`: engine de incidentes + ciclo de vida.
- S1.7 `api` v1 + `cli` + health.
- S1.8 `ui` v0: shell + design tokens + tela Events/Alerts.

## Fase 2 — Operação SOC

- S2.1 Dashboard Overview (KPIs, timeline, alertas críticos).
- S2.2 Investigação (drawer, evidências, timeline, notas).
- S2.3 Rules UI (criar/editar regras com validação + teste rápido).
- S2.4 Intelligence (IOC manager) + Assets.
- S2.5 Incident UI (triagem, ciclo de vida, auditoria).
- S2.6 Collectors syslog/file + Windows Event (futuro).

## Pipeline (Fase 1.5 — em andamento)

> Pipeline de eventos oficial (ADR-008). Sprints implementadas sobre o núcleo.

| Sprint | Entrega | Status |
|---|---|---|
| 2.1 | Foundation da Pipeline (ADR-008 + modelos) | ✅ Concluída |
| 2.2 | Infraestrutura de Ingestão Enterprise (ADR-009) | ✅ Concluída |
| 2.3 | Canonical Pipeline + Parser Enterprise (RFC3164/RFC5424 + normalizer) | ✅ Concluída |
| 2.4 | Enrichment Engine (framework Enterprise) | ✅ Concluída |
| 2.5 | Correlation Engine Framework (regras declarativas + janelas) | ✅ Concluída |
| 2.6 | Rule Engine + Detection Framework (DSL + DetectionRule) | ✅ Concluída |
| 2.7 | Alert Engine Enterprise (risk/fingerprint/dedup/lifecycle) | ✅ Concluída |
| 2.8 | Incident Engine Enterprise (grouping/correlator/lifecycle) | ✅ Concluída |
| 2.9 | Investigation Workspace + Case Engine | ✅ Concluída |
| 2.10 | API v1 + CLI + Health (FastAPI, OpenAPI, Swagger) | ✅ Concluída |
| 2.11 | Persistence Foundation + Engine + Event Store | ✅ Concluída |
| 2.12 | Search Engine + Audit Trail | ✅ Concluída |
| 2.13 | Engines + persistência + pipeline E2E | ⏳ Próxima |
| UI 3.0 | UX Benchmark (6 SIEMs) | ✅ Concluída |
| UI 3.1 | Design System (tokens + componentes base) | ✅ Concluída |
| UI 3.2 | React Shell (sidebar/topbar/routing/theme/state) | ✅ Concluída |
| 2.14 | Dashboard v0 (KPIs, alertas criticos) | ⏳ Próxima |
| 2.9 | API v1 + CLI + health | planejada |
| 2.10 | UI v0 (shell + tokens + Events/Alerts) | planejada |

## Fase 3 — Escala

- S3.1 Fila externa plugável (Kafka) via contrato.
- S3.2 Storage alternativo (PostgreSQL) via Protocol.
- S3.3 Auth OAuth/SSO, RBAC refinado.
- S3.4 Threat intel online (feed) + correlação enriquecida.
- S3.5 Hunting UI (MITRE navigator-like).
- S3.6 Multi-tenant e particionamento/retention.

## Critério de pronto (Definition of Done)

- [ ] Código tipado, testado, documentado
- [ ] ADR atualizado quando decisão
- [ ] API/CLI com contrato documentado
- [ ] Guia de estudo atualizado
- [ ] CI verde (pytest, mypy, ruff, coverage ≥ 85%)
