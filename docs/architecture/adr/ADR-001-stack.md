# ADR-001 — Stack de Linguagem e Runtime

- **Status:** Aceito
- **Data:** 2026-08-03

## Contexto
O EDY SIEM precisa de uma base sustentável por anos: tipagem forte, ecossistema maduro,
bom suporte a concorrência e facilidade de contratação/estudo.

## Decisão
**Python 3.12+** como linguagem principal do backend, com **tipagem estrita (mypy strict)**.
Frontend em **TypeScript** (SPA própria), sem framework obrigatório na fundação
(decidir React/Svelte apenas quando a UX exigir, ver ADR-005).

## Consequências
- (+) Autodocumentação via tipos; curva de estudo alinhada ao público Blue Team.
- (+) Ecossistema rico para syslog, parsing, ML futuro.
- (-) Concorrência: exigirá asyncio/workers bem projetados (ver ADR-004).
- Manutenção em 1 ano: tipagem estrita evita regressões silenciosas.

## Critério "daqui a um ano"
Um desenvolvedor novo deve entender o fluxo lendo os tipos e a doc das camadas.
