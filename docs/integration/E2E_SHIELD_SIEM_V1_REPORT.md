# E2E real EDY Shield → EDY SIEM v1

**Resultado:** PASS para a integração ponta a ponta e para o build oficial do SIEM.

**Execução canônica:** 2026-08-11 23:25–23:27 (America/Sao_Paulo), equivalente a
2026-08-12 02:25–02:27 UTC.

## Ambiente e versões

| Componente | Branch | Commit inicial | Runtime |
|---|---|---|---|
| EDY SIEM | `codex/shield-siem-integration-architecture` | `a56ee81` | Python 3.12.10, FastAPI/Uvicorn, SQLite isolado |
| EDY Shield | `codex/siem-producer-outbox-v1` | `0b0964a` | Python 3.12.10, servidor stdlib, SQLite isolado |

Os processos reais foram executados em loopback: SIEM em `127.0.0.1:8080` e Shield em
`127.0.0.1:8000`. Cada produto usou seu próprio banco. O token M2M foi gerado em
memória, não foi impresso, documentado ou versionado.

## Fluxo comprovado

`fato real no Shield → mapper → siem_outbox → worker → HTTP Bearer M2M → endpoint v1
→ validação → ingestion_inbox → CanonicalEvent → ack individual → sent`

O primeiro evento foi `shield.fim.file.added`, ID
`e499e1bd-48a9-4ea1-ba98-4d12b40f03e4`. Ele saiu do outbox com uma tentativa, chegou
com o mesmo ID e `source.instance_id=8f6fa199-365a-443b-9cc4-6a18b080a88d`, preservou
`file_path=created.txt` e normalizou para `event_action=created`.

## Matriz de resultados

| Cenário | Resultado | Evidência técnica |
|---|---|---|
| Inicialização SIEM | PASS | `/api/v1/health=200`, migrations/inbox disponíveis |
| Inicialização Shield | PASS | `/api/health=200`, instance ID persistente, worker ativo |
| Primeiro `file_created` | PASS | outbox `sent`, inbox e CanonicalEvent com mesmo ID |
| `file_modified` | PASS | FIM real gerou e normalizou `shield.fim.file.modified` |
| `file_deleted` | PASS | FIM real gerou e normalizou `shield.fim.file.removed` |
| `hash_changed` | PASS | Hash Checker real gerou `shield.hash.mismatch` |
| `baseline_created` | PASS | baseline real persistida e entregue |
| `scan_completed` | PASS | scan FIM real persistido e entregue |
| `security_alert` | PASS | `AlertService` real gerou alerta crítico e telemetria |
| SIEM offline | PASS | 5 eventos permaneceram duráveis; Shield continuou saudável |
| Recuperação | PASS | 5 pendentes → 5 entregues; perdas 0; duplicatas lógicas 0 |
| Backoff | PASS | máximo 3 tentativas; `next_attempt_at` avançou após falha |
| Idempotência | PASS | mesmo ID; inbox 16 antes/depois; ack `duplicate` |
| Crash recovery | PASS | exit 9 após lease; tentativa 2 entregou; 1 linha lógica |
| Auth correta/inválida/ausente | PASS | 202/401/401; eventos preservados e recuperados |
| Batch real | PASS | 101 eventos reais enviados em lotes de 100 e 1 |
| Ack por item | PASS | `accepted`, `duplicate`, `rejected` no mesmo lote |
| Limites 100/64 KiB/1 MiB | PASS | excesso retornou `413`; maior evento real: 886 bytes |
| Integridade | PASS | 122 outbox `sent` vs. 122 inbox únicos; 0 diferenças |
| Logs/secrets | PASS | 0 tokens, 0 `Bearer`, 0 tracebacks |

## Geração controlada

- Baseline, arquivos, scan e hash foram produzidos por `POST /api/scan` no Shield real.
- Como não existe endpoint para criar `AlertEvent`, o alerta crítico executou o serviço
  real `AlertService` com o producer real; não houve `INSERT` direto no outbox.
- O crash foi um processo real que adquiriu lease e terminou com `os._exit(9)`, sem
  corromper o banco.
- Para ack misto e limites inválidos, payloads reais foram enviados à borda HTTP real;
  somente cópias inválidas foram mutadas intencionalmente.

## Integridade de dados

Foram comparados payloads JSON persistidos nos dois bancos. Permaneceram idênticos:
`event_id`, `schema_version`, `source`, `instance_id`, `event_type`, `severity`,
`timestamp`, `asset`, `hostname`, `file_path`, hashes, baseline, `evidence` e
`metadata`. O SIEM adicionou somente dados próprios de recebimento e normalização.

## Regressões e quality gates

### EDY SIEM

- focados contrato/receptor: **126 passed**;
- suíte completa: **928 passed**;
- cobertura: **95,15%** (gate 95%);
- Ruff: PASS; MyPy: PASS em 151 arquivos; `git diff --check`: PASS;
- 2 depreciações preexistentes Starlette/FastAPI;
- build de pacote: **PASS** em 2026-08-11; após instalar a dependência legítima de
  desenvolvimento `hatchling`, `python -m build` gerou
  `edy_siem-0.2.0.tar.gz` e `edy_siem-0.2.0-py3-none-any.whl`.

### EDY Shield

- focados producer/outbox: **45 passed**;
- suíte completa: **680 passed, 2 skipped**;
- cobertura: **86,78%** (gate 85%);
- Ruff: PASS; MyPy: PASS em 88 arquivos; `git diff --check`: PASS;
- build: PASS; wheel e sdist 2.0.0 gerados fora do repositório;
- depreciações preexistentes SHA-1/MD5 e metadata de licença.

O `pytest` usou `TEMP`, `TMP`, `USERPROFILE` e `HOME` isolados e graváveis. A tentativa
inicial sem isso falhou por permissão no perfil do usuário, não por regressão.

## Bugs, segurança e limitações

Nenhum bug de produção foi encontrado e nenhum código de produção/frontend foi
alterado. Ajustes feitos foram somente no roteiro descartável do laboratório.

- HTTP somente em loopback; token apenas em ambiente de processos filhos.
- Nenhum secret, `.env`, banco ou log está no working tree dos projetos.
- A inbox ainda fica `processing_status=pending`; worker downstream está fora do escopo.
- O Shield não possui endpoint público para criação de alerta bruto.
- Retenção/purge do outbox continua pendente.
- O build requer `hatchling`, conforme `[build-system]` do `pyproject.toml`.

## Próximo passo

**UX INTEGRATION V1:** no Shield, evento/alerta oferece **“Investigar no EDY SIEM”**;
no SIEM, abrir a investigação correspondente com origem EDY Shield, ativo, evidências,
hashes, timeline, MITRE quando aplicável e criação de caso. Não implementar nesta etapa.
