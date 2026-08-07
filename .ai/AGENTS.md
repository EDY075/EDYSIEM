# AI collaboration guide

Any agent working on EDY SIEM should first read the
[project context](PROJECT_CONTEXT.md), [architecture notes](ARCHITECTURE.md),
[workflow](WORKFLOW.md), [coding standards](CODING_STANDARDS.md), and
[decision register](DECISIONS.md).

## Guardrails

- Do not change API contracts, architecture, or product behavior without a documented decision.
- Do not manufacture operational data in the frontend; use explicit unavailable or empty states.
- Keep runtime dependencies out of the domain core. Tooling belongs in the `dev` extra and HTTP dependencies in the `api` extra.
- Before delivery, run pytest, mypy, Ruff, `npm run build`, and `npx tsc -b` as applicable.
- Record durable delivery lessons in [KNOWLEDGE_BASE.md](KNOWLEDGE_BASE.md) and significant work in [MEMORY_LOG.md](MEMORY_LOG.md).

## Handoff

Use [AI_HANDOFF.md](AI_HANDOFF.md) for task context, affected files, validation evidence, and any remaining risk. Keep the public [README.md](../README.md) aligned with the shipped project.
