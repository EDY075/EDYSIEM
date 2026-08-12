# ADR-010 — Integração de Eventos EDY Shield → EDY SIEM

- **Status:** Aceito
- **Data:** 2026-08-11

## Contexto

O EDY Shield é uma ferramenta defensiva local-first: scans, FIM, baseline, verificação de
hash e alertas locais precisam continuar funcionando sem rede. O EDY SIEM é o ponto
central do SOC para receber telemetria, normalizar, enriquecer, correlacionar, investigar
e criar alertas, incidentes e casos.

Os projetos têm ciclos de release e bancos SQLite próprios. Compartilhar schema ou acesso
direto ao banco criaria acoplamento entre domínios e faria uma indisponibilidade do SIEM
afetar o endpoint protegido. A infraestrutura genérica de ingestão do ADR-009 ainda não
define uma fronteira externa durável e idempotente para agentes EDY Shield.

## Decisão

### Contrato e fronteira

- `docs/integration/EVENT_CONTRACT_V1.md` é o contrato normativo inicial, versão `1.0`.
- Modelo Pydantic, exemplos, fixtures versionadas e testes automatizados formam o golden
  contract. Os repositórios não compartilham pacote Python de runtime.
- O endpoint futuro será
  `POST /api/v1/ingestion/sources/edy-shield/events`, exclusivo para essa fonte; as rotas
  genéricas `/pipeline/run` e `/soc/pipeline/run` não são contratos de integração.
- O Shield produz fatos locais. O SIEM preserva a severidade de origem, mas decide a
  classificação analítica, alertas, incidentes e casos finais.

### Transporte e autenticação

- O transporte futuro será HTTPS, assíncrono e em lotes de até 100 eventos/1 MiB.
- HTTP será permitido somente em loopback com modo de laboratório explícito.
- Autenticação máquina-a-máquina v1 usará Bearer token aleatório com escopo fixo
  `ingestion:shield:write`.
- Secrets serão lidos de variáveis de ambiente, nunca incluídos em código, fixtures,
  banco versionado ou logs. A rota não confiará em `X-EDY-Role` informado pelo cliente.

### Confiabilidade e idempotência

- O Shield terá transactional outbox em seu próprio SQLite. O scan/alerta local não
  aguardará nem dependerá da rede.
- O SIEM terá inbox durável em seu próprio banco e só responderá `202` após persistência.
- O transporte será at-least-once; o processamento terá exactly-once lógico pela chave
  `(source.instance_id, event_id)` e pelo hash do JSON canônico.
- Reenvio idêntico será aceito como duplicado; reutilização do mesmo ID com conteúdo
  diferente será conflito auditável.
- Retry, backoff com jitter e dead letter ocorrerão fora do caminho crítico do Shield.

### Entrada no pipeline

Após validação e persistência, o SIEM transformará o payload em `RawEvent`, aplicará um
parser/normalizer `edy_shield` e seguirá o pipeline imutável do ADR-008:

`RawEvent → ParsedEvent → CanonicalEvent → EnrichedEvent → Correlation → Detection`

O adapter específico do Shield reutilizará fila, backpressure, retry, dead letter,
rate-limit, health e métricas do ADR-009; não criará uma segunda infraestrutura genérica.

### Evolução com WAR_ROOM

O WAR_ROOM poderá entrar futuramente como fonte independente de threat intelligence por
feed/API próprio. O SIEM validará confiança, validade e TTL dos IOCs e os disponibilizará
ao enrichment. O Shield não dependerá diretamente do WAR_ROOM.

## Consequências

### Positivas

- Shield mantém autonomia e isolamento de falhas quando o SIEM estiver offline.
- Replay, auditoria e prevenção de alertas/casos duplicados são possíveis.
- Contrato versionado permite evolução independente e testes entre repositórios.
- A normalização permanece centralizada e compatível com os ADRs 008 e 009.
- A futura fonte WAR_ROOM não aumenta o acoplamento no endpoint.

### Negativas

- Outbox e inbox duplicam temporariamente dados e exigem retenção, limpeza e métricas.
- Consistência é eventual; eventos podem chegar atrasados ou fora de ordem.
- Retry, dead letter, rotação de token e migrações aumentam a complexidade operacional.
- SQLite limita concorrência até uma futura troca do adapter de persistência.
- Schema estrito exige versionamento e negociação disciplinados.

## Alternativas consideradas

### Banco compartilhado

Rejeitado porque acopla schema, credenciais, releases e domínio, amplia o raio de falha e
viola a propriedade de dados de cada projeto.

### Chamadas síncronas diretas

Rejeitadas porque timeout, lentidão ou indisponibilidade do SIEM bloqueariam scans e
alertas locais. A integração não pode fazer parte do caminho crítico do Shield.

### Message broker externo neste estágio

Kafka/RabbitMQ continuam opções futuras, mas foram adiados porque adicionariam instalação,
credenciais e operação desproporcionais ao laboratório/portfólio. Outbox/inbox mantém a
semântica necessária agora e permite substituir o transporte depois.

### Reutilizar rotas genéricas/de demonstração

Rejeitado porque essas rotas não oferecem contrato M2M scoped, inbox durável ou
idempotência de produtor e podem mudar com o fluxo interno do SOC.

## Critério "daqui a um ano"

Uma nova versão do Shield ou uma nova fonte deve integrar-se por contrato versionado,
credencial própria e adapter, sem acessar o banco do SIEM nem bloquear sua operação local.
Trocar HTTP por broker ou SQLite por outro storage não deve alterar o evento v1 nem os
engines analíticos.
