# EDY SIEM project context

EDY SIEM is an open-source Security Information and Event Management platform
for SOC operations, detection engineering, incident response, investigation,
and threat intelligence.

## Current delivery

- **Version:** `0.2.0`
- **Release scope:** Dashboard, War Room, Alert Center, incidents, cases,
  investigation, rules, IOC and asset context, and Detection Dashboard.
- **Backend:** Python 3.12, FastAPI v1, SQLite, typed domain modules.
- **Frontend:** React 18, TypeScript, Vite, and the Echelon design system.
- **Quality baseline:** 801 tests, 95%+ coverage, mypy strict, Ruff, TypeScript,
  and production build.

## Source of truth

- [Product manifesto](../docs/product/project-manifesto.md)
- [Product overview](../docs/product/overview.md)
- [Architecture overview](../docs/architecture/overview.md)
- [System design](../docs/architecture/system-design.md)
- [Roadmap](../ROADMAP.md)
- [Documentation hub](../docs/README.md)

## Release constraint

The final 0.2.x work is portfolio and release hardening only: no new features,
backend behavior, API contracts, or architecture changes.
