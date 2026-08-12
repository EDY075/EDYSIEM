# Session State — EDY Shield → EDY SIEM

## Estado

- Etapa do receptor/inbox API v1 no EDY SIEM concluída em 2026-08-11.
- Branch: `codex/shield-siem-integration-architecture`.
- Base da etapa: `0137dc4`.
- EDY SIEM v0.2.0; EDY Shield v2.2.0/`5fd63bb`.
- Nenhum código, banco ou frontend do EDY Shield foi alterado nesta etapa.

## Arquitetura implementada

- Endpoint: `POST /api/v1/ingestion/sources/edy-shield/events`.
- Auth M2M: `Authorization: Bearer`, token atual obrigatório e token anterior opcional
  para rotação; comparação em tempo constante e sem secrets em logs/código.
- HTTPS obrigatório fora de loopback.
- Envelope e eventos validados pelo Event Contract v1 congelado.
- Migração SQLite v5 cria recibos em `ingestion_batches` e eventos em
  `ingestion_inbox`.
- O recibo e os eventos aceitos são gravados atomicamente antes do `202`.
- Idempotência de evento por `(source.instance_id, event_id)` + SHA-256 canônico.
- Idempotência de lote por `batch_id = Idempotency-Key` + SHA-256 canônico do corpo.
- Adapter isolado `ShieldEventV1 -> CanonicalEvent`; payload original e normalizado ficam
  persistidos para investigação/reprocessamento.
- Batch misto suporta `accepted`, `duplicate` e `rejected` por item. Lote totalmente
  inválido persiste recibo idempotente e retorna `422`.

## Configuração necessária

```dotenv
EDYSIEM_DB=edysiem.db
EDYSIEM_SHIELD_INGEST_TOKEN=<token aleatório com pelo menos 32 bytes>
# EDYSIEM_SHIELD_INGEST_PREVIOUS_TOKEN=<token anterior durante rotação curta>
```

O exemplo versionado está em `.env.example`; nenhum segredo real foi adicionado.

## Arquivos alterados/criados

- `.env.example`
- `src/edysiem/api/app.py`
- `src/edysiem/api/deps.py`
- `src/edysiem/api/ingestion_schemas.py`
- `src/edysiem/api/routes/shield_ingestion.py`
- `src/edysiem/api/security.py`
- `src/edysiem/api/shield_normalizer.py`
- `src/edysiem/container.py`
- `src/edysiem/persistence/__init__.py`
- `src/edysiem/persistence/inbox.py`
- `src/edysiem/persistence/schema.py`
- `src/edysiem/persistence/transactions.py`
- `tests/test_persistence.py`
- `tests/test_shield_ingestion_api.py`
- `docs/integration/SHIELD_SIEM_HANDOFF.md`
- `docs/integration/SESSION_STATE.md`

## Testes e resultados

- Focados em receptor, contrato, persistência e segurança: 151 aprovados.
- Cobertura focada: 95,20%.
- Suíte completa: 928 testes aprovados.
- Cobertura global: 95,15% (gate de 95% aprovado).
- Ruff: aprovado em todo o repositório.
- MyPy: aprovado em 151 arquivos.
- `git diff --check`: aprovado.
- Dois warnings de depreciação preexistentes de Starlette/FastAPI; nenhuma falha.

## Limitações conhecidas e fora de escopo

- O token v1 possui escopo fixo `ingestion:shield:write`; cadastro de credenciais por
  instalação e resposta `403` por escopo ficam para a evolução multiagente.
- Em proxy reverso, a aplicação precisa receber corretamente o scheme HTTPS confiável;
  configuração de proxy/TLS é responsabilidade do deploy.
- A inbox recebe e normaliza, mas deixa `processing_status=pending`; o worker downstream
  para enrichment, detecção, incidentes e casos não faz parte desta etapa.
- Producer, outbox, retry/backoff e health do conector no EDY Shield ainda não existem.
- Nenhum frontend foi modificado.

## Git

- Branch: `codex/shield-siem-integration-architecture`.
- Base: `0137dc4` (`docs: sync Shield SIEM session state`).
- Commit principal do receptor: pendente no momento desta gravação; consultar
  `git log -2 --oneline` após o clone.
- O commit posterior pode sincronizar aqui o hash principal.

## Próximo passo EXATO

Implementar o **producer/outbox no EDY Shield**:

1. Mapear FIM/baseline/scan/hash/alertas locais para os nove `event_type` do contrato v1.
2. Criar `telemetry_outbox` no SQLite do Shield, com enqueue na mesma unidade de trabalho
   da operação local e estados `pending`, `in_flight`, `sent`, `dead_letter`.
3. Criar worker independente com batch máximo 100/1 MiB, timeout 2 s/5 s, retry, full
   jitter, `Retry-After`, lease recuperável e prioridade critical/high.
4. Configurar `EDY_SIEM_ENABLED`, `EDY_SIEM_URL`, `EDY_SIEM_TOKEN` e instance ID sem
   segredo no código.
5. Testar SIEM offline, restart, resposta perdida, duplicata, 401/403, 409, 413, 422,
   429/5xx e fila cheia sem interromper scans ou alertas locais.

Pare antes de criar frontend ou o worker downstream da inbox no SIEM. Não compartilhar
banco nem importar módulos de runtime entre os projetos.
