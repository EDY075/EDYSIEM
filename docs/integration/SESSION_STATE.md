# Session State — EDY Shield → EDY SIEM

> **ESTADO CANÔNICO MAIS RECENTE — 2026-08-11 23:27 BRT.** O primeiro E2E real foi
> concluído com PASS. Leia primeiro `E2E_SHIELD_SIEM_V1_REPORT.md`; as seções antigas
> abaixo permanecem como histórico.

## Checkpoint E2E v1

- SIEM: branch `codex/shield-siem-integration-architecture`, início em `a56ee81`.
- Shield: branch `codex/siem-producer-outbox-v1`, início em `0b0964a`.
- Processos reais em loopback, bancos separados e token efêmero não persistido.
- Primeiro `file_created` e os 7 cenários: PASS.
- Offline: 5 pendentes, 5 recuperados, 0 perdidos, 0 duplicatas lógicas.
- Idempotência, crash recovery, auth correta/ausente/inválida e batch 100+1: PASS.
- Integridade: 122 eventos comparados, sem divergência.
- SIEM: 126 focados; 928 completos; cobertura 95,15%; Ruff/MyPy PASS.
- Checkpoint E2E `4b07923` publicado em
  `origin/codex/shield-siem-integration-architecture`.
- Build oficial PASS: `python -m build` gerou sdist e wheel 0.2.0 após instalar
  `hatchling`, exatamente como declarado em `[build-system]`.
- Nenhum código de produção ou frontend foi alterado.
- Próximo passo: **UX INTEGRATION V1** — receber deep link do Shield e abrir a
  investigação correspondente com origem, ativo, evidências, hashes, timeline, MITRE
  quando aplicável e criação de caso. Não iniciar WAR_ROOM nem worker downstream sem
  nova etapa.

## Estado

- Etapa do receptor/inbox API v1 no EDY SIEM concluída em 2026-08-11.
- Branch: `codex/shield-siem-integration-architecture`.
- Commit de implementacao: `6d30737`.
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
- Commit principal do receptor: `0100a1f`
  (`feat(ingestion): add durable Shield receiver v1`).
- O commit imediatamente posterior sincroniza este hash no estado da sessão; consultar
  `git log -2 --oneline` para obter seu hash completo.

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

> O próximo passo acima foi concluído no Shield pelo commit `6e25619`; o estado atual
> substituto está registrado abaixo.

## Producer Shield implementado

- Repositório: `EDY075/edy-shield`.
- Branch: `codex/siem-producer-outbox-v1`.
- Commit publicado: `6e25619` (`feat: add durable EDY SIEM producer outbox`).
- Resultado: mapper, instance ID, SQLite outbox, HTTPS client e worker conectados a fatos
  reais, opt-in e local-first.
- Validação: 680 testes, 2 skipped, 86,78% de cobertura, Ruff/MyPy/build aprovados.
- Documentação operacional do produtor:
  `docs/integration/EDY_SIEM_INTEGRATION.md` no repositório Shield.

## Próximo passo EXATO — estado atual

Executar o primeiro **E2E real isolado Shield → SIEM** sem alterar frontend:

1. configurar o mesmo token de laboratório nos dois processos;
2. iniciar este receptor e o worker do Shield em loopback;
3. gerar baseline e mudança FIM reais no Shield;
4. confirmar `202`, inbox durável e payload normalizado neste SIEM;
5. derrubar o SIEM, gerar eventos, religá-lo e confirmar replay/duplicate sem perda;
6. salvar evidências e atualizar os dois handoffs.

## Checkpoint UX Integration V1 - 2026-08-12

- Branch: `codex/shield-siem-integration-architecture`.
- Deep link: `/investigate/shield/{event_id}`.
- APIs: GET do evento Shield e POST idempotente para criar/reabrir caso.
- Pagina: `frontend/src/pages/ShieldEventInvestigationPage.tsx`.
- E2E real: evento `fa3f171e-bb8e-43f2-9bd3-ae716d7316da`, alerta
  `ALT-UX-E2E-003`, caso `32964cd9-b797-4ab2-8350-72658d6e7b11`.
- Qualidade: 932 testes, 95,11%, Ruff/MyPy e builds backend/frontend aprovados.
- Relatorio completo: `docs/integration/UX_INTEGRATION_V1_REPORT.md`.
- Proximo passo salvo: **PRODUCT REDESIGN V1**. Nao iniciar sem novo prompt.

## Revalidacao de retomada - 2026-08-12

