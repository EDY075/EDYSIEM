# EDY SIEM — Relatório do Sprint 2.8 (Incident Engine Enterprise)

**Data:** 03/08/2026
**Produto:** EDY SIEM — Security Information and Event Management
**Escopo:** Camada de agrupamento de Alertas em Incidentes de segurança
**Fora de escopo:** Case Management, Dashboard, notificações reais — sprints futuras
**Status:** ✅ CONCLUÍDO — pipeline de qualidade 100% verde

---

## 1. Arquivos Criados

### Pacote `src/edysiem/incidents/` (12 módulos)

| Módulo | Responsabilidade |
|---|---|
| `__init__.py` | API pública |
| `models.py` | `Incident`, `IncidentStatus`, `IncidentSeverity`, `IncidentPriority`, `IncidentFingerprint`, `IncidentEvidence`, `IncidentReason`, `IncidentMetrics`, `IncidentTimelineEntry` |
| `grouping.py` | `GroupingConfig` + `GroupingEngine` + `IncidentGroup` — critérios configuráveis |
| `correlator.py` | `IncidentCorrelator` — decisão NEW/DEDUP/NO_GROUP |
| `builder.py` | `IncidentBuilder` — agrega múltiplos Alert em um Incident |
| `lifecycle.py` | `IncidentLifecycleManager` — transições validadas |
| `engine.py` | `IncidentEngine` — orquestração |
| `registry.py` | Hooks on_created/on_updated/on_status_changed/on_reopened |
| `context.py` | `IncidentContext` — storage + índice de fingerprints |
| `base.py` | `IncidentProcessor` (Protocol) |
| `exceptions.py` | Hierarquia de erros |
| `README.md` | Documentação |

### Testes — 4 arquivos, +56 casos

`test_incidents_models.py`, `test_incidents_grouping.py`, `test_incidents_engine.py`, `test_incidents_coverage.py`

---

## 2. Arquitetura

```
Detection -> Risk -> Alert -> Incident Engine -> Incident

Alertas (múltiplos)
    -> Correlator (GroupingEngine: asset/user/ioc/rule/fingerprint/janela/MITRE)
    -> Builder (agrega alertas em um Incident)
    -> Dedup (fingerprint)
    -> Lifecycle (OPEN->TRIAGE->INVESTIGATING->CONTAINED->RESOLVED->CLOSED->REOPENED)
    -> Incident
```

### Modelo Incident

```python
Incident(
    id, title, description,
    severity, priority, risk_score, confidence,
    status, first_seen, last_seen, closed_at,
    occurrences, alerts, assets, users, iocs,
    mitre, tactics, techniques, tags,
    timeline, owner, fingerprint, reason, evidence
)
```

### Critérios de agrupamento (configuráveis — nada hardcoded)

| Critério | Peso | Descrição |
|---|---|---|
| ASSET | 20 | Mesmo asset |
| USER | 20 | Mesmo usuário |
| IOC | 25 | Mesmo IOC |
| RULE | 20 | Mesma regra |
| FINGERPRINT | 30 | Mesmo fingerprint de alerta |
| TIME_WINDOW | 10 | Dentro da janela temporal |
| MITRE | 20 | Mesma referência MITRE |

Pontuação = soma dos pesos normalizada 0-100; grupo forma incidente se `score >= min_score` (default 40). Tudo configurável via `GroupingConfig`.

### Ciclo de vida

```
OPEN -> TRIAGE -> INVESTIGATING -> CONTAINED -> RESOLVED -> CLOSED
  ^                                          ^          |
  |__________________________________________|__________|
                     REOPENED (reabrir)
```

---

## 3. Componentes Implementados

| Componente | Comportamento |
|---|---|
| **GroupingEngine** | Verifica critérios ativos; pontuação ponderada; fingerprint determinístico por chave (`group_by`) |
| **IncidentCorrelator** | NEW (cria), DEDUP (occurrences+1), NO_GROUP (abaixo do min_score) |
| **IncidentBuilder** | Agrega severidade máxima, união de assets/users/iocs/mitre, média de risco/confiança, evidências |
| **LifecycleManager** | Valida transições; CLOSED seta closed_at; REOPENED registrado |
| **IncidentEngine** | Orquestra correlator → builder → dedup → lifecycle; métricas |

---

## 4. Algoritmo DEMO

**"Cinco Alertas de Brute Force → Um único Incidente."**

Com `GroupingConfig` padrão, 5 alertas com mesma `rule_id` + asset + user dentro da janela atingem `score >= 40` e formam um único incidente. Validado em testes diretos e no fluxo completo do `IncidentEngine`.

---

## 5. Qualidade

| Métrica | Alvo | Resultado | Status |
|---------|------|-----------|--------|
| Testes | — | **646 passando** (2.94s) | ✅ |
| Cobertura | ≥ 95% | **95.09%** | ✅ |
| mypy strict | 0 erros | **0 erros (96 arquivos)** | ✅ |
| ruff check | 0 avisos | **All checks passed** | ✅ |
| ruff format | ok | **152 arquivos formatados** | ✅ |

---

## 6. Próxima Sprint

**Sprint 2.9 — Case Management + Dashboard v0**:
- Investigação (timeline, notas, atribuição)
- Dashboard executivo (KPIs, alertas críticos)
- Persistência externa (SQLite)

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
