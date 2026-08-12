# EDY Shield → EDY SIEM — Contrato Oficial de Eventos v1

**Status:** aprovado para implementação

**Versão do schema:** `1.0`

**Endpoint:** `POST /api/v1/ingestion/sources/edy-shield/events`

**Atualizado em:** 2026-08-11

Este documento é a fonte normativa do contrato entre o produtor EDY Shield e o
consumidor EDY SIEM. Em caso de divergência com exemplos ou documentos anteriores,
este contrato prevalece.

## 1. Escopo e princípios

- O Shield continua operando, escaneando e alertando localmente sem conexão com o SIEM.
- Os projetos não compartilham banco, modelos de runtime nem diretórios de dados.
- O transporte oferece entrega **at-least-once**; a inbox do SIEM oferece processamento
  **exactly-once lógico** por idempotência.
- O evento descreve um fato já ocorrido no endpoint. O SIEM decide a classificação,
  correlação, alerta, incidente e caso finais.
- O payload original validado é preservado para investigação e reprocessamento.
- Dados opcionais desconhecidos ou não aplicáveis são omitidos, nunca enviados como
  `null`.

## 2. Envelope HTTP do lote

```json
{
  "batch_id": "a65c942d-6aa7-4b1a-9bb2-f04546bcb540",
  "sent_at": "2026-08-11T18:42:15.120Z",
  "events": []
}
```

| Campo | Tipo | Obrigatório | Regra |
|---|---|---:|---|
| `batch_id` | string UUID v4 | sim | Novo por lote; reutilizado somente ao repetir o mesmo corpo |
| `sent_at` | string RFC 3339 UTC | sim | Instante de montagem do lote, terminado em `Z` |
| `events` | array | sim | Entre 1 e 100 eventos |

O lote não carrega `schema_version`: cada evento declara sua versão. Isso permite uma
transição controlada entre versões menores no mesmo transporte. Na primeira release,
somente `1.0` é aceita.

## 3. Schema canônico do evento

```json
{
  "event_id": "7a4ec1d2-3b61-4e9c-8f12-2b9a6e1d4501",
  "schema_version": "1.0",
  "timestamp": "2026-08-11T18:42:10.123Z",
  "sequence": 184,
  "source": {
    "product": "edy-shield",
    "product_version": "2.2.0",
    "instance_id": "9df3e3b7-f905-49f8-b6a7-3da64227e3d1",
    "component": "fim"
  },
  "event_type": "shield.fim.file.modified",
  "severity": "high",
  "asset": {
    "asset_id": "shield:9df3e3b7-f905-49f8-b6a7-3da64227e3d1:ws-fin-01",
    "hostname": "ws-fin-01",
    "ip": "192.168.10.25",
    "os": "Windows 11 Pro 24H2"
  },
  "evidence": {
    "file_path": "Windows/System32/drivers/etc/hosts",
    "hash_algorithm": "sha256",
    "previous_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "current_hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "baseline_id": "fim-sha256-20260811-001",
    "baseline_status": "modified",
    "scan_id": "scan-20260811-1842",
    "file_size_bytes": 824,
    "mtime": "2026-08-11T18:42:08.901Z",
    "details": {}
  },
  "metadata": {
    "correlation_id": "scan-20260811-1842",
    "tags": ["fim", "file-change"]
  }
}
```

### 3.1 Campos raiz

| Campo | Tipo | Obrigatório | Validação |
|---|---|---:|---|
| `event_id` | string UUID v4 | sim | Forma canônica minúscula; gerado uma vez e preservado em todos os retries |
| `schema_version` | string | sim | Exatamente `1.0` nesta versão |
| `timestamp` | string | sim | RFC 3339, UTC, terminado em `Z` |
| `sequence` | inteiro | sim | `>= 1`, monotônico por `source.instance_id`; gaps são permitidos |
| `source` | objeto | sim | Identidade imutável do produtor |
| `event_type` | enum | sim | Um dos tipos da seção 4 |
| `severity` | enum | sim | Um dos níveis da seção 5 |
| `asset` | objeto | sim | Endpoint afetado |
| `evidence` | objeto | sim | Evidência específica; regras condicionais na seção 6 |
| `metadata` | objeto | sim | Contexto não probatório; pode ser `{}` |

