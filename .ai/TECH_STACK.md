# TECH_STACK.md — Stack, Versões e Contrato de Execução

> Tudo o que um agente precisa saber sobre **linguagens, libs e como rodar**.

## Backend
| Item | Versão / Config |
|---|---|
| Python | `>= 3.12` |
| Core runtime | **100% stdlib** (ADR-001) — `dependencies = []` |
| API | `fastapi>=0.141`, `uvicorn>=0.52`, `pydantic>=2.13` (extra `api`) |
| Dev | `pytest==9.1.1`, `pytest-cov==7.1.0`, `pytest-asyncio==0.25.3`, `mypy==2.3.0`, `ruff==0.16.1` |
| CLI | `edysiem` → `edysiem.cli.main:main` |
| Build | hatchling (wheel em `src/edysiem`) |

## Frontend (`frontend/`)
- **Node 18+**, Vite 5, React 18, TypeScript 5, `react-router-dom` 6, `recharts 3`.
- Scripts: `dev` (vite), `build` (`tsc -b && vite build`), `preview`.
- Proxy dev: `/api` → `http://localhost:8080` (configurável via `VITE_API_URL`).

## Comandos de qualidade (obrigatórios antes de "pronto")

### Backend (na raiz do repo)
```bash
python -m pytest                 # testes + coverage ≥ 95% (addopts já inclui cov)
python -m mypy                   # strict, src (0 erros)
python -m ruff check .           # lint (0 issues)
python -m ruff format --check .  # (formatação, se aplicável)
```

### Frontend (`frontend/`)
```bash
cd frontend && npm run build     # tsc -b + vite build
```

### Subir o ambiente (comando único)
```bash
python run.py            # backend :8080 + frontend :5173 + seed + abre browser
python run.py --no-seed  # sem dados de demonstração
python run.py --no-open  # não abre navegador
# ou CLI: edysiem dev [flags]
# scripts: scripts/dev.ps1 (Win) / scripts/dev.sh (Linux/macOS)
```

### Servidores individuais (debug)
```bash
# backend
python -m uvicorn edysiem.api.app:create_app --factory --host 127.0.0.1 --port 8080
# frontend
cd frontend && npm run dev
```

## Pontos de atenção
- Coverage gate configurado em `pyproject.toml` (`[tool.coverage...] fail_under = 95`).
- Mypy strict em `files = ["src"]`, `ignore_missing_imports = false`.
- O core runtime **não** usa libs externas (ADR-001) — dependências ficam em extras (`dev`, `api`).

## Referências
- `pyproject.toml` (config real) · `frontend/package.json` · `frontend/vite.config.ts`
- Guias: `docs/BACKEND_GUIDE.md` · `docs/FRONTEND_GUIDE.md` · `docs/TESTING_GUIDE.md`