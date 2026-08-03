# EDY SIEM — Component Library

> Catálogo completo de componentes do design system.
> Toda tela usa apenas componentes desta biblioteca. Nada de UI avulsa.
> Specs detalhadas em `DESIGN_SYSTEM.md`; este documento é o índice de uso.

## Índice de componentes

### Navegação e estrutura
| Componente | Uso | Estado |
|---|---|---|
| `Sidebar` | Navegação principal + status do sistema | Planejado |
| `Topbar` | Contexto, pesquisa global, ações, perfil | Planejado |
| `Breadcrumb` | Localização na hierarquia | Planejado |
| `Tabs` | Alternar conteúdo no mesmo contexto (drawer) | Planejado |

### Ação
| Componente | Uso | Estado |
|---|---|---|
| `Button` | primary / secondary / ghost / danger / icon | Planejado |
| `IconButton` | ação só ícone (tooltip obrigatório) | Planejado |
| `Dropdown` | menu de seleção/ações acionado por clique | Planejado |
| `ContextMenu` | ações em linha (tabela/timeline) | Planejado |
| `SplitButton` | ação principal + menu de variantes | Planejado |

### Entrada
| Componente | Uso | Estado |
|---|---|---|
| `Input` | texto | Planejado |
| `Search` | busca com debounce + ícone + clear | Planejado |
| `Select` | seleção única | Planejado |
| `MultiSelect` | seleção múltipla com tags | Planejado |
| `DatePicker` | intervalo de datas (presets: 1h/24h/7d/30d) | Planejado |
| `Textarea` | notas/observações | Planejado |
| `Checkbox` | seleção múltipla (tabelas) | Planejado |
| `Radio` | escolha única | Planejado |
| `Switch` | liga/desliga (regras, features) | Planejado |

### Exibição
| Componente | Uso | Estado |
|---|---|---|
| `Card` | agrupamento de conteúdo | Planejado |
| `Badge` | severity/status com dot | Planejado |
| `Tag` | rótulos livres (tags de asset, categorias) | Planejado |
| `Table` | dados densos: header, ordenação, seleção, paginação | Planejado |
| `Timeline` | investigação, incidente, histórico | Planejado |
| `StatCard` | KPI com valor + mini-barra | Planejado |
| `Progress` | barra de progresso (tarefas, saúde) | Planejado |
| `Tooltip` | contexto em ícones/siglas/truncados | Planejado |
| `Avatar` | usuário/entidade | Planejado |

### Feedback e sobreposição
| Componente | Uso | Estado |
|---|---|---|
| `Modal` | confirmação/formulário crítico | Planejado |
| `Drawer` | detalhe/investigação sem perder contexto | Planejado |
| `CommandPalette` | navegação/ações via Ctrl+K | Planejado |
| `Toast` | feedback de ação (success/error/warning/info) | Planejado |
| `Skeleton` | loading (shimmer) | Planejado |
| `Spinner` | loading inline | Planejado |
| `EmptyState` | estado vazio útil (ação sugerida) | Planejado |
| `ErrorState` | erro recuperável (retry) | Planejado |
| `Status` | indicador de status (online/degraded/offline) | Planejado |

### Visualização de dados
| Componente | Uso | Estado |
|---|---|---|
| `Chart` | linha (tendência), barra (volume), donut (distribuição) | Planejado |
| `Heatmap` | densidade temporal | Planejado |
| `MiniBar` | barras em KPI cards | Planejado |

### Temas
| Componente | Uso | Estado |
|---|---|---|
| `DarkTheme` | tema padrão (tokens dark) | Planejado |
| `LightTheme` | tema claro (tokens espelhados) | Planejado |
| `Responsive` | breakpoints sm/md/lg/xl/2xl | Planejado |

## Contrato de componente

Cada componente segue:

```ts
interface ComponentProps {
  id?: string;
  className?: string;
  disabled?: boolean;
  ariaLabel?: string;
  dataTestId?: string;
}
```

- Tipado (TypeScript estrito).
- Acessível (role, aria, foco visível, teclado).
- Estados: default, hover, focus, disabled, loading (quando aplicável), erro (quando aplicável).
- Sem valor avulso: cores/espaços/fontes vêm dos tokens.

## Regras de uso

1. Tela nova = composição de componentes existentes (nunca CSS novo para o que já existe).
2. Falta componente? Crie na biblioteca + documente ANTES de usar.
3. Variação de visual: token/estado, nunca copiar componente.
4. Todo componente novo exige: spec no `DESIGN_SYSTEM.md` + exemplo no `STYLE_GUIDE.md`.
