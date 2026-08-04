# Case Engine (Investigation Workspace) — EDY SIEM

Camada operacional utilizada por um Analista SOC para investigar incidentes.
Nao e um CRUD de Cases - e um ambiente de investigacao.

## Fluxo

```
Incident
    -> CaseBuilder (Case a partir do Incident)
    -> Case (workspace)
        -> Timeline Engine (auto-registro append-only)
        -> Evidence Engine (logs/hashes/IPs/domains/arquivos/prints/JSON/IOC/links)
        -> Comment Engine (notas markdown)
        -> Task Engine (criar/concluir/reabrir)
        -> Owner Engine (transferencia de responsavel)
        -> Attachment Engine (anexos)
    -> Resolution
```

## Modelo Case

```python
Case(
    id,
    title,
    description,
    owner,
    status,
    severity,
    priority,
    risk_score,
    created_at,
    updated_at,
    closed_at,
    incident_id,
    alerts,
    assets,
    users,
    iocs,
    mitre,
    timeline,
    comments,
    attachments,
    tasks,
    evidences,
    playbook,
    resolution,
)
```

## Timeline (auto-registro)

O `TimelineEngine` registra automaticamente:
- Case criado (`created`)
- Novo alerta (`alert_added`)
- Mudanca de status (`status_change`)
- Comentario (`comment`)
- Anexo (`attachment`)
- Tarefa (`task`, `task_completed`, `task_reopened`)
- Mudanca de owner (`owner_change`)
- Resolucao (`resolved`)
- Reabertura (`reopened`)

Timeline e **append-only** (imutavel).

## Evidence Engine

Permite anexar evidencias por tipo (`CaseEvidenceKind`):
- `LOG`, `HASH`, `IP`, `DOMAIN`, `FILE`, `SCREENSHOT`, `JSON`, `IOC`, `LINK`

```python
case = await engine.create_from_incident(incident)
case = engine.add_evidence(case.id, CaseEvidenceKind.HASH, "abc123...", label="malware sha256")
case = engine.add_evidence(case.id, CaseEvidenceKind.IP, "1.2.3.4", label="C2")
```

## Task Engine

```python
case = engine.create_task(
    case.id, "Coletar memoria do host-1", priority=CasePriority.P2, assignee="analyst-02"
)
case = engine.complete_task(case.id, task_id)
case = engine.reopen_task(case.id, task_id)
```

## Comment Engine (Notas Markdown)

```python
case = engine.add_comment(case.id, "## Hipotesis\nO host parece comprometido", author="analyst-01")
```

## Owner Engine

```python
case = engine.transfer_owner(case.id, "analyst-02", assigned_by="analyst-01")
```

## Playbook

Estrutura para futuramente executar playbooks automaticos (ainda sem automacao):

```python
from edysiem.cases import Playbook, PlaybookStep

playbook = Playbook(
    name="Isolamento de host comprometido",
    steps=(
        PlaybookStep(order=1, title="Isolar host", description="Desconectar da rede"),
        PlaybookStep(order=2, title="Coletar evidencias", description="Imagem de memoria"),
    ),
)
```

## Ciclo de vida

```
OPEN -> IN_PROGRESS -> ON_HOLD -> RESOLVED -> CLOSED
  ^                                     ^          |
  |_____________________________________|__________|
                    REOPENED (reabrir)
```

Transicoes invalidas levantam `CaseInvalidStateTransition`.

## Metricas

`total_created`, `total_transitions`, `total_comments`, `total_evidences`,
`total_tasks_created`, `total_tasks_completed`, `total_owner_changes`.

## Fora de escopo (sprints futuras)

- Automacao de playbooks
- Dashboard
- Persistencia externa (SQLite)
- Notificacoes reais
