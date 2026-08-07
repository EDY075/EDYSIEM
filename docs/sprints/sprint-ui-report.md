# EDY SIEM — Relatório do Sprint UI 3.0/3.1/3.2

**Data:** 04/08/2026
**Produto:** EDY SIEM — Security Information and Event Management
**Escopo:** Benchmark UX de 6 SIEMs + Design System definitivo + Estrutura React (shell)

---

## 1. UI 3.0 — Enterprise UX Benchmark

### Documento: `docs/ux/enterprise-ux-benchmark.md`

Benchmark profundo de UX dos principais SIEMs: **Splunk Enterprise Security, Microsoft Sentinel,
Elastic Security, CrowdStrike Falcon, Wazuh Dashboard, IBM QRadar**.

### Dimensões analisadas
layout, navegação, sidebar, topbar, dashboards, alert center, investigation, incident/case,
cores, tipografia, espaçamento, métricas, gráficos, tabelas, filtros, experiência do analista SOC.

### Principais decisões (síntese)
| Dimensão | Decisão EDY |
|---|---|
| Tema | **Dark default** (fundo `#0F1218`), light opcional |
| Severidade | Low=azul `#58A6FF`, Medium=âmbar `#D29922`, High=laranja `#DB6E28`, Critical=vermelho `#F85149` |
| Layout | 3 zonas: sidebar colapsável + topbar + **master-detail** |
| IA | Overview → Triage → Investigate → Respond → Manage |
| Alert center | Master-detail com abas Summary/Details/Activity + bulk actions |
| Investigation | Entidade-cêntrica: timeline + graph complementar + evidências + inspect |
| Tipografia | Inter (UI) + JetBrains Mono (dados) |
| Filtros | Query bar com autocomplete + modo assistido |

### Anti-patterns documentados
grafo-only, query como única porta, sem case management, light default, menu infinito,
flyout overload, severidade sem contexto, esconder query, tabelas sem virtualização.

---

## 2. UI 3.1 — Design System Definitivo

### `frontend/src/design-system/`

**Tokens** (inspirado em Sentinel + CrowdStrike + Splunk):
- `tokens/colors.ts` — cores dark + paleta semântica de severidade única
- `tokens/index.ts` — typography (Inter + JetBrains Mono), spacing (escala 4px), density, radii, shadows, zIndex
- `tokens/motion.ts` — animações (instant/fast/normal/slow)
- `tokens/tokensCss.ts` — CSS variables bridge

**Componentes base:**
- `Button` (variantes: primary/secondary/ghost/danger)
- `Badge` (severidade semântica)
- `Card`, `Input`, `Table` (densidade compacta default + comfortable)

Tudo **novo** — não reutiliza componentes do EDY Shield.

---

## 3. UI 3.2 — Estrutura React (sem lógica)

### `frontend/`
- `shell/AppShell.tsx` — shell de 3 zonas + `<Outlet/>` + responsividade
- `shell/Sidebar.tsx` — navegação por workflow, colapsável (56/240px)
- `shell/Topbar.tsx` — global search, time range, contador de alertas, theme toggle
- `theme/ThemeProvider.tsx` — dark default + toggle
- `state/AppState.tsx` — estado global (density, currentUser)
- `routing/routes.tsx` — 10 rotas (Overview, Triage, Alertas, Incidentes, Investigar, Cases, Playbooks, Regras, Intel, Config)
- `App.tsx`, `main.tsx`, `index.html`, `vite.config.ts`, `tsconfig.json`, `package.json`

### Validação
- `npx tsc -b` ✅ (TypeScript strict, 0 erros)
- `npm run build` ✅ (Vite production build OK)

---

## 4. Como Executar

```bash
cd frontend
npm install
npm run dev      # dev server (Vite, porta 5173)
npm run build    # production build
```

---

## 5. Próxima Sprint

**Dashboard v0 (2.14)**: conectar o Design System ao backend (KPIs, alert center, incidentes)
com dados reais via API v1.

---

> Relatório gerado pelo TITAN AI SQUAD (jr + NOVA + ORION + LUMINA + QA)
