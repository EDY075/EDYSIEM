# Alert Engine Enterprise — EDY SIEM

Camada responsavel pelo ciclo de vida completo de um alerta SOC.

## Fluxo

```
DetectionFinding
    -> Risk Evaluation (RiskEngine)
    -> Fingerprint (FingerprintEngine)
    -> Alert Builder (AlertBuilder)
    -> Deduplication (DedupEngine)
    -> Alert Lifecycle (LifecycleManager)
    -> Alert
```

## Componentes

| Componente | Responsabilidade |
|---|---|
| `RiskEngine` | Calcula `risk_score` (0-100) a partir de fatores (severidade, confianca, asset criticality, intel) |
| `FingerprintEngine` | Hash SHA-256 deterministico de campos-chave (rule_id + identidade) |
| `AlertBuilder` | Transforma `DetectionFinding` em `Alert` (risco + fingerprint + timeline) |
| `DedupEngine` | Se o fingerprint ja existir, incrementa `occurrences` e atualiza `last_seen` |
| `LifecycleManager` | Transicoes de estado (OPEN -> TRIAGE -> INVESTIGATING -> RESOLVED/FALSE_POSITIVE) |
| `AlertRegistry` | Hooks de ciclo de vida (on_created, on_updated, on_status_changed) |
| `AlertContext` | Armazenamento in-memory + indice de fingerprints |

## Modelo Alert

```python
Alert(
    id,
    title,
    description,
    severity,
    priority,
    risk_score,
    confidence,
    first_seen,
    last_seen,
    occurrences,
    status,
    source,
    rule_id,
    mitre,
    asset_id,
    user,
    ioc_ids,
    tags,
    timeline,
    fingerprint,
    event_ids,
)
```

## Uso

```python
from edysiem.alerts import AlertEngine, AlertBuilder, RiskEngine, FingerprintEngine
from edysiem.alerts import DedupEngine, AlertContext, AlertRegistry, LifecycleManager

context = AlertContext()
engine = AlertEngine(
    builder=AlertBuilder(FingerprintEngine(), RiskEngine()),
    dedupe=DedupEngine(context),
    registry=AlertRegistry(),
    context=context,
)

# Processar um DetectionFinding
result = await engine.process_finding(finding, source_event)
if result.was_new:
    print("Alerta criado:", result.alert.id)
else:
    print("Alerta deduplicado, occurrences:", result.alert.occurrences)

# Transicao de estado
engine.transition(result.alert, AlertLifecycle.TRIAGE, actor="analyst-01")
```

## Fingerprint deterministico

- Campos de identidade padrao: `rule_id`, `ip_src`, `ip_dst`, `user`, `source_host`
- Serializacao canonica (chaves ordenadas, separadores estaveis)
- Mesmo evento -> mesmo fingerprint

## Deduplicacao

- `AlertContext` guarda `fingerprint_hash -> alert_id`
- Se o fingerprint ja existe: `occurrences += 1`, `last_seen` atualizado
- Nenhum alerta duplicado e criado

## Ciclo de vida

```
OPEN -> TRIAGE -> INVESTIGATING -> RESOLVED
                        \-> FALSE_POSITIVE
RESOLVED -> OPEN (reabrir)
FALSE_POSITIVE -> OPEN (reabrir)
```

Transicoes invalidas levantam `AlertInvalidStateTransition`.

## Fora de escopo (sprints futuras)

- Persistencia externa (SQLite) do AlertContext
- Cases/Incidents
- Dashboard
- Notificacoes reais
