<p align="center">
  <img src="assets/branding/edysiem-banner.png" alt="EDY SIEM — Open Source Security Information and Event Management Platform">
</p>

<p align="center">
  <a href="https://github.com/EDY075/EDYSIEM/actions/workflows/ci.yml"><img src="https://github.com/EDY075/EDYSIEM/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" alt="Python 3.12">
  <img src="https://img.shields.io/badge/TypeScript-5.x-3178C6?logo=typescript&logoColor=white" alt="TypeScript">
  <img src="https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=111827" alt="React 18">
  <img src="https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/tests-801-16a34a" alt="801 automated tests">
  <img src="https://img.shields.io/badge/coverage-95.10%25-16a34a" alt="95.10 percent coverage">
  <img src="https://img.shields.io/badge/version-0.2.0-2563eb" alt="Version 0.2.0">
  <img src="https://img.shields.io/badge/license-MIT-f59e0b" alt="MIT License">
</p>

<p align="center">
  <strong>Open-source SIEM and SOC operations platform with detection engineering, incident response, investigation workflows, and threat intelligence.</strong>
</p>

<p align="center">
  <a href="#quick-start">Quick start</a> ·
  <a href="#product-tour">Product tour</a> ·
  <a href="#architecture">Architecture</a> ·
  <a href="docs/README.md">Documentation</a>
</p>

![EDY SIEM product tour](assets/demos/edysiem-product-tour.gif)

## Product tour

<table>
  <tr>
    <td width="50%"><strong>Dashboard</strong><br><img src="assets/screenshots/dashboard-overview.png" alt="EDY SIEM Dashboard"></td>
    <td width="50%"><strong>War Room</strong><br><img src="assets/screenshots/war-room.png" alt="EDY SIEM War Room"></td>
  </tr>
  <tr>
    <td><strong>Alert Center</strong><br><img src="assets/screenshots/alert-center.png" alt="EDY SIEM Alert Center"></td>
    <td><strong>Incidents</strong><br><img src="assets/screenshots/incident-management.png" alt="EDY SIEM Incident Management"></td>
  </tr>
  <tr>
    <td><strong>Investigation</strong><br><img src="assets/screenshots/investigation-workspace.png" alt="EDY SIEM Investigation Workspace"></td>
    <td><strong>Rules</strong><br><img src="assets/screenshots/rules-engine.png" alt="EDY SIEM Rules Engine"></td>
  </tr>
  <tr>
    <td><strong>IOC and Assets</strong><br><img src="assets/screenshots/intelligence-ioc-assets.jpg" alt="EDY SIEM IOC Manager and asset context"></td>
    <td><strong>Detection Dashboard</strong><br><img src="assets/screenshots/detection-dashboard.png" alt="EDY SIEM Detection Dashboard"></td>
  </tr>
</table>

## Overview

EDY SIEM turns telemetry into an operational SOC workflow. The Python backend
persists the detection lifecycle, while the React interface gives analysts a
focused workspace for triage, response, investigation, rules, and intelligence.

**Operational flow:** Event → Rule → Alert → Incident → Case → Investigation.

| Area | What it supports |
| --- | --- |
| Operations | Dashboard, War Room, Alert Center, incidents, cases, and playbooks |
| Detection engineering | Rules, simulator, MITRE context, and detection metrics |
| Threat intelligence | IOC Manager and asset context connected to SOC data |
| Platform | FastAPI v1 contracts, SQLite persistence, typed Python, and a React/Vite UI |

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

The current 0.2.x delivery record and the next milestones are in the
[roadmap](ROADMAP.md). Historical implementation reports are kept in the
[sprint archive](docs/sprints/README.md).

## Documentation

| Topic | Entry point |
| --- | --- |
| Documentation hub | [docs/README.md](docs/README.md) |
| Development and quality | [development guide](docs/development/getting-started.md) · [testing](docs/development/testing.md) |
| Product and UX | [product overview](docs/product/overview.md) · [design system](docs/ux/design-system.md) |
| Security | [security model](docs/security/security-model.md) |
| Release notes | [release 0.2.0](docs/releases/release-0.2.0.md) |

## Contributing and license

See the [contributing guide](CONTRIBUTING.md), [security guidance](SECURITY.md),
and [MIT License](LICENSE). Built and maintained by [EDY075](https://github.com/EDY075).
