# Memory log

## 2026-08-06 — Release final 0.2.x

- Reorganized the repository for open-source presentation: documentation taxonomy, community standards, CI, visual assets, README banner, GIF, and product gallery.
- Fixed CI dependency resolution by updating `pytest-asyncio` to 1.4.0 and declaring `httpx2` for the Starlette test client.
- Reproduced the final dependency set in a clean Python 3.12 environment: `pip check`, 801 tests, mypy, and Ruff all passed.
- GitHub About and topics were updated. The professional release will be created after the pushed CI run is green.

## Ongoing constraints

- No new product features, backend behavior, API contracts, or architecture changes are included in this release finalization.
