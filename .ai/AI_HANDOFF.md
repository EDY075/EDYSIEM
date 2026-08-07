# AI_HANDOFF.md — Como assumir o projeto

> **Objetivo:** permitir que **qualquer agente de IA** continue o desenvolvimento
> do ponto atual **apenas lendo a pasta `.ai`**. Este é o documento de entrada.

## Como assumir (checklist obrigatório)

Leia, **nesta ordem**:

1. **[PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md)** — o que é o EDY SIEM e seu estado.
2. **[ARCHITECTURE.md](./ARCHITECTURE.md)** — onde está cada coisa (backend, frontend, API, pipeline).
3. **[TECH_STACK.md](./TECH_STACK.md)** — dependências e contrato de execução.
4. **[WORKFLOW.md](./WORKFLOW.md)** — como rodar, testar, build e publicar.
5. **[CODING_DECISIONS.md](./DECISIONS.md)** + **[CODING_STANDARDS.md](./CODING_STANDARDS.md)** + **[GIT_WORKFLOW.md](./GIT_WORKFLOW.md)**.
6. **[MEMORY_LOG.md](./MEMORY_LOG.md)** (antes) e **[KNOWLEDGE_BASE.md](./KNOWLEDGE_BASE.md)** (lições).
7. **[ROADMAP_AI.md](./ROADMAP_AI.md)** — onde parou e para onde ir.

> Se tiver pressa: leia `PROJECT_CONTEXT.md`, `ARCHITECTURE.md`, `WORKFLOW.md`. São suficientes para começar
> **sem quebrar nada**.

## Ponto exato de continuação (snapshot atual)

- **Versão:** `0.2.0`
- **Último release:`0.2.0-rc.1`
- **Fase:** Sprints 2.1–2.17 concluídas + UI 3.x/4.x concluída. **Próxima: Sprint 2.18 (Escala)** —
  fila externa Kafka, storage PostgreSQL por Protocol e auth/SSO.
- **Working tree:** limpa (baseline commit `Sprint UI/UX Polish - Baseline`).
- **Servidores** (se iniciados): backend `127.0.0.1:8080` (uvicorn), frontend `localhost:5173` (vite).
- **Publicação:** commit + tag `release-0.2.0` locais; **push pendente (sem remoto configurado)**.

## O que fazer ao assumir

1. **Confirme o ambiente:** `git status` (árvore limpa?) e `git log -1`.
2. **Suba o ambiente** com o comando único: `python run.py` (ver **[WORKFLOW.md](./WORKFLOW.md)**).
3. **Rode os gates** para confirmar que o estado está verde.
4. **Escolha a tarefa** da `ROADMAP..md` (próxima sprint 2.18 ou pendências de release 0.2.0).
5. **Nunca** pule o Quality Gate nem altere contrato sem ADR (ver **[AGENTS.md](./AGENTS.md)**).

## Ao concluir qualquer tarefa

- Atualize `ROADMAP.md`/`CHANGELOG.md` (se afetar lançamento).
- Registre em **[MEMORY_LOG.md](./MEMORY_LOG.md)** (o que fez, decisões, pendências).
- Use a célula do **[KNOWLEDGE_BASE.md](./KNOWLEDGE_BASE.md)** se descobrir uma lição.
- Roda os gates de qualidade (build + testes) e **vermelho os committers**.
- Mantenha a **working tree limpa**.

## O que NUNCA fazer

- **Não** introduzir dados fictícios no frontend.
- **Não** alterar o `core` (stdlib puro) sem ADR.
- **Não** subir uma feature sem ADR/contrato.
- **Não** deixar mais de um agente editando o mesmo arquivo simultaneamente.

> Se você está retomando após pausa longa, leia também **`docs/CHANGELOG.md`** e os `SPRINT*_REPORT.md`
> da raiz para contexto detalhado das sprints já entregues.