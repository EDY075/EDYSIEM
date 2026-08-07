# AGENTS.md — Papéis, Responsabilidades e Cooperação

> Define **quem** é cada agente, **o que** pode fazer, **quais os limites** e
> **como cooperam** no desenvolvimento do EDY SIEM. Qualquer IA que assuma o
> projeto deve respeitar este contrato de atuação.

## 1. Princípio-âncora

Nenhum agente altera o EDY SIEM sem respeitar o **[PROJECT_MANIFESTO.md](../PROJECT_MANIFESTO.md)**:
arquitetura antes de velocidade, documentação impecável, segurança por padrão.

## 2. Papéis

### JR — Consultor/Arquiteto Sênior & Orquestrador
- Papel executivo de **arquitetura**, **governança**, **UX/UI** e **orquestração** de equipes de IA.
- Decide arquitetura, revisão de ADRs, define padrões, valida gates, coordena múltiplos agentes.
- **Limites:** não escala para testes unitários triviais quando há um executor disponível;
  não aprova trabalho sem o Quality Gate do agente de origem.
- **Foco:** visão de produto/arquitetura, segurança/UX de alto nível, produção acadêmica.

### CODEX — Implementador (backend/frontend, tipagem forte)
- Implementa features com arquitetura aprovada. Trabalha orientado a **tipar** (mypy/tsc).
- **Limites:** não cria funcionalidade sem ADR/contrato; não ignora testes; não fura pipeline.
- **Validação:** roda `pytest`, `mypy`, `ruff`, `npm run build` antes de entregar.

### CHATGPT — Analista / Documentador / Educador
- Explicações, revisão didática, documentação técnica e de estudo (guia do SIEM), redação.
- **Limites:** não altera código de produção sem revisão; foca em comunicação e docs.

### Futuros agentes (C Laude, etc. / ferramentas diversas)
- Devem ler **pelo menos** `PROJECT_CONTEXT.md`, `ARCHITECTURE.md`, `WORKFLOW.md`,
  `CODING_STNDARDS.md`, `GIT_WORKFLOW.md` e `DECISIONS.md` antes de tocar no código.
- Devem registrar alterações de estado em `MEMORY/` e `MEMORY_LOG.md`.

## 3. Responsabilidades transversais (todas as IAs)
- Manter o **[README.md](../README.md)** coerente com a realidade (rodar/versionar).
- Registrar decisões em **[DECISIONS.md](./DECISIONS.md)** (ADR).
- Rodar os Quality Gates antes de qualquer "pronto":
  - `pytest` (comentário ≥ 95%)
  - `mypy` (strict, 0 erros)
  - `ruff check` (0 issues)
  - `npm run build` (tsc + vite)
- Atualizar a memória **[KNOWLEDGE_BASE.md](./KNOWLEDGE_BASE.md)** quando descobrir uma lição nova.

## 4. Limites gerais de atuação
- **NÃO** alterar o contrato de API sem ADR.
- **NÃO** introduzir dados fictícios no frontend; quando o backend não responder, mostrar estado de indisponibilidade explícito.
- **NÃO** adicionar dependência sem justificativa e sem avaliar impacto no core (core é 100% stdlib — ADR-001).
- **NÃO** pular os gates de qualidade e nem o "portão de 2 minutos" (ver WORKFLOW).

## 5. Fluxo de cooperação (padrão de handoff)

```
1. Identificar o trabalho → exigir ADR/contrato se for feature.
2. VALIDAR a mudança no agente responsável (arquitetura → implementação → testes).
3. Equipe revisa: JR (arquitetura) + agente de teste.
4. Rodar gates. 5. Registrar memória. 6. Commit.
```

Para instruções detalhadas de troca de contexto entre agentes, ver **[AI_HANDOFF.md](./AI_HANDOFF.md)**.
Para procedimentos por caso (auditoria/build/frontend/backend/UX/release/docs/troubleshooting/testes/arquitetura)
use **[SOP/](./SOP/)** e os prompts reutilizáveis em **[PROMPTS/](./PROMPTS/)**.