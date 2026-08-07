# EDY SIEM — Screen Map

> Mapa de telas: hierarquia, navegação e transições. Complementa `UX_ARCHITECTURE.md`.
> Objetivo: qualquer analista encontra qualquer tela em ≤ 2 cliques.

## 1. Mapa hierárquico

```
EDY SIEM (Shell: Sidebar + Topbar + Command Palette)
├── Overview ................. /overview
├── Events ................... /events
│   └── Drawer: Evento ........ (detalhe)
├── Alerts ................... /alerts
│   └── Drawer: Alerta ........ (triagem/investigação)
│       └── Drawer: Evento relacionado
├── Incidents ................ /incidents
│   └── Workspace: Incidente .. (timeline/notas/ações)
├── Rules .................... /rules
│   ├── Form: Nova/Editar regra
│   └── Modal: Teste de regra
├── Intelligence ............. /intelligence
│   └── Drawer: IOC
├── Assets ................... /assets
│   └── Drawer: Asset
├── Hunting .................. /hunting
│   └── Timeline de resultados
└── Settings ................. /settings
```

## 2. Transições

| De | Ação | Para | Tipo |
|---|---|---|---|
| Overview | clicar KPI/badge | Alerts (filtrado) | navegação c/ estado |
| Alerts | clicar linha | Drawer Alerta | drawer |
| Drawer Alerta | "ver eventos" | Drawer Evento | drawer sobre drawer |
| Drawer Alerta | "escalar" | Incidentes (novo) | navegação |
| Events | clicar linha | Drawer Evento | drawer |
| Intelligence | "ver eventos c/ IOC" | Events (filtrado) | navegação c/ estado |
| Assets | clicar linha | Drawer Asset | drawer |
| Hunting | "promover" | Incidentes (novo) | navegação |
| Rules | "testar" | Modal Teste | modal |
| Qualquer | Ctrl+K | Command Palette | sobreposição |

## 3. Regras de navegação

- Sidebar: seções de 1º nível sempre visíveis.
- Drawer: preserva a lista (voltar = fechar drawer, não recarregar).
- Filtros via drill-down chegam pré-aplicados (URL query/estado).
- Command Palette: atalho global (Ctrl+K), busca de tela/ação.
- Breadcrumb: `Seção / Item` no topbar para navegação explícita.

## 4. Rotas reservadas

| Rota | Conteúdo |
|---|---|
| `/overview` | Resumo operacional (padrão) |
| `/events` | Busca de eventos |
| `/alerts` | Triagem |
| `/incidents` | Gestão |
| `/rules` | Regras |
| `/intelligence` | IOCs |
| `/assets` | Inventário |
| `/hunting` | Busca proativa |
| `/settings` | Preferências |

## 5. Prioridade de implementação (UX)

1. `/alerts` (triagem) — núcleo operacional
2. `/overview` — visão geral
3. Drawer Alerta (investigação)
4. `/incidents`
5. `/events`
6. `/rules`
7. `/intelligence`, `/assets`, `/hunting`, `/settings`
