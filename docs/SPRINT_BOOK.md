# EDY SIEM — Sprint Book

> Registro oficial de todas as sprints. **Toda sprint futura deve ser registrada aqui**
> antes de iniciar e revisada ao final (lições aprendidas).

## Formato obrigatório de registro

```markdown
## Sprint N.N — <Título>

- **Status:** Planejada | Em andamento | Concluída
- **Data:** ...
- **Objetivo:** ...
- **Escopo:** ...
- **Arquivos afetados:** ...
- **Resultado:** ...
- **Lições aprendidas:** ...
- **Pendências:** ...
```

## Histórico

### Sprint 0 — Fundação
- **Status:** Concluída
- **Objetivo:** visão, arquitetura, modelagem, UX, design system, estrutura.
- **Arquivos:** `docs/` completo (visão, arquitetura, ADRs, design, UX, wireframes), `README.md`, `PROJECT_MANIFESTO.md`.
- **Resultado:** fundação documental completa; zero funcionalidade.
- **Lições:** critério "daqui a um ano" em toda decisão; benchmark orientou direcionamentos.

### Sprint 0.1 — Manifesto
- **Status:** Concluída
- **Objetivo:** posicionamento Enterprise do produto.
- **Arquivos:** `PROJECT_MANIFESTO.md`.
- **Resultado:** missão, visão, valores, não-objetivos, compromisso.

### Sprint 0.2 — Benchmark
- **Status:** Concluída
- **Objetivo:** estudar 9 SIEMs comerciais.
- **Arquivos:** `docs/research/benchmark.md`.
- **Resultado:** tabela comparativa + direcionamentos (modelo canônico, MITRE, incident aggregator, entity-centric, risk score).
- **Lições:** inspiração, nunca cópia.

### Sprint 0.3 — Design System
- **Status:** Concluída
- **Objetivo:** design system completo criado do zero.
- **Arquivos:** `docs/design/{DESIGN_SYSTEM,COMPONENT_LIBRARY,DESIGN_GUIDE,UI_GUIDE}.md`.
- **Resultado:** tokens, componentes, padrões, DoR UI.

### Sprint 0.4 — Arquitetura
- **Status:** Concluída
- **Objetivo:** arquitetura completa + dataflow.
- **Arquivos:** `docs/{ARCHITECTURE,SYSTEM_DESIGN,DATAFLOW}.md`, ADR-007.
- **Resultado:** fluxo etapa por etapa, Clean Architecture, SOLID, DI, plugin system.

### Sprint 0.5 — UX Architecture
- **Status:** Concluída
- **Objetivo:** projetar toda experiência do usuário.
- **Arquivos:** `docs/design/{UX_ARCHITECTURE,SCREEN_MAP,USER_JOURNEY,UX_FLOW,WIREFRAMES}.md`.
- **Resultado:** 4 perguntas por tela, jornadas por perfil, wireframes ASCII.

### Sprint 0.6 — Enterprise Foundation
- **Status:** Concluída
- **Objetivo:** infraestrutura Enterprise (docs de convenções, qualidade, logging, eventos, banco, API, git).
- **Arquivos:** `docs/{PROJECT_STRUCTURE}.md`, `docs/guides/{CODING,GIT_WORKFLOW,QUALITY,LOGGING_DESIGN,EVENT_BUS}.md`, `docs/{DATABASE_DESIGN,API_DESIGN}.md`, `docs/SPRINT_BOOK.md`.
- **Resultado:** fundação Enterprise pronta para Sprint 1.
- **Lições:** documentação como produto; nada de código sem contrato.

## Próximas sprints (planejadas)

- **S1.1** — Núcleo: `core` (modelos, erros, contratos, logging, config) + testes.
- **S1.2** — Persistência: SQLite, migrações, repositórios + testes.
- **S1.3** — Pipeline: ingestion, normalization (parser syslog) + testes.
- **S1.4** — Enrichment: enricher base + asset/intel + testes.
- **S1.5** — Correlation/Detection: rule engine + MITRE + testes.
- **S1.6** — Incident engine + ciclo de vida.
- **S1.7** — API v1 + CLI + health.
- **S1.8** — UI v0: shell + tokens + tela Events/Alerts.