Campos raiz desconhecidos são rejeitados. Strings têm espaços externos removidos antes
da validação somente no produtor; o SIEM não deve corrigir silenciosamente payloads.

### 3.2 `source`

| Campo | Tipo | Obrigatório | Validação |
|---|---|---:|---|
| `product` | string constante | sim | `edy-shield` |
| `product_version` | string | sim | SemVer, máximo 32 caracteres |
| `instance_id` | string UUID | sim | Forma canônica minúscula; criado na instalação e persistente entre reinícios |
| `component` | enum | sim | `fim`, `hash_checker`, `scanner` ou `alert_engine` |

O `instance_id` muda apenas após reinstalação/reset explícito. Hostname não identifica o
produtor porque pode mudar ou se repetir em redes diferentes.

### 3.3 `asset`

| Campo | Tipo | Obrigatório | Validação |
|---|---|---:|---|
| `asset_id` | string | sim | Estável, 1–255 caracteres; formato recomendado `shield:<instance_id>:<hostname>` |
| `hostname` | string | sim | 1–255 caracteres |
| `ip` | string | não | IPv4 ou IPv6 válido; omitir quando indisponível |
| `os` | string | não | Nome/versão sanitizados, máximo 255 caracteres |

### 3.4 `evidence`

| Campo | Tipo | Obrigatório global | Validação |
|---|---|---:|---|
| `file_path` | string | não | Caminho lógico relativo à raiz monitorada, máximo 4096 caracteres |
| `hash_algorithm` | enum | não | `md5`, `sha1`, `sha256` ou `sha512` |
| `previous_hash` | string hexadecimal | não | Tamanho deve corresponder ao algoritmo |
| `current_hash` | string hexadecimal | não | Tamanho deve corresponder ao algoritmo |
| `baseline_id` | string | não | 1–255 caracteres |
| `baseline_status` | enum | não | `not_applicable`, `created`, `matched`, `added`, `modified`, `removed` ou `invalid` |
| `scan_id` | string | não | 1–255 caracteres |
| `file_size_bytes` | inteiro | não | `>= 0` |
| `mtime` | string | não | RFC 3339 UTC terminado em `Z` |
| `details` | objeto | sim | Objeto limitado, pode ser `{}` |

O SIEM aceita hashes MD5/SHA-1 para representar telemetria legada, mas não os considera
prova criptográfica forte. O Shield deve preferir SHA-256. Paths devem ser relativos à
raiz monitorada, usar `/` como separador e não conter drive, raiz, segmento vazio, `.` ou
`..`: não exportar nome de usuário ou raiz local quando isso não for necessário.

### 3.5 `metadata`

O objeto é obrigatório, mas suas chaves são opcionais. Chaves conhecidas:

| Campo | Tipo | Uso |
|---|---|---|
| `correlation_id` | string | Agrupa eventos do mesmo scan/operação |
| `tags` | array de strings | Busca e classificação; no máximo 32 tags |
| `shield_alert_id` | string | Referência ao alerta local, sem impor alerta no SIEM |
| `rule_id` | string | Regra local que produziu o alerta |
| `dedup_fingerprint` | string | Fingerprint local informativo; não substitui `event_id` |

Extensões experimentais devem usar prefixo `x_`, por exemplo `x_lab_scenario`. Nenhum
campo pode conter token, credencial, conteúdo integral de arquivo ou dado pessoal não
necessário à investigação.

## 4. Enum oficial de `event_type`

