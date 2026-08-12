# EDY SIEM 0.3.0 — Release Notes

## SOC Detection, Investigation & Response

This release completes the EDY Shield integration and the analyst workflow around it.
Shield telemetry is received through Event Contract v1, persisted in the SIEM inbox and
opened as an evidence-led investigation with safe provenance, entity context and MITRE
techniques only when the source supplied them.

## Highlights

- SOC Decision Center with a compact Decision Queue, real SLA/ownership and Ingestion Health.
- Shield event investigation with evidence, baseline/hash context and idempotent case handoff.
- Case Center resolves the exact case and returns to the same Shield `event_id`.
- Dedicated route error boundary avoids exposing the raw router error page to operators.
- Real-process E2E confirms offline outbox recovery, no lost events and no logical duplicates.

## Release validation

- 948 tests passed with 95.02% coverage.
- Ruff, MyPy, TypeScript/Vite, wheel/sdist and diff checks passed.
- External Chrome QA covered desktop, notebook, tablet and mobile states; no new application
  console errors or horizontal overflow were found.

## Known limitations

- Production authentication/RBAC remains a deployment concern; the local development
  identity is unchanged.
- The inbox processing worker, retention policy, external queue/storage and SSO remain future
  work. WAR_ROOM is an evolving internal context surface, not a separate integration.
