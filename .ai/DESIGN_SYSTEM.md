# DESIGN_SYSTEM.md — Design System "Echelon"

> Sistema visual do EDY SIEM. Fonte canônica em `docs/design/`. Código real em
> `frontend/src/design-system/` (tokens + componentes).

## Princípio de marca (Echelon)
Clareza operacional sob pressão: legibilidade, hierarquia e confiança — **nunca**
estética teatral de segurança. Símbolo: "passo Echelon" (marca de **3 degraus**
contínuos = ler, classificar, decidir). Ver `docs/design/ECHELON_BRAND.md` (SVG do símbolo).

## Cores (tokens em `design-system/tokens/colors.ts`)

| Token | Dark | Light |
|---|---|---|
| background | `#0A0F17` | `#F5F8FC` |
| surface | `#111925` | `#FFFFFF` |
| brand/accent | `#3B9CFF` | `#176DCA` |
| critical | `#F15B68` | `#C43345` |
| high | `#F08A4B` | `#BE5A17` |
| medium/warning | `#E6B64A` | `#A76D00` |
| low/info | `#56B4FF` | `#176DCA` |
| online/success | `#42C981` | `#168453` |

> **Regra de marca:** azul é p/ navegação, foco e ações primárias — **nunca** é cor de severidade.

## Tipografia (tokens/index.ts)
- **Inter** = voz do produto (UI). **JetBrains Mono** = dados técnicos/investigação.
- Tamanhos: `xs 12` · `sm 13` · `base 14` · `lg 16` · `xl 18` · `2xl 22` · `3xl 28` · `display 30`.
- Pesos 400/500/600/700; line-height tight 1.25 / normal 1.5 / relaxed 1.7.

## Espaçamento / densidade / raio / elevação
- **Base 4px** em `spacing` (`1..10`).
- **Densidade:** `compact 28px` (default) · `comfortable 40px`.
- **Raio:** `sm 4`, `md 6`, `lg 8` (default), `xl 12`, `full 9999`.
- **Elevação/sombra:** tokens `--elevation-*` preservam contraste nos 2 temas.
- **z-index:** sidebar 100 · topbar 200 · flyout 300 · modal 400 · toast 500.

## Componentes (barrel `design-system/index.ts`)
- **Tokens:** `colors`, `typography`, `spacing`, `density`, `radii`, `elevation`, `shadows`, `motion`, `zIndex`, `tokensCss`.
- **Base:** `Button`, `BrandMark`, `Badge`, `Card`, `Input`, `Table`.
- **Badges:** `SeverityBadge`, `StatusBadge`.
- **Cards:** `KpiCard`, `MetricCard`.
- **Tabelas:** `DataTable`.
- **Feedback:** `EmptyState`, `LoadingSkeleton`, `Toolbar`.
- **Overlays:** `Drawer`, `Modal`.
- **Timeline/Activity:** `Timeline`, `ActivityFeed`.
- **Layout/shell:** `Breadcrumb`, `GlobalSearch`, `Sidebar`, `Topbar`, `AppShell`.

## Estados globais
- **EmptyState**, **LoadingSkeleton**, **Toast** (via `state/toast.tsx`), **retry** padronizados.

## Referências
- `docs/design/DESIGN_SYSTEM.md` · `docs/design/ECHELON_BRAND.md` · `docs/design/COMPONENT_LIBRARY.md`
- Código: `frontend/src/design-system/*` · tokens/CSS: `tokens/tokensCss.ts`