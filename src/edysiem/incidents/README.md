# Incident Engine Enterprise — EDY SIEM

Camada responsavel por agrupar Alertas relacionados em um Incidente de seguranca.
Sem Case Management ainda, sem Dashboard - somente arquitetura.

## Fluxo

```
Detection -> Risk -> Alert -> Incident Engine -> Incident

Alertas (múltiplos)
    -> Correlator (grouping: asset/user/ioc/rule/fingerprint/janela/MITRE)
    -> Builder (agrega alertas em um Incident)
    -> Dedup (fingerprint)
    -> Lifecycle (OPEN -> TRIAGE -> INVESTIGATING -> CONTAINED -> RESOLVED -> CLOSED -> REOPENED)
    -> Incident
```

## Componentes

| Componente | Responsabilidade |
|---|---|
| `GroupingEngine` | Agrupa alertas com base em criterios configuraveis (`GroupingConfig`) |
| `IncidentCorrelator` | Decide se alertas formam um incidente (NEW/DEDUP/NO_GROUP) |
| `IncidentBuilder` | Recebe multiplos `Alert` e produz um unico `Incident` (agregacao) |
| `IncidentLifecycleManager` | Transicoes de estado (OPEN->TRIAGE->INVESTIGATING->CONTAINED->RESOLVED->CLOSED->REOPENED) |
| `IncidentEngine` | Orquestra correlacao -> builder -> dedup -> lifecycle |
| `IncidentRegistry` | Hooks de ciclo de vida (on_created, on_updated, on_status_changed, on_reopened) |
| `IncidentContext` | Armazenamento in-memory + indice de fingerprints |

## Modelo Incident

```python
Incident(
    id,
    title,
    description,
    severity,
    priority,
    risk_score,
    confidence,
    status,
    first_seen,
    last_seen,
    closed_at,
    occurrences,
    alerts,
    assets,
    users,
    iocs,
    mitre,
    tactics,
    techniques,
    tags,
    timeline,
    owner,
    fingerprint,
    reason,
    evidence,
)
```

## Criterios de agrupamento (configuraveis)

| Criterio | Peso | Descricao |
|---|---|---|
| ASSET | 20 | Mesmo asset |
| USER | 20 | Mesmo usuario |
| IOC | 25 | Mesmo IOC |
| RULE | 15 | Mesma regra |
| FINGERPRINT | 30 | Mesmo fingerprint de alerta |
| TIME_WINDOW | 10 | Dentro da janela temporal |
| MITRE | 20 | Mesma referencia MITRE |

A pontuacao e a soma dos pesos normalizada para 0-100. O grupo forma um
incidente se `score >= min_score` (padrao 50). Tudo configuravel via
`GroupingConfig` (criterios ativos, janela temporal, pontuacao minima, chave).

## Uso

```python
from edysiem.incidents import IncidentEngine, GroupingConfig, GroupingEngine
from edysiem.incidents import IncidentCorrelator, IncidentContext, IncidentRegistry

context = IncidentContext()
engine = IncidentEngine(
    correlator=IncidentCorrelator(GroupingEngine(GroupingConfig(min_score=40)), context),
    registry=IncidentRegistry(),
    context=context,
)

# Processar N alertas de brute force -> 1 incidente
result = await engine.process_alerts(alerts)
if result.kind.value == "created":
    print("Incidente criado:", result.incident.title)

# Transicao de estado
engine.transition(result.incident, IncidentStatus.TRIAGE, actor="analyst-01")
```

## Ciclo de vida

```
OPEN -> TRIAGE -> INVESTIGATING -> CONTAINED -> RESOLVED -> CLOSED
  ^                                  ^                         |
  |__________________________________|_________________________|
                    REOPENED (reabrir fechado)
```

Transicoes invalidas levantam `IncidentInvalidStateTransition`.

## Algoritmo DEMO

**"Cinco Alertas de Brute Force -> Um unico Incidente."**

Com `GroupingConfig` padrao (RULE + TIME_WINDOW ativos), 5 alertas com a
mesma `rule_id` dentro da janela temporal atingem a pontuacao minima e
formam um unico incidente. Ver testes em `tests/test_incidents_*`.

## Fora de escopo (sprints futuras)

- Case Management (investigacao, notas, atribuicao)
- Dashboard
- Persistencia externa do IncidentContext
