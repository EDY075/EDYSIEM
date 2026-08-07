# UI_GUIDELINES.md — Diretrizes de UX/UI

> Regras de experiência e interface para agentes que editarem o frontend.

## Regras de UX (produto)
- **Tudo tem propósito operacional** (Manifesto). Cada tela responde: *o quê, onde, risco, quem, ação*.
- **Sem dados fictícios.** Quando a API não responder, mostre estado explícito de indisponibilidade
  (skeleton/empty/retry) — nunca dados inventados.
- Ações que dependem de contrato ausente devem ser **desabilitadas/explicadas**, não simuladas.

## Regras de interface
- **Hierarquia visual** clara em cada tela; KPIs com labels semânticos e **sparklines com dados reais** (diferentes por card).
- **Tabelas:** cabeçalho *sticky*, alinhamento, EmptyCell discreto, densidade consistente, hover elegante, paginação uniforme.
- **Contraste:** texto secundário/muted elevado (acessível em dark e light).
- **Drawer/Alert Center:** Drawer 460px, header sticky; **Alert/Incident/Case**: relação Evento→Alerta→Incidente→Caso visível na investigation.
- **Responsividade:** revisar breakpoints; sem overflow horizontal em notebook (1280×720) nem empilhamento desnecessário.
- **Acessibilidade:** contraste adequado, `aria-label` onde necessário, foco visível.

## Temas
- **Dark** é o padrão. Light disponível via toggle. Tokens em `colors.ts` garantem contraste nos 2 temas.

## Estados globais (unificados)
- Usar os componentes de feedback do Design System: `EmptyState`, `LoadingSkeleton`, toasts consistentes, botão de retry padronizado.

## Referências
- `docs/design/UI_GUIDE.md` · `docs/design/UX_ARCHITECTURE.md` · `docs/design/USER_JOURNEY.md`
  · `docs/ENTERPRISE_UX_BENCHMARK.md` (benchmark dos 6 SIEMs) · ver [DESIGN_SYSTEM.md](./DESIGN_SYSTEM.md)