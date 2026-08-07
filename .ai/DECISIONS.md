# DECISIONS.md — Decisões Técnicas (ADR) relevantes

> Índice e resumo das decisões que moldam o EDY SIEM. ADRs completos em `docs/adr/`.
> **Regra:** toda decisão arquitetural nova exige um ADR.

## Índice de ADRs

| ADR | Tema | Resumo |
|---|---|---|
| ADR-001 | Stack/backbone | **Core 100% stdlib**; dependências só em extras (`dev`, `api`) |
| ADR-002 | Persistência | SQLite por padrão (portabilidade), camada de repositórios |
| ADR-003 | Pipeline | Fluxo canônico de eventos |
| ADR-004 | Rules | Rule engine declarativo (DSL + `DetectionRule`) |
| ADR-005 | Frontend | React + TypeScript + Vite, Design System próprio |
| ADR-006 | Observabilidade | Logger estruturado JSON, correlation/request ID |
| ADR-007 | Plugins/DI | Container DI manual, contratos de plugin |
| ADR-008 | Pipeline de eventos | Pipeline oficial de eventos (event bus) |
| ADR-009 | Ingestão | Infraestrutura de ingestão Enterprise |

## Decisões-chave (resumo executivo)
1. **Core lib-free** (ADR-001) — núcleo portável e testável sem depender de libs.
2. **SQLite por padrão** (ADR-002) — com *Protocol* p/ storage alternativo (PostgreSQL na Sprint 2.18).
3. **Frontend com Design System próprio** (Echelon) + API real, **sem dados fictícios**.
4. **Auth opt-in** na API: `X-API-Key` somente se `EDYSIEM_API_KEY` definida (RBAC + rate limit em camadas).
5. **Mypy strict + ruff + coverage ≥ 95%** como gate obrigatório.

## Regras de governança de decisões
- Qualquer mudança no contrato de API, no pipeline ou no design system → ADR.
- Any (tipos dinâmicos) só em fronteiras justificadas (ver exceções em `pyproject.toml` → `[tool.ruff.lint.per-file-ignores]`).

## Referências
- `docs/DECISIONS.md` (índice canônico) · `docs/adr/` (ADRs completos)