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

Copy `.env.example` to `.env`, replace both token placeholders with random
values of at least 32 bytes, and explicitly choose the operator identity and
role. The example placeholders are intentionally rejected.

One way to generate a key without an additional package is:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

```bash
python run.py
```

The command creates the local development database, applies migrations, starts
the FastAPI service on port 8080 and the Vite frontend on port 5173. Use
`--no-seed` to skip demonstration data and `--no-open` to prevent browser
launching. Backend and frontend are localhost-only in version 0.3.0. Do not
override the loopback bind or publish either port; remote deployment requires a
separately reviewed TLS reverse-proxy architecture.

## Useful endpoints

- UI: `http://localhost:5173`
- Health: `http://127.0.0.1:8080/api/v1/health`
- API documentation: `http://127.0.0.1:8080/docs`

The UI requests the configured API key on first access and keeps it only for the
current browser tab/session. Direct API clients send the same value in
`X-API-Key`; the role comes exclusively from server configuration.

For development conventions, see [coding standard](coding-standard.md). For
dependency origin and reproducible-resolution policy, see
[dependency provenance](dependency-provenance.md).
