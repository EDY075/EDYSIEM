# ADR-003 — Pipeline e Concorrência

- **Status:** Aceito
- **Data:** 2026-08-03

## Contexto
O fluxo Entrada → Normalização → Enriquecimento → Correlação → Detecção → Incidente é o coração
do SIEM. Precisa ser processável, observável e escalável sem violar a arquitetura.

## Decisão
**Pipeline linear com etapas assíncronas** (`asyncio` + filas internas com backpressure).
Cada etapa é uma função pura de transformação com contrato tipado, executada por um worker
com timeout. Estado compartilhado mínimo (sem lock global).

- Etapas são testáveis isoladamente (funções puras).
- Backpressure: se uma etapa atrasa, a anterior pausa (filas limitadas).
- Observabilidade: cada etapa emite métricas e log estruturado (ver ADR-006).

## Consequências
- (+) Simples de testar e raciocinar; cada etapa ensina um conceito.
- (+) Idempotência e replay (eventos imutáveis).
- (-) Workers processam eventos; para alto throughput futuro, fila externa (Kafka) é plugável
  no mesmo contrato.
- Manutenção em 1 ano: adicionar etapa = novo contrato, sem alterar pipeline existente.

## Critério "daqui a um ano"
Novos coletores e regras entram sem modificar etapas existentes.
