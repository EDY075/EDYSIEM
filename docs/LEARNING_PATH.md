# EDY SIEM — Learning Path

> Trilha de estudos pessoal para dominar SIEM/SOC construindo o EDY SIEM.
> Cada etapa conecta teoria + prática no projeto.

## Trilha

| Etapa | Teoria | Prática no projeto |
|---|---|---|
| 1 | O que é SIEM, ciclo do evento | `STUDY_GUIDE.md` + fluxo no `SYSTEM_DESIGN.md` |
| 2 | Logs: syslog, Linux, Windows | Parser syslog em `normalization` (S1.3) |
| 3 | Normalização e modelagem | `core/events.py` + `DATABASE.md` (S1.1) |
| 4 | Enriquecimento e intel | `enrichment` + IOCs (S1.4) |
| 5 | Correlação | `correlation` + regras YAML (S1.5) |
| 6 | Detecção e MITRE | `detection` + mapeamento ATT&CK (S1.5) |
| 7 | Alertas e Incidentes | `incident` engine (S1.6) |
| 8 | API e automação | `api` v1 + `cli` (S1.7) |
| 9 | SOC operations | Dashboard + triagem + investigação (S2) |
| 10 | Threat Hunting | Hunting UI + consultas (S3.5) |

## Skills praticadas

- Python tipado, Clean Architecture, testes.
- Engenharia de detecção, correlação, MITRE ATT&CK.
- REST API design, CLI, persistência.
- Frontend TypeScript + design system + UX SOC.
- Segurança da plataforma, observabilidade, documentação.

## Cadência sugerida

- 1 sessão/semana → sprints de fundação primeiro, depois 1 módulo por semana.
- Ao final de cada módulo: atualizar `STUDY_GUIDE.md` com o que aprendeu.