- Estado recuperado sem alteracoes locais pendentes; o checkpoint UX permanece em `6d30737`.
- Testes focados: 4 aprovados; suite completa: 932 aprovados, 95,11%.
- Ruff, MyPy, builds backend/frontend e `git diff --check`: aprovados.
- Revisao visual local confirmou o estado de evento ainda nao ingerido e suas acoes de
  recuperacao; o unico aviso foi o future flag preexistente do React Router.
- A rota continua validando UUIDv4, origem EDY Shield e reutilizando casos de forma
  idempotente.

## Product Redesign V1 - auditoria concluida (2026-08-12)

Escopo somente de auditoria visual e produto; nenhum codigo, configuracao ou dependencia
foi alterado. Telas reais revisadas em desktop 1920x1080: Overview, Alertas,
investigacao do evento E2E do Shield e Cases.

- A investigacao Shield ja e a tela mais forte: origem, endpoint, path, hashes, baseline,
  MITRE, cadeia de custodia e caso vinculado estao visiveis.
- Problemas: Overview excessivamente denso/repetitivo; ausencia de fila unica de agir
  agora com SLA, responsavel, ativo e proxima acao; health/ingestao contraditorios; e
  evento->caso sem foco garantido no caso vinculado.
- Preservar: shell SOC, navegacao, tabelas, evidencia/origem e timeline.
- Proposta: **SOC Decision Center** com fila de decisao primeiro. A investigacao torna-se
  workspace de duas colunas, com evidencia ao centro e trilho de acoes/responsavel/SLA.
- Sprints: A Shield Endpoint Integrity Center; B SIEM SOC Decision Center; C Investigation
  Workflow; D Shared Design System/refinamento.
- Evidencias: `outputs/product-redesign-v1/siem/01-siem-overview-current.png`,
  `02-siem-alert-queue-current.png`, `03-siem-shield-investigation-current.png` e
  `04-siem-cases-current.png` no workspace da sessao Codex.
- Proximo passo: revisar e aprovar a proposta antes da Sprint A. Nao implementar ainda.

Pare antes de integrar WAR_ROOM, criar frontend ou implementar o worker downstream da
inbox. Não compartilhar banco nem importar runtime entre projetos.

## Sprint B1 — EDY SIEM SOC Decision Center: COMPLETE (2026-08-12)

Estado canônico mais recente: a Home deixou de repetir cards, gráficos, feed, tabela e
timeline do mesmo alerta e agora começa por uma **Decision Queue** única.

- Priorização real: critical, high, SLA vencido/próximo, sem responsável e demais itens.
- Cada linha traz origem, ativo, evidência, owner, SLA e uma próxima ação existente.
- Incidentes usam SLA/owner/assets/IOCs/MITRE reais e suportam `Assumir` e continuação no
  incidente exato por query string.
- Eventos Shield são listados de forma read-only pela inbox, identificados como
  `EDY Shield` e abrem o deep link existente por `event_id`; casos vinculados fornecem
  owner, quantidade de evidências e SLA.
- Health passou a expor receptor Shield, storage e API reais. Ausência de eventos é
  tratada como fonte ainda não conectada, não como produto quebrado.
- Contagens estáticas da sidebar e métricas fictícias do rodapé foram substituídas por
  dados reais ou copy neutra.
- Dados de evento continuam renderizados somente como texto React; não há HTML arbitrário.

Validação:

- 27 testes focados aprovados.
- 934 testes completos aprovados; cobertura global 95,09%.
- Ruff, MyPy (152 arquivos), frontend Vite build, wheel/sdist e `git diff --check`: PASS.
- Google Chrome externo: Home, assumir incidente, incidente exato e investigação Shield.
- Viewports: 1920x1080, 1366x768 e 820x900; empty queue e API offline também validados.
- Console: zero erros da aplicação; permanece apenas o warning de future flag do React
  Router já existente e não habilitável nesta versão tipada do router.
- Screenshots: `outputs/sprint-b1-soc-decision-center/09-final-home-1920x1080.jpg`,
  `10-final-home-owned-1920x1080.jpg`, `11-final-shield-investigation-flow.jpg`,
  `12-final-home-1366x768.jpg`, `13-final-home-responsive-820x900.jpg`, além dos estados
  empty/error `07-home-empty-queue.jpg` e `08-home-api-error.jpg`.

## Próximo passo EXATO

**Sprint B2 — Decision Queue, SLA & Ownership**

Não iniciar Sprint B2 sem novo prompt. Não fazer merge em main.
