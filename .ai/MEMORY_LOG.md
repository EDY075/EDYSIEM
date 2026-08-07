# Memory log

## 2026-08-06 — Release final 0.2.x

- Reorganized the repository for open-source presentation: documentation taxonomy, community standards, CI, visual assets, README banner, GIF, and product gallery.
- Fixed CI dependency resolution by updating `pytest-asyncio` to 1.4.0 and declaring `httpx2` for the Starlette test client.
- Made the two exact-token rate-limiter assertions deterministic with a frozen test clock; product code and runtime behavior remain unchanged.
- Reproduced the final dependency set in a clean Python 3.12 environment: `pip check`, 801 tests, mypy, and Ruff all passed.
- GitHub About, topics, and the professional release were published after the CI passed.
- Revalidated the Alert Center with persisted data: table, severity/status filters, and detail drawer work without console errors. Updated the Alert Center screenshot and the eight-frame product tour GIF from the validated UI.

## Ongoing constraints

- No new product features, backend behavior, API contracts, or architecture changes are included in this release finalization.