| Valor | Significado |
|---|---|
| `shield.fim.baseline.created` | Baseline FIM criada/persistida |
| `shield.fim.scan.completed` | Comparação FIM concluída, com totais |
| `shield.fim.file.added` | Arquivo ausente na baseline apareceu |
| `shield.fim.file.modified` | Arquivo presente teve conteúdo/metadados alterados |
| `shield.fim.file.removed` | Arquivo da baseline não está mais presente |
| `shield.hash.verified` | Hash calculado correspondeu ao esperado |
| `shield.hash.mismatch` | Hash calculado divergiu do esperado |
| `shield.alert.created` | Alerta local foi criado |
| `shield.alert.updated` | Estado de alerta local foi alterado |

Novos tipos exigem versão menor nova do contrato ou nova versão major se alterarem
semântica existente. O SIEM rejeita tipos desconhecidos em `1.0`; não os converte para
um tipo genérico silenciosamente.

## 5. Enum oficial de `severity`

| Valor | Intenção do produtor |
|---|---|
| `info` | Evento operacional sem indício de ameaça |
| `low` | Mudança de baixo risco ou contexto auxiliar |
| `medium` | Mudança relevante que merece triagem |
| `high` | Forte desvio, alvo sensível ou alerta local importante |
| `critical` | Comprometimento provável ou impacto imediato |

Os valores são minúsculos. O SIEM preserva essa severidade como `source_severity`, mas
pode recalcular a severidade analítica após enriquecimento e correlação.

## 6. Validação condicional por tipo

| `event_type` | Requisitos adicionais em `evidence` |
|---|---|
| `shield.fim.baseline.created` | `baseline_id`, `hash_algorithm`, `baseline_status=created`; `details.file_count` |
| `shield.fim.scan.completed` | `scan_id`, `baseline_id`; `details.added`, `modified`, `removed`, `unchanged`, `ignored`, `duration_ms` como inteiros `>= 0` |
| `shield.fim.file.added` | `file_path`, `current_hash`, `hash_algorithm`, `baseline_id`, `scan_id`, `baseline_status=added` |
| `shield.fim.file.modified` | `file_path`, `previous_hash`, `current_hash`, `hash_algorithm`, `baseline_id`, `scan_id`, `baseline_status=modified` |
| `shield.fim.file.removed` | `file_path`, `previous_hash`, `hash_algorithm`, `baseline_id`, `scan_id`, `baseline_status=removed`; proíbe `current_hash` |
| `shield.hash.verified` | `file_path`, `previous_hash` (esperado), `current_hash` (calculado), `hash_algorithm`, `baseline_status=matched` |
| `shield.hash.mismatch` | `file_path`, `previous_hash` (esperado), `current_hash` (calculado), `hash_algorithm`; `baseline_status=modified` ou `not_applicable` |
| `shield.alert.created` | `metadata.shield_alert_id`, `metadata.rule_id`; `details.title` e `details.description` |
| `shield.alert.updated` | `metadata.shield_alert_id`; `details.previous_status` e `details.current_status` |

Regras gerais:

- UUIDs usam a representação canônica minúscula com hífens.
- `previous_hash` e `current_hash` usam hex minúsculo.
- Hashes têm 32/40/64/128 caracteres para MD5/SHA-1/SHA-256/SHA-512.
- Para alteração, os hashes anterior e atual não podem ser iguais.
- Campos opcionais devem ser omitidos quando desconhecidos ou não aplicáveis. `null` é
  inválido em v1.
- Chaves desconhecidas são proibidas na raiz, em `source` e em `asset`; são permitidas
  somente em `evidence.details` e `metadata`, respeitando limites.

## 7. Timestamps e ordenação

- `timestamp` representa quando o fato ocorreu no endpoint; `sent_at`, quando o lote foi
  montado; `received_at` é criado exclusivamente pelo SIEM.
