# Troubleshooting

## A local port is already in use

Stop the previous EDY SIEM development process, then run `python run.py` again.
The runner exits cleanly when a service cannot start.

## Frontend cannot reach the API

Confirm `GET /api/v1/health` on port 8080. In development, Vite proxies `/api`
to the local FastAPI service; do not hard-code an API URL unless a deployment
requires `VITE_API_URL`.

## Re-running demonstration data

The seed is idempotent. Existing alerts and incidents are reused by fingerprint
and the case linked to the incident is preserved. Use `python run.py --no-seed`
when no demonstration data should be populated.

## Quality commands

```bash
python -m pytest
python -m mypy
python -m ruff check .
cd frontend && npm run build && npx tsc -b
```
