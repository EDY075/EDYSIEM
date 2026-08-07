# Knowledge base

## Engineering rules

- Keep the domain core dependency-free; use `dev` and `api` extras for tooling and the HTTP layer.
- Keep frontend views faithful to actual API data. Missing contracts should use explicit empty or unavailable states, never fabricated metrics.
- Run `pytest` (95% coverage gate), mypy strict, Ruff, Vite build, and TypeScript build before publication.

## CI dependency baseline

- `pytest==9.1.1` requires `pytest-asyncio==1.4.0`; the prior `0.25.3` pin was incompatible with pytest 9.
- Current Starlette test client requires `httpx2==2.9.1` in the test environment. Keep it in the `dev` extra so production runtime dependencies stay unchanged.

## Release discipline

- Validate dependency installation in a clean environment, then verify the remotely triggered GitHub Actions run before creating a release.
- Keep the repository presentation assets under `assets/` and link every README image locally.
