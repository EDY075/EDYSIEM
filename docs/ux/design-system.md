# EDY SIEM — Design System

> Sistema de design completo, criado do zero (não reutiliza EDY Shield).
> Base para toda interface. Nenhuma tela existe sem tokens/componentes.
> Referência de UX: clareza, leitura rápida, poucos cliques, hierarquia forte, dark SOC.

---

## 1. Design Tokens

### 1.1 Grid

- Layout: 12 colunas (desktop), 8 (tablet), 4 (mobile).
- Container máx: 1600px (telas SOC densas), com margens laterais 24px.
- Gutter: 16px (mobile 8px).
- Breakpoints: `sm 640 / md 768 / lg 1024 / xl 1280 / 2xl 1536`.

```css
:root {
  --grid-cols: 12;
  --container-max: 1600px;
  --gutter: 16px;
  --bp-sm: 640px; --bp-md: 768px; --bp-lg: 1024px; --bp-xl: 1280px; --bp-2xl: 1536px;
}
```

### 1.2 Espaçamentos

Escala 4px (sistema consistente, sem valores avulsos):

```css
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-5: 24px;
--space-6: 32px;
--space-8: 48px;
--space-10: 64px;
```

Regras:
- Gap entre elementos irmãos: `--space-2` (8) a `--space-4` (16).
- Padding de cards: `--space-4` (16) padrão; denso `--space-3` (12).
- Seções: `--space-5` (24); blocos grandes `--space-6` (32).
- Tabelas SOC: padding de célula 8px/10px (densidade média-alta).

### 1.3 Tipografia

| Token | Família | Peso | Uso |
|---|---|---|---|
| `--font-ui` | Inter, system-ui | 400/500/600/700 | UI geral |
| `--font-mono` | JetBrains Mono, monospace | 400/600 | IDs, hashes, IPs, timestamps, logs |

Escala (rem):
```css
--text-xs: 12px;    /* metadados, badges */
--text-sm: 13px;    /* corpo denso, tabelas */
--text-base: 14px;  /* corpo padrão */
--text-lg: 16px;    /* títulos de card */
--text-xl: 20px;    /* subtítulos */
--text-2xl: 24px;   /* títulos de página */
--text-3xl: 30px;   /* valores KPI */
```

Altura de linha: corpo 1.5; títulos 1.2. Letter-spacing: títulos -0.01em; labels uppercase 0.06em.

### 1.4 Paleta (dark padrão)

```css
--bg-base: #0b0f17;          /* fundo app */
--bg-surface: #111827;       /* cards/painéis */
--bg-surface-2: #1a2233;     /* elevação 2, hover */
--bg-surface-3: #243044;     /* elevação 3 */
--bg-input: #0f1420;         /* campos */
--border: #243044;           /* bordas */
--border-strong: #334155;    /* bordas hover/focus */
--text-primary: #e5e7eb;
--text-secondary: #9aa5b1;
--text-muted: #6b7280;
--accent: #2f81f7;
--accent-hover: #3b93ff;
--accent-muted: rgba(47,129,247,0.14);
```

### 1.5 Severity colors

```css
--sev-critical: #f85149;   bg rgba(248,81,73,0.14)
--sev-high: #d29922;        bg rgba(210,153,34,0.14)
--sev-medium: #d4a72c;      bg rgba(212,167,44,0.12)
--sev-low: #58a6ff;         bg rgba(88,166,255,0.12)
--sev-info: #6b7280;        bg rgba(107,114,128,0.12)
```

Ordem de ranking: critical(5) > high(4) > medium(3) > low(2) > info(1).

### 1.6 Alert/status colors

```css
--alert-new: #58a6ff;          /* novo */
--alert-triage: #d29922;       /* em triagem */
--alert-investigating: #d4a72c;/* investigando */
--alert-resolved: #3fb950;     /* resolvido */
--alert-false-positive: #6b7280;
--success: #3fb950;
--warning: #d29922;
--danger: #f85149;
--info: #58a6ff;
```

### 1.7 Tema claro

Tokens espelhados (bg claro, texto escuro, mesmos accents/severity com contraste AA).
Toggle salvo no usuário.

---

## 2. Componentes

### 2.1 Botões

| Variante | Uso |
|---|---|
| `primary` | ação principal da tela (1 por view) |
| `secondary` | ação secundária |
| `ghost` | ação discreta (toolbar, linhas) |
| `danger` | ação destrutiva (ex.: excluir regra) |
| `icon` | apenas ícone (tooltip obrigatório) |

Spec: altura 34px; padding `0 16px`; radius 8px; font 13px/500.
Estados: default, hover (bg +1), active (translateY 0.5px), focus-visible (ring accent 2px),
disabled (opacity 0.4, cursor not-allowed), loading (spinner inline).

