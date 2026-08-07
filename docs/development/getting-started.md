# Getting started

## Requirements

- Python 3.12+
- Node.js 18+

## Install

```bash
python -m pip install -e ".[dev,api]"
cd frontend && npm ci && cd ..
```

## Run the complete stack

```bash
python run.py
```

The command creates the local development database, applies migrations, starts
the FastAPI service on port 8080 and the Vite frontend on port 5173. Use
`--no-seed` to skip demonstration data and `--no-open` to prevent browser
launching.

## Useful endpoints

- UI: `http://localhost:5173`
- Health: `http://127.0.0.1:8080/api/v1/health`
- API documentation: `http://127.0.0.1:8080/docs`

For development conventions, see [coding standard](coding-standard.md).
