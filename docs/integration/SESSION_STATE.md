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

## Sprint B2 — Decision Queue, SLA & Ownership: COMPLETE (2026-08-12)

A Home mantém o SOC Decision Center da B1, mas a Decision Queue agora funciona como
fila operacional compacta, filtrável e determinística.

- Itens exibem severidade, título, source, ativo, evidência, owner, SLA, estado e CTA
  contextual sem usar cards grandes.
- Ordem: critical, high, SLA vencido, SLA próximo, sem responsável e demais; empates usam
  deadline real, severidade, ownership, data e ID, sem score inventado.
- SLA usa o deadline persistido para mostrar tempo restante ou atraso. Ausência real é
  diferenciada como `Sem SLA` ou `caso não aberto`.
- Filtros compactos: severidade, source, SLA, responsável e estado; estado sem resultado
  não é confundido com fila vazia.
- `Assumir` reutiliza a API de incidentes, bloqueia reentrada/duplo POST, mostra loading,
  sucesso e erro e reconcilia a UI após refetch.
- Eventos EDY Shield mantêm arquivo, hash, baseline, ativo e o deep link do mesmo
  `event_id`; investigação, casos e MITRE não foram alterados.
- Hooks preservam dados anteriores durante falhas transitórias; recarga sem dados e API
  offline mostra `Fila temporariamente indisponível`, enquanto backend saudável sem itens
  mostra `Fila de decisão vazia`.
- Listagens SOC aceitam `limit` validado entre 1 e 100, mantendo o contrato existente.

Validação:

- 28 testes focados aprovados.
- 935 testes completos aprovados; cobertura global 95,09%.
- Ruff, MyPy (152 arquivos), Vite build, wheel/sdist e `git diff --check`: PASS.
- Segurança: strings de título, asset, path e evidência continuam como texto React; zero
  `innerHTML`/`dangerouslySetInnerHTML`; POST de ownership possui trava em memória.
- Google Chrome externo: 1920x1080, 1366x768 e 820x900; filtros, combinação vazia,
  fila vazia real, API offline, dados preservados, SLA vencido/próximo, ownership e deep
  link Shield exercitados.
- Console final: zero erros/warnings após o carregamento. O warning preexistente do React
  Router e uma mensagem da extensão ocorreram antes do marco da revisão final.
- Network/proxy final: health, metrics, incidents, alerts e Shield list retornaram HTTP 200.
- Screenshots finais: `outputs/sprint-b2-decision-queue/08-final-home-1920x1080.jpg`,
  `09-final-home-1366x768.jpg` e `10-final-home-820x900.jpg` no workspace da sessão.
- Branch: `codex/shield-siem-integration-architecture`; commit funcional identificado pela
  mensagem `feat(ui): refine decision queue operations`.

## Próximo passo EXATO

**Sprint B3 — Ingestion Health & Sprint B Closure**

Não iniciar Sprint B3 sem novo prompt. Não fazer merge em main.

## Sprint B — SOC Decision Center: COMPLETE (2026-08-12)

A Sprint B foi encerrada no EDY SIEM sem merge em `main`. O resultado mantém a Home
como centro de decisão, e não como dashboard genérico:

- B1 transformou a Home em **SOC Decision Center**, com Decision Queue principal e
  redução de cards, gráficos, feed e timeline duplicados.
- B2 consolidou a fila operacional compacta com prioridade determinística, SLA relativo,
  ownership, filtros, estados de erro/stale e deep link Shield pelo mesmo `event_id`.
- B3 adicionou Ingestion Health compacto com agregados reais e seguros: receptor,
  eventos aceitos, pendentes, última ingestão e pendência mais antiga, sem payloads,
  identificadores de produtor, paths, tokens ou exceções.
- Receptor pronto, fonte com eventos, fonte sem eventos, receptor indisponível, operação
  degradada e API indisponível são estados distintos. Uma falha do receptor Shield não
  declara o storage nem todo o SIEM offline.
