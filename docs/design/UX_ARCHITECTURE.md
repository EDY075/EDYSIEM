# EDY SIEM — UX Architecture

> Projeto completo da experiência do usuário. Objetivo: **qualquer analista usa sem treinamento.**
> Toda tela responde: O que aconteceu? O impacto? O que devo fazer agora? Onde clico?
> Base: `DESIGN_SYSTEM.md`, `COMPONENT_LIBRARY.md`, `UI_GUIDE.md`.

---

## 1. As quatro perguntas

Toda tela de trabalho deve responder na ordem:

| Pergunta | Onde é respondida |
|---|---|
| O que aconteceu? | Título + badge de severidade + resumo de 1 linha |
| O impacto? | Entidades afetadas (host, user, IP) + risco + MITRE |
| O que devo fazer agora? | Ações sugeridas visíveis (triar, investigar, responder) |
| Onde clico? | Próxima ação óbvia com botão primário único |

Se uma tela não responde a essas 4 perguntas, ela não está pronta.

---

## 2. Jornadas por perfil

### 2.1 Analista SOC N1 (triagem)
- Chega em `/alerts` (filtro padrão: críticos+altos, últimas 24h).
- Vê KPIs → filtra → clica alerta → drawer responde as 4 perguntas.
- Ações: ACK, Resolve, Escalar para incidente.
- **Sucesso:** decide em < 60s se é real, falso positivo ou precisa escalar.

### 2.2 Analista SOC N2 (investigação)
- Parte do alerta → drawer → segue entidade (host/user/IP) → timeline de entidade.
- Relaciona eventos, anota, cria incidente, exporta relatório.
- **Sucesso:** converte alerta em incidente com evidências e contexto em minutos.

### 2.3 Analista SOC N3 / Threat Hunter
- `/hunting` → escolhe técnica MITRE → query → timeline de resultados → promove a incidente.
- **Sucesso:** busca proativa com hipóteses e documentação.

### 2.4 Incident Responder
- `/incidents` → workspace do incidente → timeline de ações → notas → status.
- **Sucesso:** ciclo de vida completo com trilha de auditoria.

### 2.5 Detection Engineer
- `/rules` → nova regra → form com **teste rápido** → salvar → revisar em `/alerts`.
- **Sucesso:** criar/ajustar regra em minutos com feedback imediato.

---

## 3. Arquitetura da informação

```
EDY SIEM
├── Overview        (visão geral: o que está acontecendo agora)
├── Events          (busca e inspeção de eventos)
├── Alerts          (triagem)
├── Incidents       (gestão)
├── Rules           (detecção/correlação)
├── Intelligence    (IOCs)
├── Assets          (inventário)
├── Hunting         (busca proativa)
└── Settings        (preferências/sistema)
```

**Navegação:** sidebar sempre visível (desktop); 1º nível = seções acima.
**Contexto:** drawer lateral para detalhe (nunca perde a lista).
**Comando:** Command Palette (Ctrl+K) para saltar entre telas/ações.

---

## 4. Fluxos detalhados por tela

### 4.1 Overview
```
[KPIs: Críticos | Altos | Médios | Total | Incidentes abertos]
[Gráfico de tendência 24h]
[Timeline de eventos recentes]        [Estado dos componentes]
[Alertas críticos: lista resumida]    [Ações rápidas]
```
- **O que aconteceu:** KPIs e gráfico.
- **O impacto:** badges de severidade + contagem de incidentes abertos.
- **O que fazer:** clicar em card de severidade → vai para `/alerts` filtrado.
- **Onde clicar:** cada KPI é um atalho filtrado (drill-down).

### 4.2 Events
```
[Command search: query language] [Date picker] [Filtros rápidos]
[Tabela: hora | fonte | host | tipo | user | ip_src | severidade]
[Drawer do evento ao clicar]
```
- Busca com sugestões; erro de query explicado inline.
- Drawer: campos canônicos + raw + enriquecimento + "Ver alertas deste host".

### 4.3 Alerts
```
[KPIs por severidade]
[Filtros: severidade | status | fonte | período]  [Busca]
[Tabela: severidade | status | título | host | user | primeira | última]
[Ações em lote: ACK | Resolve | Suppress]
[Drawer de alerta: resumo | evidências | timeline | relacionado | ações]
```
- **Drawer responde as 4 perguntas no topo.**
- Botões: ACK (ghost), Resolver (ghost), Escalar p/ incidente (primary).
- Feedback: toast em toda ação; badge atualiza.

### 4.4 Incidents
```
[Filtros por status]
[Tabela: incidente | severidade | entidades | alertas | status | atualizado]
[Workspace (drawer grande): timeline de ações | notas | entidades | evidências]
[Ações: status (investigating/resolved/false_positive) | exportar]
```
- Timeline de ações com auditoria (quem/quando/o quê).
- Notas com autor/hora; export JSON/MD.

### 4.5 Rules
```
[Lista de regras: nome | severidade | MITRE | enabled | versão]
[Nova regra → form: nome, severidade, MITRE, condição, timeframe]
[Teste rápido: executa regra contra eventos de exemplo e mostra alertas]
```
- Edição com validação de schema; "testar" antes de salvar.
- Disable sem delete (soft).

### 4.6 Intelligence
```
[KPIs por tipo de IOC]
[Importar IOCs (paste/arquivo) | Busca]
[Tabela: tipo | valor | fonte | ameaça | criado]
[Correlação: "ver eventos com este IOC"]
```

### 4.7 Assets
```
[Tabela: hostname | ip | os | criticality | tags | last_seen]
[Drawer do asset: contexto + alertas + eventos relacionados]
```

### 4.8 Hunting
```
[Seleciona técnica MITRE → query sugerida → executa]
[Timeline de resultados | entidades destacadas]
[Ação: promover evidência a alerta/incidente]
```

---

## 5. Decisões de interação (regras)

1. **Drawer, não navegação** — detalhe de alerta/evento/asset abre no drawer.
2. **Um botão primário por view** — a próxima ação é óbvia.
3. **Drill-down por clique** — KPI e badge são clicáveis e filtram a lista.
4. **Filtros persistentes** — estado de filtro sobrevive à navegação interna.
5. **Ações destrutivas pedem confirmação** (modal), nunca toasts silenciosos.
6. **Toda ação tem feedback** — toast ou estado visível.
7. **Busca global** — Command Palette para saltar; busca por query no Events.
8. **ESC fecha sobreposições**; teclado para ações frequentes.

## 6. Estados e feedback

- **Loading:** skeleton espelhando layout real.
- **Vazio:** ícone + "o que isso significa" + próxima ação sugerida.
- **Erro:** mensagem clara + retry; nunca stack trace cru.
- **Sucesso:** toast com confirmação e (quando útil) link para o resultado.

## 7. Regras obrigatórias de UX

- [ ] Tela responde às 4 perguntas.
- [ ] Próxima ação é um botão primário único.
- [ ] Contexto preservado (drawer) em fluxos de investigação.
- [ ] Filtros e busca visíveis sem rolagem.
- [ ] Todo item de lista tem ação de contexto (menu).
- [ ] Acessibilidade AA, teclado, foco visível.
- [ ] Responsivo 320–1920.

## 8. DoR UX (Definition of Ready)

- [ ] Jornada do perfil mapeada neste documento.
- [ ] Wireframe/fluxo da tela definido.
- [ ] 4 perguntas respondidas explicitamente.
- [ ] Estados (loading/vazio/erro/sucesso) especificados.
- [ ] Componentes da biblioteca mapeados (sem UI nova não documentada).
