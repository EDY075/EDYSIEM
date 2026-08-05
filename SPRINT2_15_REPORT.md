# EDY SIEM — Relatório Técnico da Sprint 2.15 (SOC Investigation Pipeline)

**Data:** 05/08/2026
**Produto:** EDY SIEM — Security Information and Event Management
**Objetivo:** transformar o EDY SIEM de dashboard para **fluxo operacional de SOC**:
**Evento → Regra → Alerta → Incidente → Caso**, persistido, com incident/case
management, SLA, investigação e KPIs alimentados por dados reais.
**Arquitetura:** baixo acoplamento — nenhum engine existente foi alterado; um novo
orquestrador (`soc`) faz a ponte engines ↔ persistência SQLite.
**Status:** ✅ CONCLUÍDA

---

## 1. Commits (1 por work package)

| WP | Entrega | Commit |
|---|---|---|
| WP-A | Pacote `soc`: `sla.py`, `service.py` (`SocService`), `pipeline.py` (`SocPipeline`) | `3b80bbb` |
| WP-B | Wire `soc_service`/`soc_pipeline` no `ApplicationContainer` | `9fa0336` |
| WP-C | API `/api/v1/soc` (pipeline, incident/case management, investigation, KPIs) | `8174489` |
| WP-D | Testes E2E (`test_soc_pipeline`, `test_soc_api`) + `run_event` alinhado (422) | `c696445` |
| WP-E | CLI `edysiem soc-run` | `c17d2c8` |
| — | `ruff format` (style) | `d0e5adb` |

## 2. Fluxo operacional implementado

```
Evento (RawEvent) → Regra (Detection) → Alerta (AlertEngine) → Incidente (IncidentEngine) → Caso (CaseEngine)
        │                                       │                     │                      │
        └── persistido (EventStore + repos SQLite, transação atômica) ────────────────────────┘
```

- **SocPipeline.run_event** — pipeline de engines completa (parse→normalize→enrich→correlate→detect→alert).
- **SocPipeline.run_demo** — fluxo E2E garantido (4 alertas brute-force → 1 incidente → 1 caso).
- **SocService** — Incident Management (severidade/status/atribuição/SLA), Case Management
  (comentários, evidências, anexos, tarefas, resolução/encerramento), Investigation
  (pivôs alertas/IOCs/contexto via EventStore) e KPIs (`metrics`).

## 3. Cobertura de funcionalidade das prioridades

| Prioridade | Status |
|---|---|
| Pipeline Evento→Regra→Alerta→Incidente→Caso | ✅ `SocPipeline` + persistência |
| Incident Management (criação automática, severidade, status, atribuição, SLA) | ✅ `transition_incident`, `assign_incident_analyst`, `sla_of` |
| Case Management (evidências, timeline, comentários, anexos, encerramento) | ✅ `add_case_evidence/comment/attachment`, `close_case`/`resolve_case` |
| Investigation (pivôs, IOC, contexto enriquecido) | ✅ `investigate` (alertas/IOCs/assets/users/MITRE/pipeline_trail) |
| Dashboard (KPIs reais) | ✅ `/soc/metrics` (alerts/incidents/cases por status/severidade, MTTR, avg risk) |
| Arquitetura (baixo acoplamento, componentes reutilizáveis, docs atualizadas) | ✅ (engines intocados; persistência própria) |

## 4. Testes e Cobertura (Python)

| Check | Resultado |
|---|---|
| `pytest` (default) | ✅ passou (771 testes) |
| Cobertura | **95.04%** (fail-under 95) |
| `mypy` (strict) | ✅ 0 erros (145 arquivos) |
| `ruff check src tests` | ✅ All checks passed |
| `ruff format --check` | ✅ 213 arquivos formatados |

## 5. Testes adicionados (16)

- `tests/test_soc_pipeline.py` (8): fluxo demo persistido; case management + encerramento;
  incident assign/metrics/investigate; persistência de gestão confirmada; `run_event` exige
  container; transição inválida; attachment/task/resolve; SLA (overdue/met/warning); queries.
- `tests/test_soc_api.py` (4): fluxo completo; 404; `run_event` (200/422); detalhes/transition/400.

Suíte completa: **771 testes**.

## 6. Screenshots
⚠️ **Pendente** — requer abrir o app no navegador (regra 9 do squad). Expor:
- Dashboard Overview com KPIs reais: `uvicorn edysiem.api.app:create_app --factory` + `GET /api/v1/soc/metrics`
- Swagger `GET /docs` lista `/api/v1/soc/*`.

## 7. Pendências

1. Screenshots das telas (browser) — aguardando abertura do app.
2. Frontend ainda não consome `/soc/*` (Dashboard/War Room usam demo/fallback) — Sprint 2.16.
3. `cases.endpoints` retornam dicionários (sem Pydantic strict de resposta) — contratos podem ser formalizados em sprint futura.
4. Query de listagem não paginada em alguns casos (limite alto por request) — otimizar com índices para volume grande.

## 8. Próxima sprint recomendada

**Sprint 2.16 — Frontend operacional**: consumir `/api/v1/soc/*` no Dashboard/War Room/Alert
Center (dados reais E2E), telas de Investigation e Incident UI + Rules UI.

---

> Relatório gerado pelo TITAN AI SQUAD (jr + ATLAS + VULCAN + PROOF).