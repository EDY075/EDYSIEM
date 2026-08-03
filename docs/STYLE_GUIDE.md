# EDY SIEM — Style Guide / Design System

> Identidade visual e sistema de design. **Fundação de UX — nada de UI sem tokens.**
> Tema escuro profissional (padrão SOC), com suporte a tema claro.

## 1. Identidade

- **Tom:** sério, profissional, operacional. Nada de visual de faculdade.
- **Proposta:** clareza, leitura rápida, poucos cliques, hierarquia forte.

## 2. Paleta (tokens)

### Dark (padrão)
| Token | Valor | Uso |
|---|---|---|
| `--bg-base` | `#0b0f17` | fundo da aplicação |
| `--bg-surface` | `#111827` | cards/painéis |
| `--bg-surface-2` | `#1a2233` | elevação 2 |
| `--border` | `#243044` | bordas |
| `--text-primary` | `#e5e7eb` | texto principal |
| `--text-secondary` | `#9aa5b1` | texto secundário |
| `--text-muted` | `#6b7280` | texto desabilitado |
| `--accent` | `#2f81f7` | azul primário |
| `--accent-hover` | `#3b93ff` | hover |
| `--success` | `#3fb950` | ok/saudável |
| `--warning` | `#d29922` | atenção |
| `--danger` | `#f85149` | crítico |
| `--info` | `#58a6ff` | informativo |

Severidade: `critical=--danger`, `high=--warning`, `medium=#d4a72c`, `low=--info`, `info=--text-muted`.

## 3. Tipografia

- Família: **Inter** (títulos/UI) + **JetBrains Mono** (dados técnicos: IDs, hashes, IPs, timestamps).
- Escala: 12 / 13 / 14 / 16 / 20 / 24 / 30 px.
- Peso: 400 (body), 500 (ênfase), 600 (títulos), 700 (destaque numérico).
- Altura de linha: 1.5 corpo; 1.2 títulos.

## 4. Espaçamento

- Escala 4px: 4 / 8 / 12 / 16 / 24 / 32 / 48.
- Densidade média-alta (tabelas SOC): padding de linha 8px; cabeçalho 10px.
- Gaps consistentes: 8 (agrupamentos), 16 (cards), 24 (seções).

## 5. Componentes base (planejados)

- Sidebar operacional (navegação + status do sistema).
- Topbar (pesquisa global, contexto, perfil).
- KPI Cards (severidade + mini-barra).
- Tabela de eventos/alertas (densa, ordenável, filtrável, paginada).
- Drawer de investigação (timeline, evidências, ações).
- Badges (severidade/status com dot), Buttons (ghost/primary), Tooltips, Toast.
- Estados: loading (skeleton), vazio (útil), erro (recuperável).

## 6. UX obrigatória

Toda tela responde: **o quê, onde, risco, quem, ação.**
- Tooltips em ícones e campos truncados.
- Estados vazios com orientação de próxima ação.
- Feedback visual em toda ação (toast/spinner/confirmação).
- Acessibilidade: contraste AA, foco visível, aria-labels.
- Responsivo: 320px → 1920px.

## 7. Arquivos

- Design tokens: `app/ui/src/styles/tokens.css` (quando UI iniciar).
- Referências visuais futuras: `docs/design/`.
