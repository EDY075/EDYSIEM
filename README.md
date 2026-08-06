# EDY SIEM

Plataforma profissional de Security Information and Event Management (SIEM).
Python 3.12 (backend) + TypeScript (frontend) — arquitetura limpa, modular e didática.

> **Status:** Sprint 1 (Foundation Core) — tag `v0.1.0`. Sprints 2.1–2.12
> concluídas: pipeline oficial (ADR-008), infraestrutura de ingestão (ADR-009),
> parsers + normalizer, Enrichment Engine, Correlation Engine, Rule/Detection
> Framework (DSL declarativa), Alert Engine Enterprise (risk/fingerprint/dedup/
> lifecycle), Incident Engine Enterprise (grouping/correlator/lifecycle), Case
> Engine (Investigation Workspace), API v1 + CLI Enterprise (FastAPI),
> Persistence Foundation + Engine + Event Store (SQLite, repos por agregado,
> UnitOfWork, pipeline persistida), Search Engine + Audit Trail (busca
> desacoplada, auditoria completa) — frameworks desacoplados com regras
> declarativas, janelas temporais, isolamento de falhas e métricas.
> **Sprint 2.13 — Estabilização do Projeto concluída** (checkpoint v0.2.0):
> projeto consistente entre código, Git e documentação; UI 4.x formalizada.
> Próxima: Sprint 2.14 (integração E2E Pipeline → Alert → Incident → Case).
> **Regra Nº 1:** qualidade de arquitetura antes de velocidade.

## Rodando o projeto (um comando)

Qualquer pessoa que clonar o repositório consegue subir o ambiente completo:

```bash
# 1) instala as dependências (backend + frontend) automaticamente
# 2) cria o banco e aplica migrações
# 3) inicia backend (:8080) + frontend (:5173)
# 4) popula dados de demonstração e abre o navegador
python run.py
```

- Frontend (UI): http://localhost:5173
- Swagger/API: http://127.0.0.1:8080/docs

Equivalente via CLI instalada: `edysiem dev` (flags `--no-seed`, `--no-open`).
Scripts prontos: `scripts/dev.ps1` (Windows) e `scripts/dev.sh` (Linux/macOS).

### Instalação manual (opcional)

```bash
# Backend (Python 3.12+)
python -m pip install -e ".[dev]"

# Frontend (Node 18+)
cd frontend && npm install && cd ..
```

### Modo desenvolvimento

```bash
python run.py                 # backend + frontend + seed + abre o navegador
python run.py --no-seed       # sem dados de demonstração
python run.py --no-open       # não abre o navegador
```

Servidores individuais (debug):
```bash
uvicorn edysiem.api.app:create_app --factory --host 127.0.0.1 --port 8080
cd frontend && npm run dev
```

### Resolução de problemas

| Problema | Solução |
|---|---|
| `Port 8080 already in use` | Encerre o processo anterior (`Get-NetTCPConnection -LocalPort 8080`) e rode de novo |
| `node/npm não encontrado` | Instale Node.js 18+ (https://nodejs.org) |
| Frontend abre sem dados | Verifique o backend em `/docs`; o Vite faz proxy `/api` → `:8080` |
| Dados resetados | O banco dev fica em `instance/edysiem.db` (remova o arquivo para recomeçar) |
| POST retorna 422 ao testar com curl | Não passe JSON inline via shell (aspas são removidas) — use `/docs` (Swagger), Python `requests`, ou `curl --data-binary @arquivo.json` |

## Documentação

| Documento | Conteúdo |
|---|---|
| [PRODUCT_VISION.md](docs/PRODUCT_VISION.md) | Visão, público, objetivos |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Arquitetura e fluxo |
| [SYSTEM_DESIGN.md](docs/SYSTEM_DESIGN.md) | Componentes e modelagem |
| [DECISIONS.md](docs/DECISIONS.md) | Índice de ADRs |
| [ROADMAP.md](docs/ROADMAP.md) | Sprints planejadas |
| [STUDY_GUIDE.md](docs/STUDY_GUIDE.md) | O que é SIEM (didático) |
| [STYLE_GUIDE.md](docs/STYLE_GUIDE.md) | Design system |
| [CODING_STANDARD.md](docs/CODING_STANDARD.md) | Padrão de código |

Índice completo: [docs/](docs/)

## Frontend (React)

- `frontend/` — Design System (tokens + componentes base), estrutura React (AppShell, Sidebar, Topbar, Routing, ThemeProvider, estado global, toasts) e camada conectada ao backend (API client + hooks). Consome a API **`/soc/*`** real: **Dashboard** (`/`), **War Room** (`/war-room`), **Alert Center** (`/alerts`), **Incident Center** (`/incidents`), **Case Management** (`/cases`), **Investigation Workspace** (`/investigate`), **Intelligence** (Rules/IOC/Assets, `/rules` `/intel`) e **Detection Dashboard** (`/detection`). Sem dados mock.
- Benchmark UX: [docs/ENTERPRISE_UX_BENCHMARK.md](docs/ENTERPRISE_UX_BENCHMARK.md).

```bash
cd frontend && npm install && npm run dev
```

> O Vite faz proxy de `/api` para o FastAPI em `http://localhost:8080` (configurável via `VITE_API_URL`).

## Visão do fluxo

```
Event Sources -> Collectors -> RawEvent -> Parser -> ParsedEvent
-> Normalizer -> CanonicalEvent -> Enrichment -> EnrichedEvent
-> Correlation -> Detection -> Incident -> Persistence
-> REST API -> Dashboard/CLI
```

## Roadmap resumido

- **S0:** Fundação (docs, ADRs, UX, design system, estrutura) ✅
- **S1:** Núcleo (core, persistence, pipeline, regras, incidentes, API, CLI, UI v0) — Core ✅
- **S2:** Operação SOC (dashboard, investigação, regras UI, intel, assets, incident UI)
- **S3:** Escala (fila externa, storage alternativo, auth, hunting)
