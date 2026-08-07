# GIT_WORKFLOW.md — Estratégia de Git e Convenções

> Como versionar o EDY SIEM. Alinhado à estratégia de commits do projeto.

## Estado do repositório
- Repositório remoto: a definir (o push depende de um remoto configurado — ver WORKFLOW → Release).

## Práticas recomendadas
- **Commits pequenos e atômicos** (1 commit = 1 unidade lógica).
- **Mensagens descritivas no estilo Conventional Commits**:
  - `feat(...)`, `fix(...)`, `docs(...)`, `style(...)`, `refactor(...)`, `test(...)`,
    `chore(...)`, `build(...)`, `ci(...)`.
  - Ex.: `feat(api): adiciona endpoint X`, `fix(alerts): corrige dedup`, `style(ui): ajusta contraste`.
- **Nunca commitar:** segredos, `.env`, `node_modules`, `dist/`, bancos (`*.db*`), `__pycache__`,
  arquivos `UX_REVIEW/screenshots*`, `*.zip` (ver `.gitignore`).
- **Mensagens de release:** `chore(release): 0.2.0` + tag semântica.
- **Antes de commitar:** `git status` e `git diff --stat`; incluir apenas o intencional.

## Convenções de histórico (exemplos reais do projeto)
- `feat(api): Sprint Final P2 - seguranca em camadas (API Key opt-in, RBAC, rate limit)`
- `Sprint UI/UX Polish - Baseline`
- `style(dx): ruff fix (seed nao-fatal)`

## Garantia de qualidade (relacionada)
- Toda entrega deve ter **working tree limpa** ao terminar e os gates verdes (DERIVED).

## Push / publicar (comandos finais)
```bash
git remote -v                                  # conferir remoto
git add -A && git commit -m "chore(release): 0.2.0"
git tag -a release-0.2.0 -m "EDY SIEM 0.2.0"
git push origin master --tags                  # (ajuste o nome do branch/remoto conforme seu setup)
```

## Referências
- `docs/guides/GIT_WORKFLOW.md` · `docs/CONTRIBUTING.md` (se precisar de detalhes)