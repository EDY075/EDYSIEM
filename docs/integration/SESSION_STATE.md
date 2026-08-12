# Session State — EDY Shield → EDY SIEM

## Estado

- Análise arquitetural concluída em 2026-08-11.
- Nenhum código funcional foi alterado.
- EDY SIEM: `master`/`e929982`, v0.2.0.
- EDY Shield: `main`/`5fd63bb`, v2.2.0.
- Documento completo: `docs/integration/SHIELD_SIEM_HANDOFF.md`.

## Constatações essenciais

- Shield FIM gera `ScanResult`/`FimDiff`, mas o fluxo HTTP não os converte hoje em
  `AlertEvent` local nem envia telemetria.
- Shield não possui autenticação real; é uma aplicação local com security headers.
- SIEM aceita syslog no pipeline atual; não existe parser/normalizer `edy_shield`.
- `SocPipeline.run_event` persiste alertas, mas não cria incidentes/casos; o E2E completo
  existe apenas em `run_demo`.
- Não existe idempotência de produtor nem inbox/outbox persistente.

## Arquitetura definida

- Shield local-first com `telemetry_outbox` no próprio SQLite.
- Envio HTTP(S) em batch com token exclusivo e permissionamento de ingestão.
- SIEM grava `ingestion_inbox` durável e responde 202 antes do processamento.
- Chave idempotente: `(source_instance_id, producer_event_id)`.
- Parser + normalizer `source_type=edy_shield` alimentam os engines existentes.
- SIEM decide alertas, incidentes e casos; Shield continua independente offline.
- WAR_ROOM entra futuramente como provider separado de threat intelligence/enrichment.

## Próxima ação exata

1. Criar ADR no EDY SIEM formalizando contrato, outbox/inbox e segurança.
2. Criar schemas e fixtures de contrato v1, ainda sem transporte.
3. No Shield, começar por testes `FimDiff → TelemetryEventV1`.

Não implementar integração consultando o banco do outro projeto e não reutilizar a rota
genérica `/soc/pipeline/run` como contrato externo.