- O ambiente `development` é identificado como laboratório local. Ausência de eventos
  não é tratada como fonte offline porque o produto não possui um SLA de heartbeat.
- O último snapshot de health é compartilhado entre Home e barra global; em falha
  transitória ele é preservado e marcado como desatualizado. O polling de 30 segundos
  passou a realizar uma consulta real e deduplicada.
- A barra global deixou de exibir EPS/latência sem medição confiável e não contradiz mais
  o estado agregado. O topbar compacto foi antecipado para eliminar overflow em 820 px.
- Decision Queue, filtros, SLA, ownership, investigação Shield, casos, MITRE e deep links
  permanecem funcionais. Fluxo final verificado: Home → filtro Shield → investigação pelo
  mesmo `event_id` → caso vinculado → Home.

Validação final:

- 33 testes focados de health/API/persistência aprovados.
- 937 testes completos aprovados; cobertura global 95,09%.
- Ruff e MyPy em 152 módulos: PASS.
- Vite build e build backend wheel/sdist: PASS.
- `git diff --check`, scan de XSS (`innerHTML`/`dangerouslySetInnerHTML`/`eval`) e scan de
  encoding nos arquivos alterados: PASS.
- Google Chrome externo: 1920x1080, 1366x768 e 820x900; estados saudável, sem eventos,
  receptor indisponível, API offline, fila vazia e dados anteriores preservados.
- Problemas visuais corrigidos: horário cortado na barra global, fato de fonte truncado e
  overflow horizontal do topbar em 820 px.
- Console final em aba limpa: sem erro ou warning novo da sprint. O aviso conhecido do
  React Router em desenvolvimento permanece fora do código alterado.
- Screenshots finais: `outputs/sprint-b3-ingestion-health/01-home-1920x1080.jpg`,
  `02-home-1366x768.jpg` e `03-home-820x900.jpg` no workspace da sessão.

Commits da Sprint B:

- B1: `45c25d6` (`feat(ui): add SOC decision center`).
- B2: `f253784` (`feat(ui): refine decision queue operations`).
- B3: commit identificado pela mensagem `feat(ui): complete ingestion health`.

Limitações restantes:

- O backend não possui heartbeat do agente Shield nem expectativa de frequência; por
  isso a UI mostra a última recepção, mas não inventa estado `offline` por silêncio.
- Não há outras fontes externas registradas no contrato atual para validar uma segunda
  fonte offline. O estado de componente degradado continua suportado pelo health agregado.
- Eventos da inbox permanecem `pending` até o worker downstream, fora do escopo desta
  sprint; a UI os descreve como aguardando processamento, sem declarar perda.

## Próximo passo EXATO

# Sprint C — Investigation Workflow

Fluxo esperado: Alerta → Evidência → Entidade → MITRE → Decisão → Caso.

Não iniciar Sprint C sem novo prompt. Não fazer merge em main.

## Sprint C1 — Investigation Layout & Evidence: COMPLETE (2026-08-12)

A primeira etapa da Sprint C reorganizou a investigação para o fluxo operacional
**Alerta → Evidência → Entidade → MITRE → Decisão → Caso**, mantendo MITRE e casos em
seu escopo existente:

- O deep link Shield ganhou cabeçalho operacional com severidade, origem, ativo, arquivo,
  ocorrência, recebimento, processamento, responsável e SLA provenientes de dados reais.
- Evidência passou a ser protagonista: caminho, hashes completos em monospace e copiáveis,
  algoritmo, baseline, scan, tamanho, mtime e descrição factual da mudança.
- Ausência de hash anterior, baseline, path ou artefato é declarada sem criar valor. O
  evento `file.added` real foi validado sem hash anterior.
- Timeline usa somente `timestamp`, `received_at` e estado de processamento persistidos;
  não duplica timestamps para sugerir etapas não observadas.
- O painel de decisão mostra owner/status/SLA do caso e abre o caso exato por
  `/cases?case={case_id}`. O Case Center seleciona esse ID e oferece retorno seguro ao
  mesmo evento Shield.
