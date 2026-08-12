# EDY SIEM — Relatório do Sprint 2.6 (Rule Engine + Detection Framework)

**Data:** 03/08/2026
**Produto:** EDY SIEM — Security Information and Event Management
**Escopo:** Camada de interpretação de regras de detecção sobre eventos correlacionados
**Fora de escopo:** Regras reais, Sigma, MITRE, Alert generation — sprints futuras
**Status:** ✅ CONCLUÍDO — pipeline de qualidade 100% verde

---

## 1. Arquivos Criados

### Pacote `src/edysiem/detection/` (9 módulos + plugins)

| Módulo | Responsabilidade |
|---|---|
| `__init__.py` | API pública |
| `base.py` | `DetectionRule` (Protocol), `RuleMetadata`, `DetectionPriority`, `DetectionFinding`, `DetectionReason`, `DetectionDecision` |
| `dsl.py` | `RuleCondition`, `RuleExpression`, `RuleOperator`, `RuleLogicalOp` + parser mínimo (`WHEN ... AND ... THEN`) + `evaluate_expression` |
| `registry.py` | `DetectionRegistry` — ordenação topológica por prioridade + dependências, detecção de ciclos |
| `rule_engine.py` | `RuleEngine` + `RuleExecution` — carregar/registrar/validar/executar, isolamento de falhas, timeout, prioridade, métricas |
| `engine.py` | `DetectionEngine` + `DetectionOutcome` + `DetectionSummary` |
| `context.py` | `DetectionContext` — buffers temporais + cache compartilhado |
| `models.py` | `DetectionResult`, `DetectionOutcome`, `DetectionMetrics` |
| `exceptions.py` | Hierarquia de erros |
| `plugins/demo.py` | **Regra DEMO**: `LoginFailuresRule` |
| `plugins/README.md` | Guia de desenvolvimento de regras |

### Testes — 7 arquivos, +103 casos

`test_detection_dsl.py`, `test_detection_dsl_edge.py`, `test_detection_base.py`,
`test_detection_registry.py`, `test_detection_engine.py`, `test_detection_plugins_demo.py`,
`test_detection_coverage.py`

---

## 2. Arquitetura

```
Correlation Engine → CorrelatedEvent
        ↓
[DetectionRegistry] → regras ordenadas por prioridade + dependências
        ↓
[RuleEngine] → carrega/registra/valida/executa DetectionRule (DSL)
        ↓
[DetectionEngine] → produz DetectionOutcome / DetectionDecision
        ↓
(Alert em sprint futura)
```

### Modelos principais

| Modelo | Descrição |
|---|---|
| `DetectionRule` | Protocol: `metadata` + `setup`/`evaluate`/`shutdown` |
| `RuleMetadata` | id, name, version, author, priority, severity, confidence, risk_score, required_fields, dependencies, enabled, tags |
| `RuleCondition` | Condição atômica `field operator value` (EQ/NEQ/GT/GTE/LT/LTE/CONTAINS/IN/MATCHES) |
| `RuleExpression` | Árvore lógica (AND/OR/NOT) de condições/expressões |
| `RuleEngine` | Execução com isolamento de falhas, timeout, prioridade e métricas |
| `DetectionEngine` | Orquestra RuleEngine sobre CorrelatedEvents → `DetectionOutcome` |
| `DetectionResult` | Decisão (DETECTED/NO_DETECTION/DEFERRED) + findings |
| `DetectionMetrics` | execuções, detecções, falhas, timeouts, duração |

---

## 3. DSL (arquitetura preparada para evolução)

```
WHEN
  event.category == authentication
AND
  event.severity >= HIGH
THEN
  raise_alert()
```

- `parse_rule_text()` reconhece a sintaxe básica (WHEN/AND/OR/NOT/THEN)
- `evaluate_expression(expr, values)` avalia contra um mapa field→valor
- Comparação de severidade usa rank ordinal (info<low<medium<high<critical)
- Em sprints futuras o parser evoluirá para Sigma/MITRE sem alterar `RuleExpression`

---

## 4. Regra DEMO

**`LoginFailuresRule`** — "Mais de N falhas de login em X minutos."

- `required_fields = {"source_host"}`
- `threshold` configurável (default 5), `window_seconds` configurável (default 300)
- Detecta eventos `event_category == "auth"` com `event_action in ("reject", "failed")`
- Acumula em `DetectionContext` por `(rule_id, source_host)` e dispara em `count > threshold`
- Produz `DetectionFinding` com severidade, confiança e risco

---

## 5. Qualidade

| Métrica | Alvo | Resultado | Status |
|---------|------|-----------|--------|
| Testes | — | **538 passando** (2.76s) | ✅ |
| Cobertura | ≥ 95% | **95.08%** | ✅ |
| mypy strict | 0 erros | **0 erros (73 arquivos)** | ✅ |
| ruff check | 0 avisos | **All checks passed** | ✅ |
| ruff format | ok | **119 arquivos formatados** | ✅ |

---

## 6. Próxima Sprint

**Sprint 2.7 — Alert Engine**: gerar `Alert` a partir de `DetectionFinding`:
- `AlertFactory` (mapeia finding → domain.Alert)
- Dedupe por fingerprint
- Persistência + notificação
- Testes de integração pipeline → correlation → detection → alert

---

## 7. Como Executar

```powershell
cd C:\Users\user\EDYSIEM
$env:PYTHONPATH = "$PWD\src"
python -m pytest -q                # testes + cobertura
python -m mypy                     # type check strict
python -m ruff check src tests     # lint
python -m ruff format --check src tests
```

> Relatório gerado pelo TITAN AI SQUAD (jr + VULCAN + QA)
