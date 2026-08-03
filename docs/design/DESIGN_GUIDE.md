# EDY SIEM — Design Guide

> Guia de aplicação do design. Como transformar tokens e componentes em telas
> consistentes. Base: `DESIGN_SYSTEM.md` (tokens) + `COMPONENT_LIBRARY.md` (catálogo).

## 1. Princípios visuais

- **Clareza acima de decoração** — informação densa e legível.
- **Hierarquia forte** — página → seção → item.
- **Densidade controlada** — tabelas SOC densas, mas com respiro.
- **Consistência total** — nada de estilos avulsos.
- **Feedback em tudo** — toda ação tem resposta visível.
- **Dark por padrão** — tema claro como opção.

## 2. Regras de composição

1. **Layout**: container máx 1600px; grid 12 colunas; gutter 16px.
2. **Superfícies**: fundo `--bg-base`; painéis `--bg-surface`; elevações `surface-2/3`.
3. **Bordas**: 1px `--border`; realce hover `--border-strong`.
4. **Raio**: 8px (controles), 12px (cards), pill (badges/avatar).
5. **Sombras**: discretas, apenas em sobreposição (modal/drawer/menu) — nunca em cards de leitura.

## 3. Hierarquia tipográfica por elemento

| Elemento | Fonte | Tamanho | Peso |
|---|---|---|---|
| Título de página | UI | 24px | 600 |
| Subtítulo | UI | 14px | 400 (muted) |
| Título de card | UI | 16px | 600 |
| Corpo | UI | 14px | 400 |
| Tabela (célula) | UI | 13px | 400 |
| Tabela (header) | UI | 11px | 600 uppercase |
| ID/hash/IP | Mono | 12px | 400 |
| Badge | UI | 11px | 600 |
| KPI valor | UI | 30px | 700 |

## 4. Cores por papel

- **Ações**: accent (`--accent`).
- **Severidade**: sev-* (crítico → info).
- **Status de alerta**: alert-* (novo → falso positivo).
- **Estado de sistema**: success/warning/danger/info.
- **Texto**: primary (título/conteúdo), secondary (corpo), muted (metadados).

## 5. Estados vazios úteis

Todo empty state segue: ícone (44px muted) → título (14px/600) → descrição (13px muted)
→ **ação sugerida** (botão ghost/primary). Nunca "sem dados" sem próxima ação.

## 6. Micro-interações

- Transições: 150ms ease (hover), 200ms (aparecimento), 250ms (drawer/modal).
- Skeleton shimmer: 1.2s.
- Nada de animação puramente decorativa (YAGNI visual).

## 7. Anti-padrões (nunca)

- Nenhum valor de cor/fonte/espaço hardcoded fora dos tokens.
- Nenhum modal para conteúdo que deveria ser drawer.
- Nenhuma tabela sem ordenação/filtro quando > 50 linhas.
- Nenhum ícone sem tooltip.
- Nenhum botão primário duplicado na mesma view.
