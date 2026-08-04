# EDY SIEM

Plataforma profissional de Security Information and Event Management (SIEM).
Python 3.12 (backend) + TypeScript (frontend) — arquitetura limpa, modular e didática.

> **Status:** Sprint 1 (Foundation Core) concluída — tag `v0.1.0`. Sprints 2.1–2.7
> concluídas: pipeline oficial (ADR-008), infraestrutura de ingestão (ADR-009),
> parsers + normalizer, Enrichment Engine, Correlation Engine, Rule/Detection
> Framework (DSL declarativa) e Alert Engine Enterprise (risk/fingerprint/dedup/
> lifecycle) — frameworks desacoplados com regras declarativas, janelas
> temporais, isolamento de falhas e métricas.
> **Regra Nº 1:** qualidade de arquitetura antes de velocidade.

## Documentação

| Documento | Conteúdo |
|---|---|
| [PRODUCT_VISION.md](docs/PRODUCT_VISION.md) | Visão, público, objetivos |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Arquitetura e fluxo |
| [SYSTEM_DESIGN.md](docs/SYSTEM_DESIGN.md) | Componentes e modelagem |
| [DECISIONS.md](docs/DECISIONS.md) | Índice de ADRs |
| [ROADMAP.md](docs/ROADMAP.md) | Sprints planejadas |
| [STUDY_GUIDE.md](docs/STUDY_GUIDE.md) | O que é SIEM (didático) |
| [STYLE_GUIDE.md](docs/STYLE_GUIDE.md) | Design system |
| [CODING_STANDARD.md](docs/CODING_STANDARD.md) | Padrão de código |

Índice completo: [docs/](docs/)

## Visão do fluxo

```
Event Sources -> Collectors -> RawEvent -> Parser -> ParsedEvent
-> Normalizer -> CanonicalEvent -> Enrichment -> EnrichedEvent
-> Correlation -> Detection -> Incident -> Persistence
-> REST API -> Dashboard/CLI
```

## Roadmap resumido

- **S0:** Fundação (docs, ADRs, UX, design system, estrutura) ✅
- **S1:** Núcleo (core, persistence, pipeline, regras, incidentes, API, CLI, UI v0) — Core ✅
- **S2:** Operação SOC (dashboard, investigação, regras UI, intel, assets, incident UI)
- **S3:** Escala (fila externa, storage alternativo, auth, hunting)