- A investigação genérica preserva alertas, IOCs, ativos, usuários e MITRE, adiciona
  evidência/proveniência de primeira classe, erro retryable e navegação estável ao caso.
- Erros estruturados da API distinguem `wrong_source`, `shield_event_not_found` e UUID
  inválido; a UI não propaga detalhes internos. Evidências permanecem texto React e JSON
  colapsado, sem HTML arbitrário.

Validação:

- 7 testes focados aprovados.
- 938 testes completos aprovados; cobertura global 95,09%.
- Ruff, MyPy (152 arquivos), Vite build, wheel/sdist e `git diff --check`: PASS.
- Google Chrome externo: deep link Shield crítico/com hashes, evento sem hash anterior,
  investigação normal, caso exato, loading, não ingerido, API indisponível e recuperação.
- Viewports: 1920x1080, 1366x768 e 820x900; sem overflow horizontal novo.
- Console final em aba limpa: zero erros da aplicação. Permanece apenas o warning de
  future flag do React Router já existente em desenvolvimento.
- Screenshots finais: `outputs/sprint-c1-investigation-evidence/01-shield-critical-hashes-1920x1080.jpg`,
  `02-normal-investigation-1920x1080.jpg`, `03-exact-linked-case-1920x1080.jpg`,
  `04-file-added-no-previous-hash-1366x768.jpg`, `05-shield-evidence-responsive-820x900.jpg`
  e `06-event-not-ingested-820x900.jpg` no workspace da sessão.
- Branch: `codex/shield-siem-integration-architecture`; commit identificado pela mensagem
  `feat(ui): redesign investigation evidence flow`.

Limitações preservadas:

- A inbox permanece `pending` até o worker downstream já declarado fora do escopo.
- A Sprint C1 não aprofundou o modelo de entidades, MITRE nem automações de decisão; isso
  pertence à próxima etapa.
- O frontend ainda não possui runner de testes de componentes; os estados visuais foram
  exercitados no Chrome externo e os contratos/segurança no pytest.

## Próximo passo EXATO

# Sprint C2 — Entity, MITRE & Decision

Não iniciar Sprint C2 sem novo prompt. Não fazer merge em main.

## Hotfix — War Room / Ingestion Health: COMPLETE (2026-08-12)

Regressão entre B3 e o War Room corrigida antes da Sprint C2:

- Causa raiz: `WarRoomPage` enumerava o objeto heterogêneo `SystemHealth` com
  `Object.entries(health)`. A B3 adicionou `ingestionDetails` como objeto estruturado e
  o cast `as string` permitia que `healthLabel` o devolvesse como React child.
- Correção: a grade de pipeline agora usa uma lista explícita e tipada dos oito
  `ComponentStatus` (`ingestion`, `correlation`, `enrichment`, `detection`, `alerts`,
  `cases`, `storage`, `api`). `overall`, `environment` e `ingestionDetails` permanecem
  metadados e não são renderizados genericamente.
- `healthTone` e `healthLabel` aceitam somente `ComponentStatus`; os casts inseguros
  foram removidos. Os consumidores B3 da Home e barra global permanecem inalterados.
- Teste de regressão impede `Object.entries(health)`, `as string` e inclusão de
  `ingestionDetails` na lista renderizável.
- Não existe Error Boundary próprio no router atual. Uma boundary de rota foi registrada
  como melhoria futura de resiliência; não foi incluída neste hotfix cirúrgico.

Validação:

- 15 testes focados aprovados.
- 939 testes completos aprovados; cobertura global 95,09%.
- Ruff, MyPy (152 arquivos), Vite build, wheel/sdist e `git diff --check`: PASS.
- Google Chrome externo: Overview → War Room → Overview → War Room, investigação Shield,
  Decision Queue, Ingestion Health e status global; 1920x1080 e 1366x768.
- Console final: zero erros; permanece somente o warning conhecido de future flag do
  React Router em desenvolvimento.
