# EDY SIEM — Logging Design

> Projeto do sistema de logging (implementação na Sprint 1). Estrutura JSON central.
> Base: ADR-006 (log estruturado JSON + trace_id).

## 1. Categorias de log

| Categoria | Finalidade | Exemplos |
|---|---|---|
| **Application Log** | funcionamento do app | pipeline iniciado, etapa executada |
| **Audit Log** | trilha de ações do usuário | criar regra, ACK alerta, mudar status |
| **Security Log** | eventos de segurança da plataforma | login, acesso negado, auth falha |
| **Access Log** | requisições HTTP | método, rota, status, latência |
| **Debug Log** | diagnóstico detalhado (dev) | payload de parsing, decisões internas |
| **Error Log** | falhas (com stack + trace_id) | exceção não tratada, storage down |

## 2. Estrutura JSON (formato comum)

```json
{
  "ts": "2026-08-03T14:02:11.123Z",
  "level": "INFO",
  "logger": "app.pipeline.normalization",
  "trace_id": "tr_abc123",
  "event_id": "evt_...",
  "category": "application",
  "message": "evento normalizado",
  "context": {"source_type": "syslog", "source_host": "web-01"}
}
```

Campos obrigatórios: `ts, level, logger, trace_id, message`.
`category`: application|audit|security|access|debug|error.
`context`: objeto com dados relevantes (nunca secrets).

## 3. Implementação (planejada)

- `app/core/logging/` — formatter JSON + logger factory.
- `trace_id` propagado via contexto (pipeline) e injetado nos logs.
- Níveis: DEBUG/INFO/WARNING/ERROR/CRITICAL.
- Configuração via env (`EDYSIEM_LOG_LEVEL`, `EDYSIEM_LOG_JSON`).
- Saída: console (dev) / arquivo rotativo (prod).

## 4. Audit Log (obrigatório)

Toda ação de usuário importante gera Audit Log:
```json
{
  "category": "audit",
  "actor": "analyst",
  "action": "alert.ack",
  "target": "alt_...",
  "details": {"note": "validando"},
  "trace_id": "tr_..."
}
```

Persistido em `audit_log` (ver DATABASE_DESIGN.md) **e** logado.

## 5. Regras

- Nunca logar secrets/credenciais/payloads sensíveis.
- Payloads grandes truncados (max ~4KB por campo).
- `trace_id` obrigatório em logs de pipeline.
- Erros logam com stack (error level) + referência ao contexto.
- Debug apenas quando `EDYSIEM_LOG_LEVEL=DEBUG`.

## 6. Saúde/observabilidade

- Métricas simples (contadores por etapa) expostas no `/health`.
- Log de erro com alerta potencial (dashboard de operação futuro).
