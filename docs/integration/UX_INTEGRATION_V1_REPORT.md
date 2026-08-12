# UX Integration V1 - EDY Shield -> EDY SIEM

Data: 2026-08-12

Commit de implementacao SIEM: `6d30737`.
Commit de implementacao Shield: `4fa8e78`.

## Resultado

A UX Integration V1 foi concluida nas branches de integracao, sem merge em `main` e
sem alterar o Event Contract v1. O Shield agora apresenta o estado real de entrega de
um alerta e, somente quando o evento foi entregue, oferece a acao **Investigar no EDY
SIEM**. A acao abre a investigacao contextual do mesmo evento no SIEM.

## Deep link e APIs

- Deep link: `/investigate/shield/{event_id}`.
- Shield: `GET /api/integrations/edy-siem/alerts/{alert_id}` resolve o ultimo evento
  `shield.alert.%` relacionado ao alerta local e retorna um estado de UX seguro.
- SIEM: `GET /api/v1/investigation/sources/edy-shield/events/{event_id}` valida UUIDv4,
  exige `source.name=edy-shield` e carrega o evento persistido na inbox.
- SIEM: `POST /api/v1/investigation/sources/edy-shield/events/{event_id}/cases` reutiliza
  o servico de casos existente e e idempotente para o mesmo evento.
- A URL publica do frontend SIEM vem de `EDY_SIEM_UI_URL`; nao existe dominio de
  producao ou `localhost` fixado no codigo.

## Semantica no Shield

Os estados visiveis sao: integracao desativada, indisponivel, pendente, falha
temporaria, falha definitiva e entregue. O botao so e liberado no estado entregue,
pois esse e o unico estado que prova que o receptor SIEM confirmou a ingestao. Tokens,
erros internos e credenciais nao sao devolvidos ao frontend.

## Investigacao no SIEM

A pagina apresenta, conforme o contrato real:

- severidade, tipo, origem, ativo, timestamp, status e sequencia de ingestao;
- caminho do arquivo, mudanca FIM, baseline e hashes anterior/atual copiaveis;
- hostname, asset ID, IP e sistema operacional;
- timeline formada apenas por timestamps existentes;
- MITRE ATT&CK somente quando fornecido por `metadata.x_mitre`;
- metadata original como dados renderizados pelo React, sem HTML inseguro;
- criacao ou abertura do caso SOC associado ao evento.

## Teste E2E real controlado

Ambiente local isolado: Shield `:8000`, SIEM API `:8080` e SIEM frontend `:5173`.

- Alerta Shield: `ALT-UX-E2E-003`.
- Event ID: `fa3f171e-bb8e-43f2-9bd3-ae716d7316da`.
- Entrega: confirmada pelo receptor SIEM.
- Deep link: abriu o mesmo Event ID na rota de investigacao.
- Evidencia: caminho, baseline e hashes anterior/atual conferidos.
- MITRE: `T1565.001`, obtido da metadata real do evento.
- Caso criado pela interface: `32964cd9-b797-4ab2-8350-72658d6e7b11`.
- Repeticao da acao reutiliza o caso existente, sem duplicar evidencia.
- UUID invalido mostrou acesso invalido; UUID valido ausente mostrou evento ainda nao
  ingerido.

## Validacoes automatizadas

### EDY SIEM

- Testes focados: 45 aprovados.
- Suite completa: 932 aprovados; cobertura 95,11%.
- Ruff: aprovado.
- MyPy: aprovado em 152 arquivos fonte.
- Backend: wheel e sdist 0.2.0 gerados.
- Frontend: build Vite aprovado, 675 modulos transformados.

### EDY Shield

- Testes focados: 20 aprovados.
- Suite completa: 684 aprovados, 2 ignorados; cobertura 86,67%.
- Ruff: aprovado.
- MyPy: aprovado em 88 arquivos fonte.
- Build: wheel e sdist 2.0.0 gerados.

## Revisao visual e seguranca

- Shield e SIEM revisados em desktop 1440x900 e mobile 428x926, equivalente ao iPhone
  12 Pro Max; sem overflow horizontal.
- Console do Shield sem erros. SIEM sem erros; apenas avisos futuros preexistentes do
  React Router.
- Identificador canonico UUIDv4, source obrigatoria, consulta parametrizada e rejeicao
  de evento ambiguo.
- O deep link contem somente o Event ID; nao contem token, evidencia ou secret.
- URL externa aceita HTTPS e HTTP apenas em loopback, sem credenciais, query ou fragment.
- `window.open` usa `noopener,noreferrer`; React escapa evidence e metadata por padrao.

## Limitacoes deliberadas

- A acao inversa **Voltar ao EDY Shield** nao foi criada porque ainda nao existe URL
  publica confiavel/configuravel para o alerta de origem.
- Alertas anteriores a esta integracao podem nao ter um evento de outbox correlacionado.
- O worker downstream da inbox, WAR_ROOM, SOAR novo e redesign global permanecem fora
  do escopo.

## Proximo passo aprovado

**PRODUCT REDESIGN V1**, sem iniciar nesta sprint:

1. EDY Shield Home -> Endpoint Integrity Center.
2. EDY SIEM Home -> SOC Decision Center.
3. Design system compartilhado com identidades distintas.
4. Fluxo Alerta -> Evidencia -> Entidade -> MITRE -> Caso.