- Network/proxy: health, metrics e alertas SOC retornaram HTTP 200.
- Screenshots: `outputs/hotfix-war-room-health/01-war-room-fixed-1920x1080.jpg` e
  `02-war-room-fixed-1366x768.jpg` no workspace da sessão.

## Próximo passo EXATO

# Sprint C2 — Entity, MITRE & Decision

Não iniciar Sprint C2 automaticamente. Não fazer merge em main.

## Sprint C2 — Entity, MITRE & Decision: COMPLETE (2026-08-12)

A investigação agora fecha o trecho **Entidade → MITRE → Decisão** sem reduzir a
evidência construída na C1:

- o evento Shield expõe o endpoint de origem, asset ID, IP, sistema operacional,
  integração, inventário SIEM existente e contagens relacionadas por consulta somente
  leitura; telemetria não sobrescreve o inventário;
- o backend normaliza apenas o campo canônico `x_mitre`, valida IDs `Txxxx` e
  `Txxxx.xxx`, remove duplicatas e descarta valores inseguros; nome, tática e origem são
  exibidos somente quando recebidos, sem inferência por severidade ou arquivo;
- sem associação confiável, a UI informa discretamente
  **Técnica MITRE ainda não associada a este evento**;
- a área **Próxima decisão** reúne owner, SLA, status, prazo e evidências do caso, com
  ações reais para assumir, continuar a investigação e abrir o caso exato;
- a investigação genérica recebeu SLA e decisão contextual, mantendo alertas, IOCs,
  ativos, MITRE, timeline e evidências;
- `?case=` ausente/obsoleto não seleciona silenciosamente o primeiro caso, evitando ação
  sobre o contexto errado;
- o deep link e o retorno preservam o mesmo `event_id` Shield validado e codificado.

Validação:

- 18 testes focados aprovados.
- 941 testes completos aprovados; cobertura global 95,09%.
- Ruff, MyPy (152 arquivos), TypeScript, Vite production build, wheel/sdist e
  `git diff --check`: PASS.
- O Vite foi compilado a partir de uma cópia mecânica do mesmo frontend dentro da área
  autorizada, com `configFile: false` e a configuração equivalente fornecida à API de
  build, porque o carregador de config do checkout encontrou uma restrição de leitura do
  sandbox. 676 módulos foram transformados com sucesso.
- Google Chrome externo: 1920x1080, 1366x768 e 820x900; evento Shield com MITRE, sem
  MITRE, sem responsável, ownership, caso vinculado, investigação genérica, deep link
  reverso e case query inexistente.
- Sem overflow horizontal. Console sem erro da aplicação; permanece o warning conhecido
  de future flag do React Router. O Chrome também registrou mensagens de canal assíncrono
  sem stack da aplicação durante navegação; o mesmo ruído de extensão ocorreu em abas
  antigas e numa aba limpa, sem request falho ou impacto na UI.
- Screenshots finais em `outputs/sprint-c2-entity-mitre-decision/`:
  `01-shield-mitre-decision-1920x1080.png`, `02-shield-no-mitre-1366x768.png` e
  `03-shield-responsive-820x900.png`.

Segurança:

- hostname, asset, path, nome/tática MITRE e metadata continuam texto React inerte;
- nenhuma URL é aceita de metadata e não existe renderização HTML arbitrária;
- IDs MITRE são validados no backend, payload bruto permanece colapsado e o case
  preserva exatamente a mesma lista normalizada;
- ownership possui guarda de request em andamento e não executa duas vezes por clique.

Limitações preservadas:

- não existe catálogo local de nomes/táticas ATT&CK; esses campos só aparecem quando a
  fonte os fornece junto a um ID válido;
- `analista.soc` continua sendo a identidade de desenvolvimento existente, pois auth/RBAC
  não faz parte desta sprint;
- o frontend ainda não possui runner de testes de componentes; contratos, segurança,
  tipos e fluxos foram cobertos por pytest, TypeScript e Chrome externo.

## Próximo passo EXATO

