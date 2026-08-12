# Session State — EDY Shield → EDY SIEM

## Estado

- Etapa de golden contract concluída em 2026-08-11.
- Branch: `codex/shield-siem-integration-architecture`.
- Base anterior desta etapa: `8fc98ed`.
- EDY SIEM v0.2.0; EDY Shield v2.2.0/`5fd63bb`.
- Não foram criados endpoint, transporte, outbox, worker ou frontend.

## Arquitetura vigente

- Shield é local-first e continua funcional com SIEM offline.
- Bancos e módulos de runtime permanecem separados.
- Futuro envio HTTPS em batch usa outbox no Shield e inbox durável/idempotente no SIEM.
- Chave do evento: `(source.instance_id, event_id)`; lote usa
  `Idempotency-Key = batch_id`.
- Auth M2M: Bearer token scoped em variáveis de ambiente; não confiar em `X-EDY-Role`.
- SIEM normaliza e decide alertas, incidentes e casos.
- WAR_ROOM continua fonte futura independente de threat intelligence/enrichment.

## Contrato v1 congelado

- Documento: `docs/integration/EVENT_CONTRACT_V1.md`.
- ADR: `docs/architecture/adr/ADR-010-shield-siem-event-integration.md`.
- Modelo: `src/edysiem/api/ingestion_schemas.py`.
- Fixtures: `tests/fixtures/shield_events/v1/valid/` e `invalid/`.
- Testes: `tests/test_shield_event_contract_v1.py`.
- Sete cenários válidos: `file_created`, `file_modified`, `file_deleted`, `hash_changed`,
  `baseline_created`, `scan_completed`, `critical_security_alert`.
- O enum v1 possui `shield.fim.baseline.created`; `baseline_changed` não existe.
- Oito fixtures inválidas cobrem campos ausentes, versão/timestamp/enums inválidos,
  asset incompleto, campo raiz extra e `null` explícito.

## Validação concluída

- Contrato focado: 85 testes aprovados; cobertura do modelo 97,00%.
- Suíte completa: 886 testes aprovados, 95,17% de cobertura e 2 warnings de depreciação
  preexistentes de Starlette/FastAPI.
- MyPy: sucesso em 148 arquivos.
- Ruff: sem achados.
- Golden check: documentação ↔ sete fixtures ↔ modelo Pydantic aprovado.

## Git

- Branch: `codex/shield-siem-integration-architecture`.
- Commit principal desta etapa: `3a62e3e` (`feat(contract): freeze Shield event contract v1`).
- O commit imediatamente posterior apenas sincroniza este hash no estado da sessão; use
  `git log -2 --oneline` para confirmar ambos após o clone.

## Próximo passo exato

Implementar o receptor/ingestion API v1 no EDY SIEM:

1. Criar migração e repository para `ingestion_batches`/`ingestion_inbox`.
2. Criar autenticação M2M scoped específica para o Shield.
3. Criar `POST /api/v1/ingestion/sources/edy-shield/events` usando o modelo congelado.
4. Persistir itens válidos antes de responder `202` e aplicar idempotência de
   batch/evento, com resultados `accepted`, `duplicate` e `rejected`.
5. Testar auth, persistência, duplicação, conflito, lote misto, limites e `503`.

Pare antes de implementar transporte HTTP/outbox/worker no Shield ou qualquer frontend.
Não usar banco compartilhado nem expor `/soc/pipeline/run` como contrato externo.