- Shield emite UTC RFC 3339 terminado em `Z`, com milissegundos recomendados.
- O SIEM rejeita timestamps mais de 5 minutos no futuro em relação ao seu relógio.
- Eventos antigos continuam válidos: indisponibilidade prolongada não causa expiração.
- `sequence` é monotônico por instância, mas gaps e chegada fora de ordem são válidos.
- Correlação temporal usa `timestamp`; métricas de atraso usam `received_at - timestamp`.

## 8. Limites do payload

| Limite | Valor v1 |
|---|---:|
| Corpo HTTP descompactado | 1 MiB |
| Eventos por lote | 1–100 |
| Evento serializado em UTF-8 | 64 KiB |
| `evidence.details` serializado | 16 KiB e 32 chaves |
| `metadata` serializado | 16 KiB e 32 chaves |
| Profundidade de objetos de extensão | 4 níveis |
| String genérica | 1024 caracteres |
| `file_path` | 4096 caracteres |
| Tags | 32 itens de até 64 caracteres |

Compressão HTTP não faz parte de v1. Conteúdo de arquivo, stack trace integral e binários
devem ser armazenados localmente ou em um mecanismo futuro de artefatos, nunca embutidos.
Números em extensões devem ser valores JSON finitos; `NaN`, `Infinity` e `-Infinity` são
inválidos.

## 9. Endpoint de ingestão v1

### 9.1 Requisição

```http
POST /api/v1/ingestion/sources/edy-shield/events HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json
Idempotency-Key: a65c942d-6aa7-4b1a-9bb2-f04546bcb540
```

`Idempotency-Key` é obrigatório e deve ser idêntico a `batch_id`.

### 9.2 Resposta de lote aceita

```json
{
  "batch_id": "a65c942d-6aa7-4b1a-9bb2-f04546bcb540",
  "accepted_count": 1,
  "duplicate_count": 1,
  "rejected_count": 1,
  "results": [
    {
      "event_id": "7a4ec1d2-3b61-4e9c-8f12-2b9a6e1d4501",
      "status": "accepted"
    },
    {
      "event_id": "7a4ec1d2-3b61-4e9c-8f12-2b9a6e1d4502",
      "status": "duplicate"
    },
    {
      "event_id": "7a4ec1d2-3b61-4e9c-8f12-2b9a6e1d4503",
      "status": "rejected",
      "error": {
        "code": "invalid_hash_length",
        "field": "evidence.current_hash",
        "message": "sha256 requires 64 hexadecimal characters"
      }
    }
  ]
}
```

Status HTTP:

| Status | Uso |
|---:|---|
| `202` | Envelope aceito; itens persistidos, duplicados ou rejeitados individualmente |
| `400` | JSON/envelope malformado ou `Idempotency-Key` diferente do `batch_id` |
| `401` | Token ausente ou inválido |
| `403` | Credencial válida sem escopo `ingestion:shield:write` |
| `409` | `batch_id` ou `(instance_id,event_id)` reutilizado com conteúdo diferente |
| `413` | Corpo/lote/evento acima do limite |
| `415` | Tipo de conteúdo diferente de `application/json` |
| `422` | Nenhum item do lote passou na validação de contrato |
| `429` | Limite de ingestão; deve incluir `Retry-After` |
| `503` | Inbox indisponível; nenhum recebimento deve ser confirmado |

O SIEM responde `202` somente depois de persistir os itens aceitos na inbox na mesma
transação. Um item `rejected` não foi aceito e exige correção; `accepted` e `duplicate`
podem ser marcados como entregues no Shield.

## 10. Autenticação máquina-a-máquina

Para laboratório/portfólio, v1 usa Bearer token aleatório de pelo menos 32 bytes, com
escopo fixo `ingestion:shield:write`.