# Sprint C3 — Case Handoff & Investigation Workflow Closure

Não iniciar Sprint C3 automaticamente. Não fazer merge em main.

## Sprint C — Investigation Workflow: COMPLETE (2026-08-12)

A C3 fechou o fluxo completo **Alerta → Evidência → Entidade → MITRE → Decisão → Caso**
reutilizando o Case Center e preservando tudo o que foi entregue nas C1/C2:

- criar caso a partir do evento Shield usa o vínculo real `shield-event:{event_id}` e
  preserva source, ativo, severidade, evidência original validada, MITRE e contexto;
- um índice parcial único em `cases.incident_id` e a criação idempotente garantem um
  único `case_id`; a evidência Shield entra no mesmo persist inicial do caso;
- requests concorrentes e duplo clique retornam o mesmo caso, sem evidência duplicada;
- quando o caso já existe, a UI remove a criação e oferece **Abrir caso**/
  **Continuar investigação** para o `case_id` exato;
- `useCases` resolve `?case=` por GET exato quando o item está fora da página da fila;
  ID inválido ou 404 real nunca seleciona outro caso por inferência;
- o Case Center mostra proveniência compacta EDY Shield com `event_id`, ativo, arquivo e
  retorno seguro à investigação original;
- falha no detalhe do caso possui loading, erro e retry próprios e não é apresentada
  como timeline/evidência vazia;
- **Assumir** usa claim condicional em transação SQLite `BEGIN IMMEDIATE`; o primeiro
  owner vence e concorrentes recebem conflito 409 estruturado;
- IDs de evento/caso são UUIDv4 canônicos, rotas usam `encodeURIComponent` e a API de
  investigação devolve erros bounded sem exceções internas.

### C1, C2 e C3

- C1: evidência, hashes, baseline/scan, timeline real e estados de consulta.
- C2: entidade/inventário read-only, MITRE confiável, decisão, owner e SLA.
- C3: criação/abertura idempotente, handoff exato, proveniência no caso e retorno ao
  mesmo `event_id`.

### Quality Gate

- 43 testes focados aprovados.
- 947 testes completos aprovados; cobertura global **95,02%**.
- Ruff, MyPy (152 arquivos), TypeScript e `git diff --check`: PASS.
- Vite production build: 676 módulos transformados. O carregador TS do `npm run build`
  encontrou a restrição de leitura do sandbox; a mesma configuração foi executada pela
  API Vite com `configFile: false` e concluiu sem erro.
- Backend: wheel e sdist gerados (`edy_siem-0.2.0-py3-none-any.whl` e
  `edy_siem-0.2.0.tar.gz`). O wheel foi construído diretamente sem isolamento para
  evitar o limite de path do Windows ao reextrair o sdist com `frontend/node_modules`.
- Google Chrome externo validado em 1920x1080, 1366x768 e 820x900: sem caso, criação,
  duplo clique, caso existente, investigação genérica, Case Center exato, ownership,
  retorno, 404 de case e API indisponível/recuperação.
- Network: create produziu um único POST no duplo clique; health, fila, investigação,
  case e claim responderam 200, com 409 esperado no teste de claim concorrente.
- Console: nenhum erro React/JavaScript da sprint. Permanece o warning conhecido de
  future flag do React Router; o Chrome registrou também ruído de canal assíncrono da
  extensão, sem stack no bundle ou impacto na UI.
- Screenshots finais em `outputs/sprint-c3-siem/`: `06-case-handoff-final-1920.png`,
  `02-investigation-linked-1366.png`, `03-investigation-linked-820.png` e
  `05-case-handoff-820-corrected.png`.

### Limitações restantes

- A identidade `analista.soc` continua sendo a identidade fixa do ambiente de
  desenvolvimento; autenticação/RBAC real permanece fora do escopo.
- O frontend ainda não possui runner de testes de componentes; contratos, tipos,
  concorrência e segurança são cobertos por pytest/TypeScript, e UX pelo Chrome real.
