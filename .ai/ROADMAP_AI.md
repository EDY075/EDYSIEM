# ROADMAP_AI.md — Pendências e próximas etapas

> Contexto de planejamento para agentes. Alinhado a `docs/ROADMAP.md`.

## Próxima Sprint: **2.18 — Escala**
- [x] Fila externa plugável (**Kafka**) via contrato.
- [x] Storage alternativo (**PostgreSQL**) via Protocol.
- [x] Auth **OAuth/SSO** + RBAC refinado.
- [x] Correlação enriquecida e hunting UI (MITRE navigator-like).
- [x] multi-tenant, particionamento/retention (posterior, Fase 3).

> Nem todos os itens são "Sprint 2.18": priorize por valor + arquitetura. Confirmar escopo com o usuário.

## Pendências de release 0.2.0 (não bloqueantes)
- **Push no Git:** commit + tag `release-0.2.0` existem **localmente**; falta remoto e push.
- **Evolução de contratos:** Triage, Playbooks e detalhes enriquecidos de alerta aguardam endpoints próprios.
- **Empacotamento Python:** artefato de build gera em ambiente com `hatchling`/`build` (declarado, não gerado aqui).
- **Dependências:** 2 deprecia son de `starlette.testclient`/`httpx` a tratar em atualização planejada.

## Estado de sprints (condensado — do ROADMAP)
- **S1:** núcleo (core, persistence, pipeline, regras, incidentes, API, CLI, UI v0) ✅
- **S2 (2.1–2.17):** Operação SOC; pipeline persistida; Alert Center, incidentes, cases, investigação, catálogo de regras, simulador, IOC/Assets, Detection Dashboard ✅
- **UI 3.x/4.x:** design system, shell, layout enterprise, componentes, API client + hooks, Dashboard, War Room ✅
- **UI polish UX:** identidade Echelon aplicada (Sprint final) ✅
- **Fase 3 (escala/hunting)** — pendente.

## Como usar
- Antes de começar uma tarefa: escolha o item na **pendência de release** ou da **Sprint 2.18/Phase 3**.
- Toda decisão (feature/arquitetura) requer ADR → **[DECISIONS.md](./DECISIONS.md)**.
- Ao terminar uma sprint: atualizar este arquivo + `docs/ROADMAP.md` + memória (ver [AI_HANDOFF.md](./AI_HANDOFF.md)).