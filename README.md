<p align="center">
  <img src="assets/branding/edysiem-banner.png" alt="EDY SIEM — Open Source Security Information and Event Management Platform">
</p>

<p align="center">
  <a href="https://github.com/EDY075/EDYSIEM/actions/workflows/ci.yml"><img src="https://github.com/EDY075/EDYSIEM/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" alt="Python 3.12">
  <img src="https://img.shields.io/badge/TypeScript-5.x-3178C6?logo=typescript&logoColor=white" alt="TypeScript">
  <img src="https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=111827" alt="React 18">
  <img src="https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/tests-948-16a34a" alt="948 automated tests">
  <img src="https://img.shields.io/badge/coverage-95.02%25-16a34a" alt="95.02 percent coverage">
  <img src="https://img.shields.io/badge/version-0.3.0-2563eb" alt="Version 0.3.0">
  <img src="https://img.shields.io/badge/license-MIT-f59e0b" alt="MIT License">
</p>

<p align="center">
  <strong>SOC Detection, Investigation & Response platform with an operational decision queue, evidence-led investigation and case handoff.</strong>
</p>

<p align="center">
  <a href="#quick-start">Quick start</a> ·
  <a href="#product-tour">Product tour</a> ·
  <a href="#architecture">Architecture</a> ·
  <a href="docs/README.md">Documentation</a>
</p>

## Product tour

<table>
  <tr>
    <td width="50%"><strong>SOC Decision Center</strong><br><img src="assets/screenshots/release-decision-center.png" alt="EDY SIEM SOC Decision Center"></td>
    <td width="50%"><strong>Shield investigation</strong><br><img src="assets/screenshots/release-shield-investigation.png" alt="EDY Shield evidence investigation in EDY SIEM"></td>
  </tr>
  <tr>
    <td><strong>Case Center</strong><br><img src="assets/screenshots/release-case-center.png" alt="EDY SIEM Case Center with Shield provenance"></td>
    <td><strong>Operational context</strong><br>Decision Queue, SLA, ownership and Ingestion Health use persisted API data; unavailable data is declared rather than simulated.</td>
  </tr>
</table>

## Overview

EDY SIEM is a **SOC Detection, Investigation & Response** workspace. The Python backend
persists the lifecycle while the React interface prioritizes the operational decision:
what requires attention, who owns it, its SLA, the evidence and the next supported action.

**Operational flow:** EDY Shield event → inbox/normalization → Decision Queue →
investigation → entity/MITRE context when supplied → decision → case → return to the same event.

| Area | What it supports |
| --- | --- |
| Operations | Dashboard, War Room, Alert Center, incidents, cases, and playbooks |
| Detection engineering | Rules, simulator, MITRE context, and detection metrics |
| Threat intelligence | IOC Manager and asset context connected to SOC data |
| Platform | FastAPI v1 contracts, SQLite persistence, typed Python, and a React/Vite UI |

## EDY security ecosystem

- **EDY Shield** is the endpoint telemetry and integrity product: FIM, baselines, scans,
  hashes and durable local outbox delivery.
- **EDY SIEM** receives that telemetry for correlation, investigation and response.
- **WAR_ROOM** is an evolving context and threat-intelligence surface inside the SIEM; no
  separate WAR_ROOM integration is claimed by this release.

## Quick start

Requirements: Python 3.12+ and Node.js 18+.

```bash
python -m pip install -e ".[dev,api]"
cd frontend && npm ci && cd ..
python run.py
```

The single command applies migrations, starts backend and frontend, seeds safe
demonstration data, and opens the UI. Use `--no-seed` or `--no-open` when needed.

| Service | URL |
| --- | --- |
| SOC workspace | http://localhost:5173 |
| Health check | http://127.0.0.1:8080/api/v1/health |
| OpenAPI / Swagger | http://127.0.0.1:8080/docs |

## Architecture

```text
Event sources → Collectors → Parsing → Normalization → Enrichment
             → Correlation → Detection → Alerts → Incidents → Cases
             → SQLite persistence → FastAPI v1 → React SOC workspace
```

Read the [architecture overview](docs/architecture/overview.md) and
[data flow](docs/architecture/data-flow.md) for the complete design.

## Roadmap

The current 0.3.x delivery record and the next milestones are in the
[roadmap](ROADMAP.md). Historical implementation reports are kept in the
[sprint archive](docs/sprints/README.md).

## Documentation

| Topic | Entry point |
| --- | --- |
| Documentation hub | [docs/README.md](docs/README.md) |
| Development and quality | [development guide](docs/development/getting-started.md) · [testing](docs/development/testing.md) |
| Product and UX | [product overview](docs/product/overview.md) · [design system](docs/ux/design-system.md) |
| Security | [security model](docs/security/security-model.md) |
| Release notes | [release 0.3.0](docs/releases/release-0.3.0.md) |

## Contributing and license

See the [contributing guide](CONTRIBUTING.md), [security guidance](SECURITY.md),
and [MIT License](LICENSE). Built and maintained by [EDY075](https://github.com/EDY075).
