# ENTERPRISE_UX_BENCHMARK — EDY SIEM

> Benchmark profundo de UX dos principais SIEMs para direcionar o Design System e a
> experiência do analista SOC. **Sem código** — documento de decisão (input para UI 3.1/3.2).

**Data:** 04/08/2026
**Produtos analisados:** Splunk Enterprise Security, Microsoft Sentinel, Elastic Security,
CrowdStrike Falcon, Wazuh Dashboard, IBM QRadar
**Fonte:** Pesquisa NOVA (TITAN AI SQUAD) — `SIEM_UIUX_COMPARATIVE_BENCHMARK.md`

---

## 1. Tendência dominante (2024–2026)

Convergência para **workspace unificado**:
1. Tema escuro default
2. Navegação lateral por módulos
3. Visão **master-detail** (lista + painel de detalhes)
4. Investigação entidade-cêntrica com timeline
5. MITRE ATT&CK transversal (badges, matriz, filtros)
6. Case/incident management com ciclo de vida
7. Query bar com autocomplete em todas as telas

---

## 2. Análise por dimensão

### 2.1 Layout
| Produto | Padrão |
|---|---|
| Splunk ES | Densidade alta, fluido (100% viewport), 1440px+, master-detail (ES 7) |
| Sentinel | Layout Azure Portal, telas densas, painéis empilhados |
| Elastic | **Best-in-class**: EUI consistente, dark default, grid flexível, flyouts padronizados |
| Falcon | Console limpo, densidade média, foco em ação rápida |
| Wazuh | OpenSearch Dashboards, densidade alta |
| QRadar | Top tabs (clássico), cramming sem hierarquia |

**Decisão EDY:** Shell de 3 zonas (sidebar colapsável + topbar + conteúdo master-detail), densidade compacta default com opção comfortable, viewport mínimo 1440px, grids fluidos.

### 2.2 Navegação
- **Padrão consolidado:** sidebar esquerda por módulos (exceção QRadar).
- **IA por workflow** (Falcon/Sentinel) e não por capacidade técnica:
  `Overview → Triage → Investigate → Respond → Manage`.
- Menu nunca deve exceder ~20 itens visíveis sem agrupamento.
- **Best-in-class:** Falcon (ícone+label, colapsável, busca global, zero atrito).

**Decisão EDY:** IA por workflow: Overview/Posture → Triage (home do analista) → Investigate → Respond → Manage.

### 2.3 Sidebar
- Estrutura hierárquica com ícones, colapsável (56px collapsed / 240px expanded).
- Seções reordenáveis/ocultáveis (Elastic) + busca de itens (raridade).
- **Anti-pattern:** menu infinito (>15 itens) sem busca/grupos/collapse (Wazuh/Sentinel).

**Decisão EDY:** Sidebar colapsável com seções por workflow, ícone+label, busca de itens, breadcrumbs em páginas profundas.

### 2.4 Topbar
- App selector, **global search**, **time picker global** (presets + custom), tenant, user menu.
- **Best-in-class:** Elastic (KQL em toda página + Add Filter + saved queries + time picker).
- Contador de alertas/incidents no topbar é desejável.

**Decisão EDY:** Topbar 56–64px com global search, time picker sincronizado, contador de alertas, user menu.

### 2.5 Dashboards
- **Security Posture** (KPIs executivos) + dashboards por domínio com drill-down.
- Time-range selector em todos os painéis.
- KPI tiles: número + sparkline + drill; métricas MTTR/MTTD sempre visíveis.
- **Inspect** (ver a query real por trás de cada painel) — essencial para confiança.

**Decisão EDY:** Dashboards com KPI tiles + sparklines + drill, gráficos de tendência (linha/área), donut (distribuição), heatmap/swim-lane (host×tempo), inspect em cada painel.

### 2.6 Alert Center
- **Best-in-class:** Splunk ES Analyst Queue — painel lateral direito consome o finding e dispara investigação/resposta sem sair da fila.
- Lista: badges de severidade, status (New/In Progress/Resolved), owner, tempo desde detecção.
- **Bulk actions** (mudar status/assign em lote).
- Filtros facetados + saved views personalizadas.

**Decisão EDY:** Alert center com master-detail (lista à esquerda, painel de detalhes à direita com abas Summary/Details/Activity), bulk actions, filtros facetados, saved views.

### 2.7 Investigation
- **Best-in-class:** Elastic Timeline — drag-and-drop de campos, process tree/gráfico, inline actions, persistência.
- Modelo híbrido (event-centric + entity-centric).
- **Anti-pattern:** investigação exclusivamente por grafo (troca de contexto). Ideal: tabela/timeline como fonte primária + grafo como visão complementar.
- **Inspect** (query real) em cada painel.

**Decisão EDY:** Investigação entidade-cêntrica com timeline de eventos por host/usuário + process tree/graph complementar + painel de evidências + inspect.

