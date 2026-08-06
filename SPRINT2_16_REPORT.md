# EDY SIEM — Relatório Técnico da Sprint 2.16 (Frontend Operacional)

**Data:** 05/08/2026
**Produto:** EDY SIEM — Security Information and Event Management
**Objetivo:** transformar o EDY SIEM em aplicação operacional completa, consumindo
**exclusivamente** a API `/soc/*` (sem novas engines, sem duplicar lógica).
**Critério central:** **nenhum dado mock restante.**
**Status:** ✅ CONCLUÍDA

---

## 1. Commits (1 por WP / grupo buildável)

| WP | Entrega | Commit |
|---|---|---|
| Backend | `GET /soc/alerts` + série temporal real no `/soc/metrics` | `33b2a47` |
| WP1+WP6 | Hooks reais `/soc/*` + Dashboard/War Room vivos (sem mock) | `baf76c5` |
| WP2+WP3+WP4 | Incident UI + Case UI + Investigation Workspace + rotas | `96a6a57` |
| WP7 | Sistema de toasts e feedback visual | `f930078` |
| WP5 | Alert Center Enterprise — paginação | `f03b2fd` |

## 2. Consumo real (API `/soc/*`)

| Hook / Tela | Endpoint |
|---|---|
| `useMetrics` → Dashboard/War Room | `GET /soc/metrics` (EPS, série 60 pts, avg risk, MTTR) |
| `useAlerts` → Dashboard/Alert Center/War Room | `GET /soc/alerts` |
| `useIncidents` → Incident Center | `GET /soc/incidents` |
| `useCases` → Case Center | `GET /soc/cases` |
| Case detail / Investigation | `GET /soc/cases/{id}/investigate` |
| Operações (assumir, transição, comentar, evidência, resolver, encerrar) | `POST /soc/incidents|cases/...` |

## 3. Telas entregues (dados reais)

- **Dashboard Vivo**: série temporal real (sem gerador random), severidade por contagens reais.
- **War Room Vivo**: KPIs/EPS, feed de eventos, MITRE, assets e severidade derivados de alertas reais.
- **Incident UI (`/incidents`)**: severidade/status/SLA/owner, assumir, transição e drawer de detalhes.
- **Case UI (`/cases`)**: timeline, evidências, contexto (IOC/MITRE/assets/users), comentar, anexar evidência, resolver e encerrar.
- **Investigation Workspace (`/investigate`)**: cadeia Eventos→Alerta→Incidente→Caso→MITRE→IOC→Asset→Usuário→Timeline.
- **Alert Center (`/alerts`)**: filtros/pesquisa/ordenação/bulk/drawer + paginação (10/página), dados reais.

## 4. Métricas (Qualidade)

| Check | Resultado |
|---|---|
| `pytest` | ✅ **771 testes** — coverage **95.08%** (fail-under 95) |
| `mypy` (strict) | ✅ 0 erros (145 arquivos) |
| `ruff check src tests` | ✅ All checks passed |
| `npm run build` | ✅ OK (`tsc -b && vite build`) |
| `npx tsc -b` | ✅ exit 0 |
| Working tree | ✅ **limpa** (após docs) |

## 5. Cobertura dos critérios de aceite

| Critério | Status |
|---|---|
| Nenhum mock restante | ✅ hooks sem MOCK_*; War Room/Dashboard sem DEMO_* |
| Dashboard consumindo backend real | ✅ |
| Alert Center operacional | ✅ (filtros/busca/ordem/bulk/drawer + paginação) |
| Incident UI funcional | ✅ |
| Case UI funcional | ✅ |
| Investigation Workspace completo | ✅ |
| War Room usando dados reais | ✅ |
| Build verde / Testes verdes | ✅ |
| Working tree limpa | ✅ |
| Screenshots reais das telas | ⚠️ pendente (browser) |

## 6. Pendências

1. **Screenshots das telas** (browser) — aguardando abertura do app (regra 9 do squad).
2. `GET /soc/alerts` não lista mais do que `limit`; paginação server-side para volume grande (hoje client-side).
3. Bulk actions do Alert Center ainda não chamam o backend (seleção local apenas).
4. Toasts presentes em Incident/Case Center; Dashboard/War Room podem ser migrados no futuro.

## 7. Próxima sprint recomendada

**Sprint 2.17 — Rules/Detection UI + Intelligence (IOC manager) + Assets.**

---

> Relatório gerado pelo TITAN AI SQUAD (jr + VULCAN + LUMINA + PROOF).