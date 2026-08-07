# PROJECT_CONTEXT.md — Contexto e Estado do EDY SIEM

> O essencial para qualquer agente entender *o que* é o EDY SIEM e *onde* estamos.

## O que é

Plataforma **profissional de SIEM** (Security Information and Event Management),
produto *Enterprise*, open source, autônoma (sem nuvem obrigatória/licença cara),
didática e extensível. Foco em times de segurança pequenos ou em formação.

> Declaração de caráter oficial: **[PROJECT_MANIFESTO.md](../PROJECT_MANIFESTO.md)** (leia antes de qualquer feature).

## Stack em uma linha
- **Backend:** Python 3.12, **core 100% stdlib** (ADR-001), arquitetura limpa, DI manual, SQLite (ADR-002).
- **API:** FastAPI v1 (`/api/v1`), OpenAPI/Swagger em `/docs`.
- **Frontend:** React 18 + TypeScript + Vite + Recharts, Design System próprio ("Echelon").
- **Sonhos COC:** ingestão → normalização → enriquecimento → correlação → detecção → incidente → caso.

## Estado atual (fase do projeto)
- **Versão:** `0.2.0` · release candidate `0.2.0-rc.1`.
- **Concluído:** Sprints 2.1–2.17 + UI 3.x/4.x (Dashboard, War Room, Alert Center, Incidentes,
  Cases, Investigation, Regras/Intel/Assets, Detection Dashboard, shell, design system).
- **Próxima:** **Sprint 2.18** — Escala (Kafka, PostgreSQL por Protocol, auth/SSO).
- **Publicação Git:** commit + tag `release-0.2.0` locais; **push pendente** (sem remoto).
- **Qualidade:** pytest 95%+, mypy strict, ruff, tsc build verdes.

## O produto resolve (resumo do manifesto)
Prover clareza, contexto e ação para analistas de SOC; didática real para quem aprende;
engenharia demonstrável para quem quer mostrar mercado. Cada tela responde: o quê, onde,
risco, quem, ação.

## Para mais profundidade
- Visão/objetivos: [`docs/PRODUCT_VISION.md`](../docs/PRODUCT_VISION.md)
- Arquitetura: [`ARCHITECTURE.md`](./ARCHITECTURE.md)
- Roadmap oficial: [`docs/ROADMAP.md`](../docs/ROADMAP.md) e [`ROADMAP_AI.md`](./ROADMAP_AI.md)
- Fluxo/guia por área: [`docs/SYSTEM_DESIGN.md`](../docs/SYSTEM_DESIGN.md), [`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md)