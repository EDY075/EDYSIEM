# EDY SIEM — Relatório do Sprint 2.11 (Persistence Foundation + Engine + Event Store)

**Data:** 03/08/2026
**Produto:** EDY SIEM — Security Information and Event Management
**Escopo:** Persistência SQLite (ADR-002) + Persistence Engine + Event Store
**Fora de escopo:** PostgreSQL, particionamento/retention, frontend, autenticação
**Status:** ✅ CONCLUÍDO — pipeline de qualidade 100% verde

---

## 1. Arquivos Criados

### `src/edysiem/persistence/`

| Arquivo | Responsabilidade |
|---|---|
| `connection.py` | `ConnectionManager` — conexões SQLite (WAL, foreign keys, pool por thread) |
| `migrations.py` | `Migration` + `MigrationRunner` — schema versionado (`schema_migrations`) |
| `schema.py` | `SchemaV1` (alerts/incidents/cases) + `SchemaV2` (events) + índices |
| `query.py` | `QueryFilter`, `QueryOp`, `SortOrder`, `Page` — filtros declarativos |
| `repository.py` | `Repository` (Protocol) + `GenericRepository` (CRUD + paginação/ordenação/filtros) |
| `transactions.py` | `TransactionManager` + `UnitOfWork` — transações atômicas |
| `event_store.py` | `EventStore`/`EventRepository` — Event Store da pipeline |
| `repos/alerts.py` | `AlertRepository` — CRUD + busca por fingerprint/status/severidade/data |
| `repos/incidents.py` | `IncidentRepository` — CRUD + busca por status/severidade/fingerprint/data |
| `repos/cases.py` | `CaseRepository` — CRUD + busca por status/incident/owner/data |
| `exceptions.py` | Hierarquia de erros de persistência |
| `README.md` | Documentação |

### Testes

`test_persistence.py` (fundação), `test_persistence_engine.py` (CRUD/filtros/paginação + Event Store)

---

## 2. Persistence Engine (2.11.2)

### GenericRepository

```python
class GenericRepository[T]:
    def add(entity) -> T
    def get(id) -> T | None
    def update(entity) -> T
    def delete(id) -> bool
    def all() -> list[T]
    def query(filters, sort_by, order, limit, offset) -> Page[T]
    def count(filters) -> int
    def search(field, value, limit, offset) -> Page[T]
```

- **Paginação**: `Page(items, total, offset, limit, has_more)`
- **Ordenação**: `SortOrder.ASC/DESC`
- **Filtros**: `QueryFilter(field, op, value)` com ops `eq/neq/gt/gte/lt/lte/contains`
- **Sem SQL espalhado**: filtros declarativos; SQL isolado nos repos

### Repositórios por agregado

| Repo | Buscas |
|---|---|
| `AlertRepository` | id, fingerprint, status, severity, rule, date_range |
| `IncidentRepository` | id, fingerprint, status, severity, date_range |
| `CaseRepository` | id, status, incident, owner, date_range |

---

## 3. Event Store (2.11.3)

```python
StoredEvent(event_id, timestamp, correlation_id, pipeline_stage, version, source, event_type, payload)
```

Persiste todo evento da pipeline: `RawEvent → CanonicalEvent → EnrichedEvent → CorrelatedEvent →
DetectionFinding → Alert → Incident → Case`.

Cada evento carrega: **UUID, timestamp, correlation_id, pipeline_stage, version, source**.

### Consultas

- `get(event_id)`
- `by_correlation(correlation_id)` — cadeia completa de uma correlação (ordenada por tempo)
- `by_stage(stage)` — eventos de um estágio
- `query(stage, correlation_id, limit, offset)` — paginado
- `count()`

---

## 4. Qualidade

| Métrica | Alvo | Resultado | Status |
|---------|------|-----------|--------|
| Testes | — | **742 passando** (3.62s) | ✅ |
| Cobertura | ≥ 95% | **95.17%** | ✅ |
| mypy strict | 0 erros | **0 erros (138 arquivos)** | ✅ |
| ruff check | 0 avisos | **All checks passed** | ✅ |
| ruff format | ok | **205 arquivos formatados** | ✅ |

---

## 5. Decisões Relevantes

1. **Repos não committam internamente** — o `UnitOfWork`/`TransactionManager` controla a atomicidade (rollback efetivo).
2. **Filtros declarativos** via `QueryFilter` — sem SQL espalhado nas camadas superiores.
3. **Schema versionado** com `MigrationRunner` — v1 (agregados) e v2 (event store).
4. **Prepared statements** em todo SQL + índices básicos (rule/severity/created, status, correlation, timestamp).
5. **Troca de motor via Protocol** (PostgreSQL futuro) sem refatorar as camadas superiores.

---

## 6. Como Executar

```powershell
cd C:\Users\user\EDYSIEM
$env:PYTHONPATH = "$PWD\src"
python -m pytest -q
python -m mypy
python -m ruff check src tests
```

---

## 7. Próxima Sprint

**Sprint 2.12 — Engines + persistência**: conectar os contexts (Alert/Incident/Case) aos repositórios e persistir a pipeline E2E.

---

> Relatório gerado pelo TITAN AI SQUAD (jr + VULCAN + QA)
