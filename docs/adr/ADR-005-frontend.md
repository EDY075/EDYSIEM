# ADR-005 — Frontend

- **Status:** Proposto (decisão final na Sprint 0.4/0.5, após UX/Design System)
- **Data:** 2026-08-03

## Contexto
O frontend será totalmente redesenhado (não reaproveita EDY Shield). Precisa de UX Enterprise,
dark theme profissional, responsividade e acessibilidade. A escolha da stack afeta a
manutenção por anos.

## Decisão provisória
**SPA em TypeScript**, com **design tokens** e **componentes próprios** (design system próprio).
Framework JS será decidido na Sprint 0.5 com critérios objetivos:
manutenibilidade, ecossistema, performance de listas grandes (tabelas SOC), acessibilidade.

Candidatos avaliados na Sprint 0.5: Vanilla TS + Web Components, React, Svelte.
Decisão documentada em ADR-005 final.

## Consequências
- (+) Design tokens garantem consistência e tema dark/light.
- (+) Componentes próprios evitam dívida de UI framework pesado.
- (-) Mais esforço inicial que usar UI kit pronto; compensa em identidade e controle.
- Manutenção em 1 ano: sistema de design estável = mudanças de UI rápidas e consistentes.

## Critério "daqui a um ano"
Novas telas são montadas com componentes do design system, sem CSS avulso.
