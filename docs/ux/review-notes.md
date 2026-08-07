# EDY SIEM — Problemas de UI/UX percebidos (auditoria inicial → polish)

> Aviso de transparência: este ambiente não tem visão de imagens. A lista foi levantada
> a partir do código/design system + telas reais, a confirmar no olhar das imagens
> (`screenshots/` antes · `screenshots_after/` depois).

## Aplicados (UI/UX Polish)
- [x] **Contraste de texto secundário** — `textMuted`/`textSecondary` elevados (tokens `colors.ts`).
- [x] **KPIs "decorativos"** — sparkline agora usa `label+value` (diferente por card).
- [x] **Tabelas** — cabeçalho sticky, hover por linha, EmptyCell discreto, `vertical-align`.
- [x] **Drawer** — largura 460px, header sticky, sombra/backdrop refinados.
- [x] **Detection Dashboard** — cards `Mini` com acento semântico por indicador (sem repetição visual).

## Pendentes (requerem interação/confirmação visual)
1. Drawer aberto / filtros ativos / abas (Simulator, IOC, Assets) / empty / skeleton / toast —
   não alcançáveis por URL; captura com automação de clique.
2. Responsivo 768 (tablet) — avaliar empilhamento após o polish.
3. Confirmação visual final do contraste nos PNGs (olhar humano).

## Próximo passo
Revisão das imagens + refinamentos pontuais da Sprint UI/UX Polish.