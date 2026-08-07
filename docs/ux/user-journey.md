# EDY SIEM — User Journey

> Jornadas de usuário por perfil. Passo a passo com pontos de decisão, dores e
> objetivos. Cada jornada termina em uma tarefa mensurável.
> Complementa `UX_ARCHITECTURE.md`.

## J1 — Triagem de alerta (SOC N1)

**Objetivo:** decidir o que fazer com um alerta em < 60s.

| Passo | Tela/Ação | Decisão | Sucesso |
|---|---|---|---|
| 1 | `/alerts` (filtro padrão críticos+altos 24h) | — | lista carregada |
| 2 | Ver KPIs e badge de severidade | é real? | identificou risco |
| 3 | Clicar linha → drawer | qual o impacto? | entidades visíveis |
| 4 | Ler resumo + evidências | falso positivo? | classificou |
| 5 | ACK → Resolve, ou Escalar p/ incidente | ação | estado atualizado |

**Dor evitada:** analista não sabe por onde começar → filtro padrão já aponta críticos.
**Métrica:** tempo para decisão (target < 60s).

## J2 — Investigação (SOC N2)

**Objetivo:** transformar alerta em incidente com contexto e evidências.

| Passo | Ação | Decisão | Sucesso |
|---|---|---|---|
| 1 | Drawer de alerta → seguir host/user/IP | qual entidade? | entidade identificada |
| 2 | Timeline de entidade (eventos relacionados) | padrão malicioso? | contexto montado |
| 3 | Marcar evidências | o que comprova? | evidências selecionadas |
| 4 | Anotar investigação | — | nota registrada |
| 5 | Criar incidente + exportar relatório | escalar? | incidente documentado |

**Dor evitada:** perder contexto ao navegar → drawer + timeline de entidade.
**Métrica:** alerta → incidente documentado em minutos.

## J3 — Incident Response (N3/IR)

**Objetivo:** gerir ciclo de vida completo do incidente com auditoria.

| Passo | Ação | Decisão | Sucesso |
|---|---|---|---|
| 1 | `/incidents` → abrir incidente | — | workspace aberto |
| 2 | Rever timeline de ações | quem fez o quê? | trilha auditável |
| 3 | Adicionar notas | — | contexto atualizado |
| 4 | Mudar status (investigating/resolved/false_positive) | concluído? | estado correto |
| 5 | Exportar relatório (JSON/MD) | documentar? | relatório gerado |

**Dor evitada:** falta de trilha → timeline de ações com auditoria obrigatória.
**Métrica:** incidente com trilha completa e exportação.

## J4 — Detection Engineering

**Objetivo:** criar/ajustar regra com validação imediata.

| Passo | Ação | Decisão | Sucesso |
|---|---|---|---|
| 1 | `/rules` → Nova regra | — | form aberto |
| 2 | Preencher (severidade, MITRE, condição, timeframe) | condição correta? | schema válido |
| 3 | **Testar** com eventos de exemplo | gera alertas esperados? | feedback imediato |
| 4 | Salvar (enabled) | publicar? | regra ativa |
| 5 | Revisar em `/alerts` | ruído? | regra calibrada |

**Dor evitada:** regra quebrada em produção → teste rápido antes de salvar.
**Métrica:** regra criada e validada em minutos.

## J5 — Threat Hunting (Hunter)

**Objetivo:** busca proativa por técnica MITRE.

| Passo | Ação | Decisão | Sucesso |
|---|---|---|---|
| 1 | `/hunting` → escolher técnica MITRE | hipótese? | técnica escolhida |
| 2 | Executar query sugerida | achou padrão? | resultados |
| 3 | Analisar timeline de resultados | evidência real? | suspeita validada |
| 4 | Promover a incidente | escalar? | incidente criado |

**Dor evitada:** busca sem estrutura → queries pré-definidas por técnica MITRE.
**Métrica:** hipótese → incidente documentado.

## J6 — Contexto de Asset (N1/N2)

**Objetivo:** entender o que um host já causou.

| Passo | Ação | Decisão | Sucesso |
|---|---|---|---|
| 1 | `/assets` → abrir asset | — | drawer aberto |
| 2 | Ver alertas/eventos do asset | já comprometido? | histórico visível |
| 3 | Navegar para alerta/incidente | ação necessária? | contexto transferido |

**Dor evitada:** investigação sem histórico do host → drawer do asset com alertas/eventos.

## Regras de jornada

- Toda jornada termina em **estado mutável** (status, nota, incidente, exportação).
- Toda ação importante tem **feedback visível** (toast/estado).
- Nenhuma jornada exige treinamento prévio (autoexplicativa).
