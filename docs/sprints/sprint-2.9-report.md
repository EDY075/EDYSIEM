# EDY SIEM — Relatório do Sprint 2.9 (Investigation Workspace + Case Engine)

**Data:** 03/08/2026
**Produto:** EDY SIEM — Security Information and Event Management
**Escopo:** Workspace operacional do Analista SOC (não um CRUD de Cases)
**Fora de escopo:** Automatização de playbooks, Dashboard, persistência externa — sprints futuras
**Status:** ✅ CONCLUÍDO — pipeline de qualidade 100% verde

---

## 1. Arquivos Criados

### Pacote `src/edysiem/cases/` (14 módulos)

| Módulo | Responsabilidade |
|---|---|
| `models.py` | `Case`, `CaseStatus`, `CaseSeverity`, `CasePriority`, `CaseTimelineEntry`, `CaseEvidence`/`CaseEvidenceKind`, `CaseComment`, `CaseTask`, `CaseAttachment`, `CaseOwner`, `Playbook`/`PlaybookStep`, `CaseMetrics` |
| `timeline.py` | `TimelineEngine` — auto-registro append-only |
| `evidence.py` | `EvidenceEngine` — logs/hashes/IPs/domains/arquivos/prints/JSON/IOC/links |
| `notes.py` | `CommentEngine` — notas markdown |
| `tasks.py` | `TaskEngine` — criar/concluir/reabrir |
| `owners.py` | `OwnerEngine` — transferência de responsável |
| `attachments.py` | `AttachmentEngine` — anexos |
| `builder.py` | `CaseBuilder` — Case a partir de Incident |
| `engine.py` | `CaseEngine` — orquestra todos os sub-engines |
| `registry.py` | Hooks on_created/on_updated/on_status_changed |
| `context.py` | `CaseContext` — storage in-memory |
| `base.py`, `exceptions.py`, `README.md` | Suporte e documentação |

### Testes — 4 arquivos, +41 casos

`test_cases_models.py`, `test_cases_engines.py`, `test_cases_engine.py`, `test_cases_coverage.py`

---

## 2. Arquitetura

```
Incident -> CaseBuilder -> Case -> Resolution
                ↓
          (workspace)
  Timeline | Evidence | Notes | Tasks | Owners | Attachments | Playbook
```

### Modelo Case

```python
Case(
    id, title, description, owner,
    status, severity, priority, risk_score,
    created_at, updated_at, closed_at,
    incident_id, alerts, assets, users, iocs, mitre,
    timeline, comments, attachments, tasks, evidences,
    playbook, resolution
)
```

### Timeline (auto-registro)

O `TimelineEngine` registra automaticamente: criado, novo alerta, mudança de status,
comentário, anexo, tarefa, mudança de owner, resolução e reabertura — **append-only**.

### Evidence Engine

9 tipos de evidência: `LOG`, `HASH`, `IP`, `DOMAIN`, `FILE`, `SCREENSHOT`, `JSON`, `IOC`, `LINK`.

### Ciclo de vida

```
OPEN -> IN_PROGRESS -> ON_HOLD -> RESOLVED -> CLOSED
  ^                                    ^          |
  |____________________________________|__________|
                   REOPENED (reabrir)
```

---

## 3. Componentes Implementados

| Componente | Comportamento |
|---|---|
| **TimelineEngine** | Registro automático de ações; append-only (imutável) |
| **EvidenceEngine** | Anexa evidências por tipo com label/source |
| **CommentEngine** | Notas markdown com autor + data; histórico |
| **TaskEngine** | Criar/concluir/reabrir; prioridade, responsável, prazo |
| **OwnerEngine** | Transferência de owner registrada na timeline |
| **AttachmentEngine** | Anexos (nome, MIME, tamanho, URL) |
| **CaseEngine** | Orquestra sub-engines; transições validadas; métricas |
| **Playbook** | Estrutura para futura automação (sem automação ainda) |

---

## 4. Qualidade

| Métrica | Alvo | Resultado | Status |
|---------|------|-----------|--------|
| Testes | — | **687 passando** (3.06s) | ✅ |
| Cobertura | ≥ 95% | **95.39%** | ✅ |
| mypy strict | 0 erros | **0 erros (110 arquivos)** | ✅ |
| ruff check | 0 avisos | **All checks passed** | ✅ |
| ruff format | ok | **171 arquivos formatados** | ✅ |

---

## 5. Próxima Sprint

**Sprint 2.10 — API v1 + CLI + health**: orquestração dos engines (ingestão → correlação → detecção → alertas → incidentes → cases) via REST e CLI, com health checks.

---

## 6. Como Executar

```powershell
cd C:\Users\edmil\EDYSIEM
$env:PYTHONPATH = "$PWD\src"
python -m pytest -q                # testes + cobertura
python -m mypy                     # type check strict
python -m ruff check src tests     # lint
python -m ruff format --check src tests
```

> Relatório gerado pelo TITAN AI SQUAD (jr + VULCAN + QA)