- Shield lê o segredo de `EDY_SIEM_TOKEN`.
- SIEM lê o segredo de `EDYSIEM_SHIELD_INGEST_TOKEN`.
- URL e ativação usam `EDY_SIEM_URL` e `EDY_SIEM_ENABLED` no Shield.
- Nenhum segredo entra em fonte, fixture, banco versionado, screenshot ou log.
- O SIEM compara tokens em tempo constante e a rota não confia em `X-EDY-Role`.
- Logs mostram apenas um identificador não reversível do cliente.
- HTTPS é obrigatório fora de loopback. HTTP só é aceito em `127.0.0.1`/`::1` no modo
  explícito de laboratório.
- Rotação é feita aceitando token atual e anterior por uma janela curta configurável;
  depois o anterior é revogado.

Em evolução futura, múltiplos agentes devem usar credenciais por instalação registradas,
nunca um token global compartilhado. mTLS ou OAuth2 client credentials podem substituir
o token sem mudar o schema do evento.

## 11. Idempotência e duplicação

1. O Shield gera `event_id` antes de gravar a outbox e nunca o troca em retries.
2. A chave única na inbox é `(source.instance_id, event_id)`.
3. O SIEM calcula SHA-256 do JSON canônico do evento: UTF-8, chaves ordenadas e sem
   espaços insignificantes.
4. Mesma chave e mesmo hash retorna `duplicate` sem reprocessamento.
5. Mesma chave e hash diferente retorna `409 idempotency_conflict`, registra auditoria e
   nunca sobrescreve o primeiro evento.
6. `sequence` auxilia ordenação e detecção de gaps, mas não é chave de idempotência.
7. `batch_id`/`Idempotency-Key` repetido com corpo idêntico retorna a mesma resposta;
   com corpo diferente retorna `409`.

## 12. Timeout, retry, backoff e fila local

### 12.1 Transporte

- Timeout de conexão: 2 segundos.
- Timeout total por requisição: 5 segundos.
- Envio ocorre em worker independente; o caminho do scan nunca aguarda rede.
- Batch máximo: 100 eventos, respeitando 1 MiB.

### 12.2 Retry

Retry automático para falha de DNS/conexão/timeout e HTTP `408`, `429`, `500`, `502`,
`503` ou `504`. Backoff por evento/lote:

`delay = random(0, min(300 s, 2^(attempt-1) s))`

Assim, o teto é 5 minutos com full jitter. `Retry-After` em `429`/`503` prevalece, com
teto operacional de 15 minutos. Falhas `400`, `404`, `409`, `413`, `415` e `422` vão
para `dead_letter`. `401`/`403` pausam o conector, preservam a fila e geram erro local
visível; não descartam eventos.

### 12.3 Outbox do Shield

Estados: `pending`, `in_flight`, `sent`, `dead_letter`.

- `in_flight` volta a `pending` após lease expirado ou reinício.
- Pendentes não expiram automaticamente.
- Enviados podem ser purgados após 7 dias; dead letters, após 30 dias e somente com
  contagem/auditoria preservadas.
- Alertas aos 80% do limite local padrão de 50.000 eventos ou 512 MiB.
- No limite rígido, operações do Shield continuam e a integração entra em `degraded`;
  nenhum evento existente é removido silenciosamente. Falhas novas de enqueue são
  contabilizadas em auditoria local e expostas na saúde do conector.
- O worker envia primeiro `critical/high`, depois os mais antigos das demais severidades,
  preservando `sequence` como evidência de ordem original.

## 13. Exemplos JSON válidos

Os exemplos abaixo são objetos de evento; em transporte, devem ser inseridos no array
`events` do envelope da seção 2.

### 13.1 Arquivo modificado