- O sdist atual inclui o frontend completo e `node_modules`, produzindo artefato grande;
  excluir dependências do sdist é hardening de empacotamento futuro.
- O Error Boundary próprio do React Router segue registrado como melhoria futura.

Commits da Sprint C:

- C1: `e3f83e6` (`feat(ui): redesign investigation evidence flow`).
- Hotfix: `1abecef` (`fix(ui): prevent structured health render in war room`).
- C2: `60180a8` (`feat(ui): complete entity mitre decision flow`).
- C3: commit identificado pela mensagem `feat(ui): close investigation case handoff`.

## Próximo passo EXATO

# Sprint D — Shared Design System & Final Product Polish

Não iniciar Sprint D automaticamente. Não fazer merge em main.

## Revalidação de recuperação — Sprint C3 (2026-08-12)

- A retomada confirmou o commit local `ac49355` com worktree limpo; nenhum diff válido foi
  descartado ou refeito.
- 43 testes focados da C3 e 947 da suíte completa passaram, com cobertura global de 95,02%.
- Ruff, MyPy (152 módulos), TypeScript, bundle Vite de produção e build wheel/sdist do
  backend passaram. O carregamento usual de `vite.config.ts` foi limitado pelo sandbox;
  a mesma configuração foi validada pela API Vite com `configFile: false`, sem alteração
  no produto.
- Chrome externo em ambiente isolado: evento EDY Shield ingerido, clique repetido criou
  um único case/evidência, Case Center abriu o `case_id` exato com proveniência e retornou
  ao mesmo `event_id`.
- War Room, Ingestion Health e Decision Queue foram preservados. Sprint D segue fora de escopo.

## Sprint D — Shared Design System & Final Product Polish: COMPLETE (2026-08-12)

O refinamento final preservou a identidade SOC azul/ciano do EDY SIEM e limitou-se a
resiliência de navegação, sem alterar Decision Queue, Ingestion Health ou War Room.

- `frontend/src/routing/RouteErrorBoundary.tsx` substitui a tela crua do router por uma
  recuperação operacional: explica que nenhum dado foi alterado e oferece retry e retorno
  ao Overview.
- `frontend/src/routing/routes.tsx` registra o `errorElement` no shell principal; a
  cobertura de regressão em `tests/test_frontend_error_boundary.py` bloqueia o fallback
  padrão do React Router.
- O fluxo existente Shield → investigação → Case Center continuou apontando para o mesmo
  `event_id`; o Case Center e a investigação real foram reabertos no Chrome externo.

Validação final: 948 testes, cobertura 95,02%, Ruff, MyPy (152 módulos), `tsc -b`, Vite,
wheel/sdist e `git diff --check` aprovados. Chrome externo foi revisado em 1920×1080,
1366×768, 820×900 e 390×844, sem overflow horizontal. A única mensagem não funcional
observada permaneceu o aviso pré-existente de future flag do React Router e ruído de
extensão; não houve erro novo da aplicação.

## Próximo passo exato

**FINAL — Release Readiness / final product sign-off.** Não iniciar automaticamente, não
fazer merge em `main` e não reabrir escopo de produto sem novo prompt.

## RELEASE COMPLETE — v0.3.0 (2026-08-12)

- Produção: merge não destrutivo em `master` no commit `b9e0bdf`, seguido do alinhamento
  do rodapé no commit `aa48ff9`; remoto confirmado em 0/0.
- Qualidade: 948 passed, 95,02% coverage; Ruff, MyPy, TypeScript/Vite, wheel/sdist,
  `npm audit` sem vulnerabilidades e `git diff --check` aprovados.
- E2E em processos reais: evento FIM do Shield com `event_id` estável, case idempotente,
  recuperação offline, zero eventos perdidos e zero duplicatas lógicas.
- Chrome externo: Overview, War Room, Case Center, recuperação de rota e o fluxo Shield
  foram verificados sem erro da aplicação ou overflow horizontal.
- Próxima manutenção: partir de `master`; a tag de release é `v0.3.0`.