### 2.8 Incident / Case
- **Best-in-class:** Sentinel — lifecycle completo, tasks, activity log rich-text, classification reasons, playbooks, Teams.
- Lifecycle: New → In Progress → Closed (nomenclatura varia) + classification reasons.
- Case management nativo obrigatório (Wazuh falha sem ele).

**Decisão EDY:** Incident/case com lifecycle (OPEN → IN_PROGRESS → ON_HOLD → RESOLVED → CLOSED → REOPENED), tasks, activity log, classification, playbooks com visibilidade de execução.

### 2.9 Cores
- **Dark theme default** (salas SOC escuras); light opcional.
- **Paleta semântica de severidade única em todo o produto:**
  - Informational/Low = azul `#58A6FF`
  - Medium = âmbar `#D29922`
  - High = laranja `#DB6E28`
  - Critical = vermelho `#F85149`
- Accent de marca discreto (1 cor) — não competir com semântica.
- Contraste AA sobre fundos escuros.

**Tema dark EDY:**
- Fundo `#0F1218`, superfície `#161B22`, borda `#262D38`
- Texto primário `#E6EDF3`, secundário `#9DA7B3`

### 2.10 Tipografia
- UI: **Inter** — 13–14px dados, 16px títulos de página, 12px labels/badges.
- Dados técnicos/queries/logs: **JetBrains Mono / Roboto Mono** 12–13px.
- Tabelas numéricas: `tabular-nums` para alinhamento.

**Decisão EDY:** Inter (UI) + JetBrains Mono (dados técnicos) tokenizados.

### 2.11 Espaçamento
- **Best-in-class:** Elastic/Falcon — escala 4/8px consistente, densidade confortável sem perder volume.
- Compact default: linhas 24–28px; comfortable: 36–40px.
- Base 4px; gutters 16–24px.

**Decisão EDY:** Escala 4px tokenizada (space-1..space-10), densidade compacta default com toggle comfortable.

### 2.12 Métricas
- KPIs com sparklines clicáveis (Falcon/Elastic), orientados a ação.
- RBA/score de risco explicável (Splunk RBA, QRadar magnitude) — vence badge vermelho sem contexto.

**Decisão EDY:** KPI tiles com sparkline + drill; risk_score explicável (já no backend).

### 2.13 Gráficos
- Linha/área (tendência), donut (distribuição), heatmap/swim-lane (host×tempo), bar (comparação), treemap (top contributors).
- Todos com inspect.

### 2.14 Tabelas
- **Best-in-class:** Elastic — virtualização, colunas arrastáveis, expandable rows, toggle de coluna.
- Server-side pagination (nunca renderizar 100k linhas).
- Mono font em dados técnicos.

### 2.15 Filtros
- **Best-in-class:** Elastic (KQL com autocomplete + pinned filters + saved queries).
- **Anti-pattern:** query language como única porta (SPL) — oferecer filtros facetados + busca assistida para L1.

**Decisão EDY:** Query bar com autocomplete + syntax highlighting + modo assistido (construtor visual de filtros para L1).

### 2.16 Experiência do analista SOC
- Atalhos de teclado first-class: `/` busca, `g d` dashboard, `g a` alertas, `n` novo incidente, `j/k` navegar lista, `Shift+?` paleta de comandos.
- Navegação 100% por teclado em tabelas (baseline Elastic).
- Onboarding guiado, templates de filtros, glossário inline.

---

## 3. Anti-patterns a evitar (EDY)

1. Investigação só por grafo (usar híbrido)
2. Query language como única porta de entrada
3. Sem case management nativo
4. Light theme default
5. Densidade excessiva sem hierarquia
6. Menu lateral infinito (>15 itens)
7. Flyout overload sem breadcrumbs
8. Severidade sem contexto (MITRE/host/user/score)
9. Esconder a query (falta de inspect)
10. Ações de resposta enterradas (>5 cliques)
11. Ignorar acessibilidade
12. Terminologia proprietária sem glossário
13. Tabelas sem virtualização
14. Time picker inconsistente entre telas

---

## 4. Decisões consolidadas para o EDY SIEM

| Dimensão | Decisão |
|---|---|
| Tema | Dark default, light opcional |
| Severidade | Low=azul, Medium=âmbar, High=laranja, Critical=vermelho (única paleta) |
| Layout | 3 zonas: sidebar colapsável + topbar + master-detail |
| IA | Overview → Triage → Investigate → Respond → Manage |
| Alert center | Master-detail com abas Summary/Details/Activity + bulk actions |
| Investigation | Entidade-cêntrica: timeline + graph complementar + evidências + inspect |
| Incident/Case | Lifecycle completo + tasks + activity log + classification + playbooks |
| Tipografia | Inter (UI) + JetBrains Mono (dados) |
| Espaçamento | Escala 4px, compact default + comfortable |
| Tabelas | Virtualização + colunas configuráveis + server-side pagination |
| Filtros | Query bar com autocomplete + modo assistido + saved queries |
| Acessibilidade | Teclado first-class + contraste AA + glossário inline |

---

*Referência: Pesquisa NOVA — SIEM_UIUX_COMPARATIVE_BENCHMARK.md (04/08/2026)*