```json
{
  "event_id": "7a4ec1d2-3b61-4e9c-8f12-2b9a6e1d4501",
  "schema_version": "1.0",
  "timestamp": "2026-08-11T18:42:10.123Z",
  "sequence": 184,
  "source": {"product": "edy-shield", "product_version": "2.2.0", "instance_id": "9df3e3b7-f905-49f8-b6a7-3da64227e3d1", "component": "fim"},
  "event_type": "shield.fim.file.modified",
  "severity": "high",
  "asset": {"asset_id": "shield:9df3e3b7-f905-49f8-b6a7-3da64227e3d1:ws-fin-01", "hostname": "ws-fin-01", "ip": "192.168.10.25", "os": "Windows 11 Pro 24H2"},
  "evidence": {"file_path": "Windows/System32/drivers/etc/hosts", "hash_algorithm": "sha256", "previous_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "current_hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", "baseline_id": "fim-sha256-20260811-001", "baseline_status": "modified", "scan_id": "scan-20260811-1842", "file_size_bytes": 824, "mtime": "2026-08-11T18:42:08.901Z", "details": {}},
  "metadata": {"correlation_id": "scan-20260811-1842", "tags": ["fim", "file-change"]}
}
```

### 13.2 Hash alterado/diferente do esperado

```json
{
  "event_id": "8b5fd2e3-4c72-4fad-9013-3cab7f2e5602",
  "schema_version": "1.0",
  "timestamp": "2026-08-11T18:43:00.000Z",
  "sequence": 185,
  "source": {"product": "edy-shield", "product_version": "2.2.0", "instance_id": "9df3e3b7-f905-49f8-b6a7-3da64227e3d1", "component": "hash_checker"},
  "event_type": "shield.hash.mismatch",
  "severity": "critical",
  "asset": {"asset_id": "shield:9df3e3b7-f905-49f8-b6a7-3da64227e3d1:ws-fin-01", "hostname": "ws-fin-01", "ip": "192.168.10.25", "os": "Windows 11 Pro 24H2"},
  "evidence": {"file_path": "Program Files/EDY/app/agent.exe", "hash_algorithm": "sha256", "previous_hash": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", "current_hash": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd", "baseline_status": "not_applicable", "details": {"verification_source": "manual_hash_check"}},
  "metadata": {"correlation_id": "hash-check-20260811-004", "tags": ["hash", "integrity", "mismatch"]}
}
```

### 13.3 Novo arquivo

```json
{
  "event_id": "9c60e3f4-5d83-40be-a124-4dbc803f6703",
  "schema_version": "1.0",
  "timestamp": "2026-08-11T18:44:12.010Z",
  "sequence": 186,
  "source": {"product": "edy-shield", "product_version": "2.2.0", "instance_id": "9df3e3b7-f905-49f8-b6a7-3da64227e3d1", "component": "fim"},
  "event_type": "shield.fim.file.added",
  "severity": "medium",
  "asset": {"asset_id": "shield:9df3e3b7-f905-49f8-b6a7-3da64227e3d1:ws-fin-01", "hostname": "ws-fin-01", "ip": "192.168.10.25", "os": "Windows 11 Pro 24H2"},
  "evidence": {"file_path": "Users/Public/Downloads/update-helper.exe", "hash_algorithm": "sha256", "current_hash": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", "baseline_id": "fim-sha256-20260811-001", "baseline_status": "added", "scan_id": "scan-20260811-1844", "file_size_bytes": 49152, "mtime": "2026-08-11T18:44:07.400Z", "details": {}},
  "metadata": {"correlation_id": "scan-20260811-1844", "tags": ["fim", "new-file"]}
}
```

### 13.4 Arquivo removido

```json
{
  "event_id": "ad71f405-6e94-41cf-b235-5ecd91407804",
  "schema_version": "1.0",
  "timestamp": "2026-08-11T18:45:21.455Z",
  "sequence": 187,
  "source": {"product": "edy-shield", "product_version": "2.2.0", "instance_id": "9df3e3b7-f905-49f8-b6a7-3da64227e3d1", "component": "fim"},
  "event_type": "shield.fim.file.removed",
  "severity": "high",
  "asset": {"asset_id": "shield:9df3e3b7-f905-49f8-b6a7-3da64227e3d1:ws-fin-01", "hostname": "ws-fin-01", "ip": "192.168.10.25", "os": "Windows 11 Pro 24H2"},
  "evidence": {"file_path": "ProgramData/EDY/policies/denylist.json", "hash_algorithm": "sha256", "previous_hash": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff", "baseline_id": "fim-sha256-20260811-001", "baseline_status": "removed", "scan_id": "scan-20260811-1845", "details": {}},
  "metadata": {"correlation_id": "scan-20260811-1845", "tags": ["fim", "file-removed", "policy"]}
}
```

