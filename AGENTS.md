# EDY SIEM repository guidance

- Keep the backend and frontend contracts stable unless a task explicitly
  requires a product change.
- Preserve historical documentation; use `docs/archive/` rather than deleting it.
- Run `pytest`, `mypy`, `ruff`, and the frontend build before release-oriented
  changes.
- Do not commit databases, credentials, local logs, or generated caches.
