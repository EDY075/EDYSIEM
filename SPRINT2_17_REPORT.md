# EDY SIEM — Relatório Técnico da Sprint 2.17 (Detection Engineering + Threat Intelligence)

**Data:** 05/08/2026
**Produto:** EDY SIEM — Security Information and Event Management
**Objetivo:** detectar, enriquecer e contextualizar eventos, aproximando o fluxo de um
SOC moderno. **Reutiliza `SocService` e a API `/soc/*` existentes** — sem duplicar
lógica, sem quebrar arquitetura.
**Status:** ✅ CONCLUÍDA

---

## Commits (1 por WP / buildável)

| WP | Entrega | Commit |
|---|---|---|
| WP1–5 | Backend: SchemaV4 + Rule Engine gerenciável + Simulator + IOC + Asset + Detection Dashboard + API | `b1597d6` |
| WP6 | Frontend: `IntelligencePage` (Rules/Simulator/IOC/Assets) + `DetectionDashboardPage` | `97028dd` |
| — | Lint (E501/PT018) | `f8d319f` |

## Arquivos modificados
- `src/edysiem/persistence/schema.py` — **SchemaV4**: `det_rules`, `iocs`, `assets`.
- `src/edysiem/soc/service.py` — Rule catalog (`register/list/set_enabled` + auto fire_count), `simulate_rule`, IOC (`register/list/related`), Asset (`register/list/related`), `detection_stats`.
- `src/edysiem/api/routes/soc.py` — `/soc/rules`, `/soc/simulator`, `/soc/iocs`, `/soc/assets`, `/soc/detection`.
- `frontend/src/pages/{IntelligencePage,DetectionDashboardPage}.tsx`, `routing/routes.tsx`.
- Testes + docs.

## Testes / Cobertura

| Check | Resultado |
|---|---|
| `pytest` | ✅ **~783 testes** — coverage **95.11%** (fail-under 95) |
| `mypy` (strict) | ✅ 0 erros (145 arquivos) |
| `ruff check` / `format` | ✅ limpos |
| `npm run build` / `tsc -b` | ✅ verdes |
| Working tree | ✅ limpa |

## Critérios de aceite

| Critério | Status |
|---|---|
| Rule Engine gerenciável (listar/habilitar/desabilitar/severidade/categoria/MITRE/tags/contador) | ✅ |
| Rule Simulator funcional (regra aplicada/score/alerta/motivo — sem tocar a pipeline) | ✅ |
| IOC Manager operacional (IP/domínio/URL/hash/e-mail, reputação, first/last, incidentes/casos) | ✅ |
| Asset Inventory operacional (hostname/IP/OS/criticidade/owner/status/última com + relação) | ✅ |
| Detection Dashboard funcionando (top rules, MITRE, IOC, assets críticos, tendência) | ✅ |
| Integração total com APIs (frontend sem mock) | ✅ |
| Build verde / Testes verdes / Working tree limpa | ✅ |
| Screenshots das novas telas | ⚠️ pendente (browser) |

## Performance
- Frontend com **code-splitting** (todas as rotas lazy) — novas telas `/rules`, `/intel`, `/detection` entram como chunks dedicados; bundle inicial permanece ~248 kB (gzip ~80 kB).
- `persist_alert` incrementa `fire_count` na mesma transação atômica (sem overhead extra).

## Fluxo demonstrado
1. `POST /soc/rules` cria regras (ex.: `brute-force-ssh`, categoria `authentication`, MITRE `T1110`).
2. `POST /soc/pipeline/demo` gera alertas reais → `persist_alert` incrementa `fire_count`.
3. `POST /soc/simulator` valida a aplicação da regra sobre um evento JSON (score/motivo/alerta).
4. `POST /soc/iocs` e `GET /soc/iocs/{value}/related` → reputação + incidentes/casos.
5. `POST /soc/assets` → inventário crítico.
6. `GET /soc/detection` → dashboard (top rules/MITRE/IOC/assets/trend).

## Pendências
1. Screenshots das telas (browser).
2. Simulador avalia por metadados (rule_id/categoria/tag) — pode evoluir para DSL de condições.
3. Feed de intel externo (reputação online) — Sprint 2.20.
4. IOC hash/email já suportados em tipo; enriquecedor externo é encaminhamento futuro.

## Próxima Sprint recomendada
**Sprint 2.18 — Escala**: fila externa (Kafka via contrato), storage PostgreSQL via
Protocol, Auth/SSO.

---

> Relatório gerado pelo TITAN AI SQUAD (jr + ATLAS + VULCAN + PROOF).