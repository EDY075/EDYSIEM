# EDY SIEM — Frontend Guide

> Guia de desenvolvimento do frontend. UI nova (não reaproveita EDY Shield).
> A stack definitiva será decidida na Sprint 0.5 (ver ADR-005).

## 1. Princípios

- **Design tokens primeiro** — nada de cor/fonte avulsa.
- **Componentes do design system** — sem CSS espalhado por página.
- **Toda tela responde**: o quê, onde, risco, quem, ação.
- Dark theme profissional por padrão; tema claro como alternativa.

## 2. Arquitetura (provisória)

- SPA em TypeScript.
- Camadas: `pages` (telas) → `components` (design system) → `services` (API client) → `store` (estado).
- API client tipado (contratos do `API_GUIDE.md`).
- Estado mínimo e local; cache consciente; loading/erro explícitos.

## 3. Telas planejadas

| Rota | Tela | Propósito operacional |
|---|---|---|
| `/overview` | Overview SOC | O que aconteceu agora (KPIs, críticos, timeline) |
| `/events` | Events | Buscar e inspecionar eventos |
| `/alerts` | Alerts | Triagem e ciclo de vida |
| `/incidents` | Incidents | Gestão de incidentes |
| `/rules` | Rules | Detection/Correlation rules |
| `/intelligence` | Intelligence | IOCs e threat intel |
| `/assets` | Assets | Inventário |
| `/settings` | Settings | Preferências e sistema |

## 4. Experiência

- Tabelas densas, ordenáveis, filtráveis, paginadas.
- Drawer de investigação para contexto sem perder contexto.
- Skeleton loading, estados vazios úteis, tooltips, feedback visual.
- Acessibilidade: contraste AA, foco visível, aria-labels.

## 5. Padrões de código

- TypeScript estrito; componentes tipados.
- Design tokens em `tokens.css` (ver `STYLE_GUIDE.md`).
- Testes de componentes para comportamento crítico.
- `node --check`/tsc no gate.
