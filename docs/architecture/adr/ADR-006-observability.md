# ADR-006 — Observabilidade e Logs

- **Status:** Aceito
- **Data:** 2026-08-03

## Contexto
Um SIEM precisa ser observável: saber o que aconteceu em cada etapa do pipeline, com
rastreabilidade (trace_id) e sem depender de debug manual.

## Decisão
**Log estruturado JSON** (stdlib `logging` com formatter JSON próprio — sem dependência).
Cada evento processado carrega `trace_id` que atravessa o pipeline. Métricas simples
(contadores por etapa) expostas no health/status.

- Logs em JSON: consultáveis, parseáveis, sem gambiarra.
- `trace_id`: correlação ponta a ponta (ingestão → alerta).
- Health: `GET /api/v1/health` reporta status por componente.

## Consequências
- (+) Depuração em produção sem caixa preta.
- (+) Base para dashboards de operação (futuro).
- (-) Custo de formatação JSON por evento — aceitável na v1 (métrica para tuning).
- Manutenção em 1 ano: rastrear um alerta à origem é direto (trace_id).

## Critério "daqui a um ano"
Qualquer operador explica o caminho de um evento com um trace_id.
