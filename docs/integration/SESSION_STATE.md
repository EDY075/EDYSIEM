# Session State — EDY Shield → EDY SIEM

## Estado

- Análise arquitetural e contrato oficial v1 concluídos em 2026-08-11.
- Branch documental do SIEM: `codex/shield-siem-integration-architecture`.
- EDY SIEM base: `e929982`, v0.2.0; EDY Shield: `5fd63bb`, v2.2.0.
- Nenhum código funcional foi alterado.
- Documentos obrigatórios:
  - `docs/integration/SHIELD_SIEM_HANDOFF.md`
  - `docs/integration/EVENT_CONTRACT_V1.md`

## Contrato fechado

- Endpoint: `POST /api/v1/ingestion/sources/edy-shield/events`.
- Envelope: `batch_id`, `sent_at`, `events`; 1–100 eventos e máximo 1 MiB.
- Evento v1: `event_id`, `schema_version=1.0`, `timestamp`, `sequence`, `source`,
  `event_type`, `severity`, `asset`, `evidence`, `metadata`.
- Idempotência: `(source.instance_id, event_id)`; `Idempotency-Key = batch_id`.
- Auth: Bearer token scoped via `EDY_SIEM_TOKEN`/`EDYSIEM_SHIELD_INGEST_TOKEN`, sem
  secrets no código e sem confiar em `X-EDY-Role`.
- Transporte: timeout 2 s/5 s, at-least-once, full-jitter até 5 min, outbox persistente;
  SIEM persiste inbox antes do `202`.
- Opcionais são omitidos; `null` e campos raiz desconhecidos são rejeitados.
- SIEM decide alertas, incidentes e casos. Bancos continuam separados.

## Lacunas atuais

- Shield ainda não converte `ScanResult`/`FimDiff` em telemetria nem possui outbox.
- SIEM ainda não possui rota, inbox, parser ou normalizer `edy_shield`.
- O fluxo real ainda não cria incidente/caso fora de `run_demo`.

## Próxima ação exata

1. Criar ADR no EDY SIEM formalizando contrato, outbox/inbox e segurança.
2. Copiar os seis exemplos do contrato para fixtures e criar testes de contrato
   inicialmente vermelhos, sem transporte.
3. Só depois criar schemas/rota/inbox no SIEM.
4. No Shield, começar por testes `FimDiff → TelemetryEventV1`.

Não usar o banco do outro projeto, não importar módulos entre repositórios e não expor
`/soc/pipeline/run` como contrato externo.
