# EDY SIEM — Decisões (Índice de ADRs)

> Registro de decisões de arquitetura. Formato: ADR (Architecture Decision Record).
> Critério transversal: **como esta decisão afeta manutenção, escalabilidade e UX
> daqui a um ano?** Toda decisão nova deve responder isso explicitamente.

## ADRs registrados

| ADR | Título | Status | Resumo |
|---|---|---|---|
| 001 | Stack de Linguagem e Runtime | ✅ Aceito | Python 3.12+ backend, TypeScript frontend |
| 002 | Persistência | ✅ Aceito | SQLite stdlib isolado atrás de Protocol; motor trocável |
| 003 | Pipeline e Concorrência | ✅ Aceito | Pipeline linear asyncio com backpressure; etapas puras |
| 004 | Regras Declarativas | ✅ Aceito | Detection/Correlation rules em YAML, validadas por schema |
| 005 | Frontend | 🔄 Proposto | SPA TypeScript + design tokens; framework decidido na S0.5 |
| 006 | Observabilidade e Logs | ✅ Aceito | Log estruturado JSON + trace_id + health por componente |
| 007 | Plugin System e DI | ✅ Aceito | Registries por tipo + contêiner DI leve; plugins isolados |
| 008 | Pipeline Oficial de Eventos | ✅ Aceito | RawEvent → ParsedEvent → CanonicalEvent → EnrichedEvent; estágios puros e imutáveis |
| 009 | Infraestrutura de Ingestão Enterprise | ✅ Aceito | Pacote `ingestion` desacoplado: CollectorPlugin, RawEventQueue, backpressure, retry, dead letter, rate limit, health, metrics |

## Regras para novos ADRs

1. Toda decisão arquitetural relevante deve virar ADR.
2. Formato obrigatório: Status, Data, Contexto, Decisão, Consequências, Critério "daqui a um ano".
3. ADR rejeitado/superado deve ser marcado `Substituído por ADR-NNN`, nunca apagado.
4. Decisão sem ADR não existe oficialmente.
