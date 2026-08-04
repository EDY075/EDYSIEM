# EDY SIEM — Relatório do Sprint 2.10 (API v1 + CLI + Health)

**Data:** 03/08/2026
**Produto:** EDY SIEM — Security Information and Event Management
**Escopo:** Infraestrutura de orquestração dos engines (API REST, CLI, health, metrics, version)
**Fora de escopo:** Dashboard React, banco, autenticação, frontend — sprints futuras
**Status:** ✅ CONCLUÍDO — pipeline de qualidade 100% verde

---

## 1. Arquivos Criados

### Infraestrutura

| Arquivo | Responsabilidade |
|---|---|
| `src/edysiem/container.py` | `ApplicationContainer` — container DI único conectando todos os engines |
| `src/edysiem/bootstrap.py` | Config load + build container + logging |

### API v1 (`src/edysiem/api/`)

| Arquivo | Responsabilidade |
|---|---|
| `app.py` | Factory FastAPI (lifespan, middleware, rotas, OpenAPI/Swagger) |
| `middleware.py` | RequestID (`X-Request-ID`) + HTTP logging |
| `errors.py` | Error handler global + validation handler + handlers de domínio |
| `schemas.py` | Modelos Pydantic de request/response |
| `deps.py` | Dependency injection (get_container) |
| `routes/health.py` | `GET /health`, `GET /version`, `GET /metrics` |
| `routes/pipeline.py` | `POST /pipeline/run` |
| `routes/alerts.py` | `POST /alerts` |
| `routes/incidents.py` | `POST /incidents` |
| `routes/cases.py` | `POST /cases` |

### CLI Enterprise (`src/edysiem/cli/`)

`main.py` — comandos: `health`, `version`, `config`, `validate-config`, `run-pipeline`, `ingest`, `demo`.

### Testes

`test_container.py`, `test_api.py`, `test_cli.py`

---

## 2. Arquitetura

```
edysiem (CLI) ─┐
               ├── ApplicationContainer (DI) ── todos os engines
FastAPI v1 ────┘
  ├── GET /health | /version | /metrics
  ├── POST /pipeline/run | /alerts | /incidents | /cases
  ├── Middleware: RequestID + HTTP logging
  ├── Error handlers globais + validation (422)
  └── OpenAPI/Swagger (/docs) + ReDoc (/redoc)
```

### Lifespan

Startup: inicializa enrichment/correlation/detection. Shutdown: finaliza graciosamente.

---

## 3. Endpoints

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/v1/health` | Estado dos engines |
| GET | `/api/v1/version` | Nome, versão, ambiente |
| GET | `/api/v1/metrics` | Métricas agregadas e por engine |
| POST | `/api/v1/pipeline/run` | Executa pipeline ponta a ponta (parse→normalize→enrich→correlate→detect) |
| POST | `/api/v1/alerts` | Cria/deduplica alerta a partir de finding |
| POST | `/api/v1/incidents` | Agrupa alertas em incidente |
| POST | `/api/v1/cases` | Abre case de investigação |

OpenAPI em `/openapi.json`, Swagger UI em `/docs`, ReDoc em `/redoc`.

---

## 4. CLI

```bash
edysiem version          # exibe versão
edysiem health           # estado dos engines
edysiem config           # configuração carregada
edysiem validate-config  # valida configuração (exit 0/1)
edysiem run-pipeline     # executa pipeline ponta a ponta
edysiem ingest "<log>"   # ingere payload bruto (parse+normalize)
edysiem demo             # demo da pipeline com exemplo syslog
```

---

## 5. Qualidade

| Métrica | Alvo | Resultado | Status |
|---------|------|-----------|--------|
| Testes | — | **713 passando** (3.73s) | ✅ |
| Cobertura | ≥ 95% | **95.27%** | ✅ |
| mypy strict | 0 erros | **0 erros (125 arquivos)** | ✅ |
| ruff check | 0 avisos | **All checks passed** | ✅ |
| ruff format | ok | **189 arquivos formatados** | ✅ |

---

## 6. Como Executar

```bash
# API
uvicorn edysiem.api.app:create_app --factory --host 0.0.0.0 --port 8080
# ou via python
python -c "from edysiem.api import create_app; import uvicorn; uvicorn.run(create_app())"

# CLI
python -m edysiem.cli.main version
python -m edysiem.cli.main demo

# Qualidade
python -m pytest -q
python -m mypy
python -m ruff check src tests
```

---

## 7. Próxima Sprint

**Sprint 2.11 — Persistência (SQLite)**: persistir Alert/Incident/Case contexts em SQLite com repositórios por agregado (ADR-002), mantendo os contratos atuais.

---

> Relatório gerado pelo TITAN AI SQUAD (jr + VULCAN + QA)
