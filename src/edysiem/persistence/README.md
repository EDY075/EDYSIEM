# Persistence Foundation — EDY SIEM

Camada de persistencia isolada (ADR-002), 100% stdlib (SQLite).

## Componentes

| Componente | Responsabilidade |
|---|---|
| `ConnectionManager` | Conexoes SQLite (WAL, foreign keys ON, pool por thread) |
| `TransactionManager` | BEGIN/COMMIT/ROLLBACK com context manager |
| `UnitOfWork` | Agrupa repositorios em transacao atomica |
| `Repository` (Protocol) | Contrato de repositorio por agregado |
| `Migration` / `MigrationRunner` | Schema versionado (`schema_migrations`) |
| `AlertRepository` | Persiste `Alert` (risk/fingerprint/dedup) |
| `IncidentRepository` | Persiste `Incident` (grouping/correlator) |
| `CaseRepository` | Persiste `Case` (timeline/evidences/tasks/comments/playbook) |

## Uso

```python
from edysiem.persistence import (
    ConnectionManager,
    MigrationRunner,
    UnitOfWork,
    ALL_MIGRATIONS,
)

manager = ConnectionManager(":memory:")
MigrationRunner(ALL_MIGRATIONS).apply(manager)

with UnitOfWork(manager) as uow:
    uow.alerts.add(alert)
    uow.incidents.add(incident)
    uow.cases.add(case)
# commit automatico ao sair do bloco
```

## Regras

- **Nada de SQL espalhado** — repositorios isolam o acesso a dados.
- **Repositorios por agregado** — Alert, Incident, Case.
- **Transacoes atomicas** — via `UnitOfWork` / `TransactionManager`.
- **Prepared statements** — todo SQL usa parametros (`?`).
- **Indices basicos** — rule/severity/created em alerts; status/severity/created em incidents; status/incident/created em cases.
- **Schema versionado** — `schema_migrations` + `MigrationRunner`.

## Migracoes

```python
class SchemaV2(Migration):
    version = 2
    description = "adiciona coluna X"

    def up(self, conn):
        conn.execute("ALTER TABLE alerts ADD COLUMN x TEXT")
```

Registre em `ALL_MIGRATIONS` e `MigrationRunner.apply` aplica as pendentes em ordem.

## Fora de escopo (sprints futuras)

- PostgreSQL (trocar via Protocol, sem refatorar)
- Particionamento/retention
- Eventos append-only (tabela de eventos)
