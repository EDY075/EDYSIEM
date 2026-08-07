# EDY SIEM — UI Guide

> Guia de interface e experiência. Define as telas, seus fluxos e como cada perfil
> de usuário interage com o produto. Base: design system + component library.

## 1. Princípios de UX

Toda tela responde: **O quê aconteceu? Onde? Qual o risco? Quem? Qual ação?**

- Poucos cliques para a informação essencial.
- Contexto sem perder contexto (drawer, não navegação destrutiva).
- Autoexplicativa: labels claros, tooltips, estados úteis.

## 2. Telas planejadas

| Rota | Tela | Perfil primário | Propósito |
|---|---|---|---|
| `/overview` | Overview SOC | Todos | O que aconteceu agora (KPIs, críticos, timeline) |
| `/events` | Events | SOC N2/N3, Hunter | Buscar e inspecionar eventos |
| `/alerts` | Alerts | SOC N1/N2 | Triagem e ciclo de vida |
| `/incidents` | Incidents | N2/N3, IR | Gestão de incidentes |
| `/rules` | Rules | Detection engineer | Detection/Correlation rules |
| `/intelligence` | Intelligence | N2/N3, Hunter | IOCs e threat intel |
| `/assets` | Assets | N1/N2 | Inventário e contexto de ativos |
| `/hunting` | Hunting | Hunter | Busca proativa (MITRE) |
| `/settings` | Settings | Admin | Preferências e sistema |

## 3. Fluxos principais

### 3.1 Triagem de alertas (N1)
Alerts → filtra por severidade/status → seleciona alerta → drawer (detalhe, evidências,
timeline) → ACK / Resolve / Escalar para incidente.

### 3.2 Investigação (N2)
Alerts/Events → abre drawer → segue entidade (host/user/IP) → timeline de entidade →
relaciona eventos → anota → cria incidente → exporta relatório.

### 3.3 Gestão de incidente (N2/N3/IR)
Incidents → abre incidente → timeline de ações → notas → status (open→investigating→
resolved/false_positive) → auditoria.

### 3.4 Criação de regra (Detection engineer)
Rules → Nova regra → form (severidade, MITRE, condição) → **teste rápido** com dados de
exemplo → salvar (enabled) → revisar em Alerts.

### 3.5 Hunting (Hunter)
Hunting → escolhe técnica MITRE → query pré-definida → timeline de resultados →
promove evidência a alerta/incidente.

## 4. Padrões por tela

- **Overview**: StatCards (críticos/altos/médios/totais) + gráfico de tendência +
  timeline recente + estado dos componentes.
- **Events**: busca (query language) + tabela densa + filtros rápidos + drawer de evento.
- **Alerts**: filtros (severidade/status/fonte/periodo) + tabela + ações em lote + drawer.
- **Incidents**: lista por status + drawer/workspace com timeline + notas + ações.
- **Rules**: tabela + form + teste de regra.
- **Intelligence**: IOCs por tipo + import + busca + correlação com eventos.
- **Assets**: inventário + contexto por ativo.

## 5. Responsividade

- Desktop (≥1280): layout completo, tabelas densas.
- Tablet (768–1279): sidebar recolhida, tabelas com scroll horizontal.
- Mobile (<768): navegação via drawer; tabelas viram cards; ações via menu.

## 6. Acessibilidade

- Contraste AA; foco visível; aria-labels; navegação por teclado (Tabs, Enter, ESC).
- Command Palette (Ctrl+K) para acesso rápido.

## 7. Definição de Pronto (UI)

- [ ] Fluxo definido neste guia
- [ ] Componentes da biblioteca (sem CSS avulso)
- [ ] Estados: loading/vazio/erro/feedback
- [ ] Responsivo testado (320–1920)
- [ ] Acessibilidade revisada