### 2.2 Inputs

- Texto, search, select, textarea, checkbox, radio, switch.
- Spec: altura 34px; bg `--bg-input`; border 1px `--border`; radius 8px; font 13px.
- Focus: border accent + ring 3px accent-muted.
- Placeholder: `--text-muted`. Erro: border danger + mensagem 12px. Ajuda: texto 12px muted.
- Search com ícone à esquerda; clear button.

### 2.3 Cards

- Estrutura: header (título 14px/600 + ações) + body + footer opcional.
- Padding 16px; radius 12px; border 1px `--border`; bg `--bg-surface`.
- Hover (interativos): border-strong + shadow sutil. Sem sombra pesada.

### 2.4 Badges

- Severity (com dot colorido) e Status (alerta).
- Spec: pill, altura 20px, padding `0 8px`, font 11px/600, dot 6px.
- Ex.: `badge critical` = dot vermelho + texto "CRITICAL" em bg sev-critical.

### 2.5 Tabela

- Header: bg surface-2, font 11px uppercase, padding 8px 12px.
- Linhas: padding 8px 12px; separador border; hover bg surface-2; seleção accent-muted.
- Densidade: altura de linha ~36px. Ordenação (indicador ↑↓), seleção múltipla,
  paginação no rodapé (linhas/página, contador, navegação).
- Células: mono para IDs/hashes/IPs/timestamps; truncamento com tooltip.

### 2.6 Timeline

- Uso: investigação, incidente, histórico.
- Estrutura: eixo vertical + dot (severity/status colorido) + conteúdo
  (título 13px/600, meta 12px muted, badge).
- Padding entre itens 12px; linha 2px `--border`.

### 2.7 Modal

- Uso: confirmação, formulário crítico (não para detalhe — drawer).
- Spec: largura 480px (padrão) / 640px (grande); radius 12px; overlay rgba(0,0,0,0.6);
  foco preso; ESC fecha; header (título + X), body, footer (cancel/confirm).

### 2.8 Drawer

- Uso: detalhe/investigação sem perder contexto (ex.: alerta).
- Spec: lateral direita, largura 480px (máx 90vw mobile), altura total, overlay sutil;
  header fixo + body scroll + footer de ações fixo; abas internas se necessário.

### 2.9 Command Palette

- Uso: navegação rápida e ações (Ctrl+K).
- Spec: overlay; campo central 600px; lista de comandos (ícone + label + atalho);
  setas navegam, Enter executa; ESC fecha; filtro instantâneo.

### 2.10 Loading

- **Skeleton** (padrão): shimmer suave 1.2s; formas espelhando layout real
  (card, linha de tabela, barra de chart).
- **Spinner** (inline/ações): 18px, animação 700ms.
- **Overlay de página**: skeleton, nunca spinner gigante.

### 2.11 Toast

- Uso: feedback de ação (sucesso, erro, aviso, info).
- Spec: bottom-right; largura 360px; radius 10px; border-left 4px colorido;
  auto-dismiss 4s (erro 6s); botão fechar; stack com gap 8px.
- Icon + título 13px/600 + mensagem 12px.

### 2.12 Context Menu

- Uso: ações em linha (tabela, timeline).
- Spec: menu flutuante 240px; item altura 32px; padding `0 12px`; icon 16px + label 13px;
  hover bg surface-2; separadores; fecha com ESC/fora; submenu opcional.
- Atalho visível à direita quando existir.

---

## 3. Padrões de UX

- **Hierarquia:** página (título 24px) → seção (card 16px) → item (14px).
- **Foco:** anel accent 2px em todo interativo.
- **Feedback:** toda ação → toast ou estado visível.
- **Estados vazios:** ícone + título + descrição + ação sugerida.
- **Tooltip:** em ícones, truncamentos e siglas; delay 300ms.
- **Acessibilidade:** contraste AA (WCAG), aria-labels, foco visível, navegação por teclado.
- **Responsivo:** 320 → 1920; tabelas viram cards/scroll horizontal em mobile.

## 4. Como usar

1. Tokens em `app/ui/src/styles/tokens.css` (CSS custom properties).
2. Componentes em `app/ui/src/components/` (um por arquivo, tipado).
3. Nenhum valor avulso (cor, fonte, espaço) fora dos tokens.

## 5. DoR (Definition of Ready para UI)

- [ ] Fluxo definido (S0.4)
- [ ] Token/componente existe no design system
- [ ] Estados (hover/focus/disabled/loading/vazio/erro) especificados
- [ ] Acessibilidade e responsividade consideradas
