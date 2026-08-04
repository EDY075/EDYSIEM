# EDY SIEM — Relatório do Sprint 2.5 (Correlation Engine Framework)

**Data:** 03/08/2026
**Produto:** EDY SIEM — Security Information and Event Management
**Escopo:** Framework de Correlação desacoplado e extensível (sem regras reais de produção)
**Fora de escopo:** Regras de correlação reais (brute force, impossible travel, beaconing) — sprints futuras
**Status:** ✅ CONCLUÍDO — pipeline de qualidade 100% verde

---

## 1. Arquivos Criados

### Pacote `src/edysiem/correlation/` (7 módulos + plugins)

| Módulo | Responsabilidade |
|---|---|
| `__init__.py` | API pública (15 símbolos) |
| `base.py` | `CorrelationRule` (Protocol), `CorrelationMetadata`, `CorrelationPriority`, `CorrelationMatch`, `CorrelationReason`, `CorrelationDecision` |
| `registry.py` | `CorrelationRegistry` — descoberta, registro, ordenação topológica por prioridade + dependências, detecção de ciclos |
| `engine.py` | `CorrelationEngine` + `CorrelationMetrics` — execução por prioridade, isolamento de falhas, timeout, métricas |
| `context.py` | `CorrelationContext` — janelas temporais por `(rule_id, identity_key)` com TTL |
| `models.py` | `CorrelationResult`, `CorrelatedEvent`, `CorrelationMetrics` |
| `exceptions.py` | Hierarquia de erros do framework |
| `plugins/__init__.py` | Exports oficiais |
| `plugins/demo.py` | **Regra DEMO**: `ThresholdByIpRule` |
| `plugins/README.md` | Guia de desenvolvimento de regras |

### Testes — 5 arquivos, +74 casos

`test_correlation_base.py`, `test_correlation_context.py`, `test_correlation_registry.py`,
`test_correlation_engine.py`, `test_correlation_plugins_demo.py`, `test_correlation_coverage.py`

---

## 2. Arquitetura

```
EnrichedEvent
    ↓
[CorrelationRegistry] → regras ordenadas por prioridade + dependências
    ↓
[CorrelationEngine] → executa cada regra (timeout + isolamento de falhas)
    ↓
[CorrelationContext] → janelas temporais por (regra, chave de identidade)
    ↓
CorrelatedEvent (imutável, matches agregados) → Detection Engine
```

### Modelos principais

| Modelo | Descrição |
|---|---|
| `CorrelationRule` | Protocol: `metadata` + `setup`/`evaluate`/`shutdown` |
| `CorrelationMetadata` | id, name, version, priority, author, required_fields, required_event_types, window_seconds, dependencies, enabled_by_default, timeout_seconds |
| `CorrelationContext` | Estado de janela temporal (buffers por regra + chave, TTL, thread-safe) |
| `CorrelationResult` | Decisão (MATCH/NO_MATCH/DEFERRED) + matches + erro + duração |
| `CorrelationMatch` | rule_id, matched_event_ids, reason (estruturado), severity, tags |
| `CorrelatedEvent` | Evento correlacionado para a Detection |
| `CorrelationMetrics` | tempo, matches, falhas, timeout, cache/estado, execuções |

---

## 3. Regra DEMO

**`ThresholdByIpRule`** — "Mesmo IP gerou mais de N eventos em X minutos."

- `required_fields = {"ip_src"}`
- `window_seconds` configurável (default 300s)
- `threshold` configurável (default 5)
- Usa `CorrelationContext` para acumular eventos por `(rule_id, ip_src)` na janela
- Retorna `MATCH` quando `count >= threshold`, senão `DEFERRED`

Validada em testes diretos e no fluxo completo do `CorrelationEngine`.

---

## 4. Decisões de Design Relevantes

1. **Regras declarativas, sem hardcode**: cada regra informa via `CorrelationMetadata` o que exige (campos, tipos de evento, janela, prioridade) — o engine decide.
2. **Ordenação topológica (Kahn)**: prioridade como tiebreaker, dependências resolvidas automaticamente, ciclos detectados via DFS.
3. **Janelas temporais no contexto**: `CorrelationContext` mantém buffers por `(rule_id, identity_key)` com expiração lazy e robustez a inserções fora de ordem.
4. **Isolamento de falhas**: regra que falha ou excede timeout NÃO interrompe o pipeline; falha logada + métrica.
5. **Timeout por regra**: `metadata.timeout_seconds` (0 = default do engine, 5s).
6. **Filtro de campos**: o engine pula regras cujos `required_fields` estão ausentes no evento.
7. **Imutabilidade preservada**: regras recebem `EnrichedEvent` e nunca o mutam.

---

## 5. Qualidade

| Métrica | Alvo | Resultado | Status |
|---------|------|-----------|--------|
| Testes | — | **435 passando** (2.44s) | ✅ |
| Cobertura | ≥ 95% | **95.19%** | ✅ |
| mypy strict | 0 erros | **0 erros (62 arquivos)** | ✅ |
| ruff check | 0 avisos | **All checks passed** | ✅ |
| ruff format | ok | **100 arquivos formatados** | ✅ |

---

## 6. Próxima Sprint

**Sprint 2.6 — Detection Engine**: regras reais de detecção + MITRE + Alert generation
sobre o Correlation Engine:
- `DetectionRule` (Protocol) + metadata com MITRE
- `Alert` generation com dedupe por fingerprint
- Regras iniciais (brute force, impossible travel, beaconing)
- Testes de integração pipeline → correlation → detection

---

## 7. Como Executar

```powershell
cd C:\Users\edmil\EDYSIEM
$env:PYTHONPATH = "$PWD\src"
python -m pytest -q                # testes + cobertura
python -m mypy                     # type check strict
python -m ruff check src tests     # lint
python -m ruff format --check src tests
```

> Relatório gerado pelo TITAN AI SQUAD (jr + VULCAN + QA)