### 13.5 Scan concluído

```json
{
  "event_id": "be82a516-7fa5-42d0-8346-6fde02518905",
  "schema_version": "1.0",
  "timestamp": "2026-08-11T18:46:40.900Z",
  "sequence": 188,
  "source": {"product": "edy-shield", "product_version": "2.2.0", "instance_id": "9df3e3b7-f905-49f8-b6a7-3da64227e3d1", "component": "fim"},
  "event_type": "shield.fim.scan.completed",
  "severity": "info",
  "asset": {"asset_id": "shield:9df3e3b7-f905-49f8-b6a7-3da64227e3d1:ws-fin-01", "hostname": "ws-fin-01", "ip": "192.168.10.25", "os": "Windows 11 Pro 24H2"},
  "evidence": {"baseline_id": "fim-sha256-20260811-001", "baseline_status": "modified", "scan_id": "scan-20260811-1846", "details": {"added": 1, "modified": 1, "removed": 1, "unchanged": 1240, "ignored": 18, "duration_ms": 4873}},
  "metadata": {"correlation_id": "scan-20260811-1846", "tags": ["fim", "scan-summary"]}
}
```

### 13.6 Alerta crítico local

```json
{
  "event_id": "cf93b627-80b6-43e1-9457-70ef13629a06",
  "schema_version": "1.0",
  "timestamp": "2026-08-11T18:47:05.250Z",
  "sequence": 189,
  "source": {"product": "edy-shield", "product_version": "2.2.0", "instance_id": "9df3e3b7-f905-49f8-b6a7-3da64227e3d1", "component": "alert_engine"},
  "event_type": "shield.alert.created",
  "severity": "critical",
  "asset": {"asset_id": "shield:9df3e3b7-f905-49f8-b6a7-3da64227e3d1:ws-fin-01", "hostname": "ws-fin-01", "ip": "192.168.10.25", "os": "Windows 11 Pro 24H2"},
  "evidence": {"file_path": "Windows/System32/drivers/etc/hosts", "hash_algorithm": "sha256", "previous_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "current_hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", "baseline_id": "fim-sha256-20260811-001", "baseline_status": "modified", "scan_id": "scan-20260811-1842", "details": {"title": "Critical system file changed", "description": "Integrity mismatch detected in a protected operating-system file."}},
  "metadata": {"correlation_id": "scan-20260811-1842", "shield_alert_id": "alert-20260811-0007", "rule_id": "fim-critical-path-change", "dedup_fingerprint": "fim:ws-fin-01:hosts:modified", "tags": ["fim", "critical-file", "local-alert"]}
}
```

### 13.7 Baseline criada

O contrato v1 não define `baseline_changed`: uma nova referência persistida é representada
por `shield.fim.baseline.created`; mudanças posteriores aparecem nos eventos de arquivo e
no resumo do scan.

```json
{
  "event_id": "d0a4c738-91c7-44f2-a568-81f02473ab07",
  "schema_version": "1.0",
  "timestamp": "2026-08-11T18:40:00.000Z",
  "sequence": 183,
  "source": {"product": "edy-shield", "product_version": "2.2.0", "instance_id": "9df3e3b7-f905-49f8-b6a7-3da64227e3d1", "component": "fim"},
  "event_type": "shield.fim.baseline.created",
  "severity": "info",
  "asset": {"asset_id": "shield:9df3e3b7-f905-49f8-b6a7-3da64227e3d1:ws-fin-01", "hostname": "ws-fin-01", "ip": "192.168.10.25", "os": "Windows 11 Pro 24H2"},
  "evidence": {"hash_algorithm": "sha256", "baseline_id": "fim-sha256-20260811-001", "baseline_status": "created", "details": {"file_count": 1243, "monitored_root": "system-critical-files"}},
  "metadata": {"correlation_id": "baseline-fim-sha256-20260811-001", "tags": ["fim", "baseline"]}
}
```

## 14. Versionamento e compatibilidade

- Formato: `MAJOR.MINOR`; não há patch de schema.
- Mudança aditiva opcional gera nova versão menor (`1.1`).
- Remoção, renomeação, mudança de tipo/semântica ou novo obrigatório exige endpoint e
  schema major novos (`/api/v2/...`, `2.0`).
- O produtor só envia uma versão anunciada como suportada pelo SIEM.
- Versão não suportada é rejeitada por item com `unsupported_schema_version`.
- O payload raw permanece disponível para reprocessamento após upgrade.
- O contrato não exige pacote Python compartilhado: fixtures JSON e testes de contrato
  são a fronteira comum, evitando acoplamento de release.

## 15. Arquivos planejados para a implementação seguinte

### EDY SIEM

- `docs/architecture/adr/` — ADR de outbox/inbox, contrato e segurança.
- `src/edysiem/api/ingestion_schemas.py` — schemas Pydantic estritos.
- `src/edysiem/api/routes/ingestion.py` — rota v1 e resposta por item.
- `src/edysiem/api/security.py` — dependência de token scoped sem `X-EDY-Role`.
- `src/edysiem/ingestion/inbox.py` — idempotência e persistência durável.
- `src/edysiem/persistence/schema.py` — tabelas de inbox/batches.
- `src/edysiem/parsers/edy_shield.py` — parser do contrato.
- `src/edysiem/normalization/registry.py` — registro do normalizer Shield.
- `tests/test_shield_event_contract_v1.py` e `tests/fixtures/shield_events/v1/` — contrato
  e sete fixtures válidas, além das rejeições representativas.

### EDY Shield

- `app/core/telemetry/` — modelo interno v1 e mapper sem dependência do SIEM.
- `app/services/telemetry_outbox.py` — fila transacional e lease.
- `app/services/siem_transport.py` — batch, timeout, retry e backoff.
- Camada SQLite/configuração — outbox, estado do conector e variáveis de ambiente.
- Testes de `FimDiff`/scan/alerta para cada fixture v1.

Os caminhos novos podem ser ajustados ao padrão do repositório no ADR, sem mudar o
contrato externo definido neste documento.

## 16. Testes planejados

1. Sete fixtures válidas aceitas pelo modelo do consumidor.
2. Campos obrigatórios ausentes, extras proibidos e `null` rejeitados.
3. Todos os enums, UUIDs, IPs, timestamps, SemVer e comprimentos de hash.
4. Regras condicionais por `event_type` e paths/tags nos limites.
5. Lotes vazio, com 100/101 eventos, evento de 64 KiB e corpo de 1 MiB.
6. Token ausente, inválido, correto, rotação e redaction de logs.
7. Reenvio idêntico, duplicação em lote diferente e conflito de conteúdo.
8. Inbox persiste antes do `202`; falha de persistência retorna `503`.
9. Offline, timeout, matriz de retry, full jitter com relógio fake e `Retry-After`.
10. Reinício durante `in_flight`, lease expirado, prioridade e dead letter.
11. Parser/normalizer preserva raw e produz `CanonicalEvent` para todos os tipos.
12. Regressão completa de Shield e SIEM sem conexão entre seus bancos.

O próximo passo, depois de congelar ADR/modelo/fixtures/testes, é implementar somente o
receptor e a inbox da API v1 no SIEM. Transporte e outbox do Shield permanecem posteriores.
