# EDY SIEM — Git Workflow

> Fluxo Git profissional (Git Flow simplificado) + padrão de commits + versionamento.

## 1. Branches

```
main         → produção estável (tagged releases)
develop      → integração de features (estado "pronto para release")
feature/*    → nova funcionalidade (branch a partir de develop)
release/*    → preparação de release (a partir de develop)
hotfix/*     → correção urgente em produção (a partir de main)
```

| Branch | Origem | Merge em | Vida |
|---|---|---|---|
| `main` | — | — | eterna |
| `develop` | `main` | `main` (via release) | eterna |
| `feature/*` | `develop` | `develop` | curta (1 feature) |
| `release/*` | `develop` | `main` + `develop` | curta (preparação) |
| `hotfix/*` | `main` | `main` + `develop` | curta (urgência) |

## 2. Fluxo padrão

```
feature/alert-ui ──> develop ──> release/v1.0.0 ──> main (tag v1.0.0)
hotfix/login-bug ──> main ──> develop
```

1. Criar feature a partir de `develop`.
2. Desenvolver com commits atômicos.
3. PR para `develop`; CI verde obrigatório.
4. Reunião de release: `release/vX.Y.Z` a partir de `develop`.
5. PR release → `main` + tag semver.
6. Hotfix direto em `main` quando crítico.

## 3. Padrão de commits (Conventional Commits)

```
<type>(<escopo>): <descrição curta>

feat: nova funcionalidade
fix: correção de bug
docs: documentação
refactor: refatoração sem mudar comportamento
test: testes
chore: manutenção/ferramentas
ci: pipeline
build: build/pacote
perf: performance
style: formatação (sem lógica)
```

Exemplos:
- `feat(api): adiciona endpoint de criação de regra`
- `fix(correlation): corrige janela temporal em agregação`
- `docs(ux): wireframes da tela de triagem`

Regras: atomicidade (1 mudança lógica), mensagem no imperativo, sem `WIP` em main/develop.

## 4. Versionamento (SemVer)

```
MAJOR.MINOR.PATCH
```

- **MAJOR**: quebra de compatibilidade/arquitetura.
- **MINOR**: nova funcionalidade compatível.
- **PATCH**: correção de bug compatível.

Pré-release: `v1.0.0-rc.1`, `v1.0.0-beta.1`.
Tags apenas em `main`. Changelog gerado a partir dos commits (Keep a Changelog).

## 5. Releases

1. Branch `release/vX.Y.Z` a partir de `develop`.
2. Bump de versão (pyproject + app/__init__).
3. Changelog atualizado.
4. CI verde; testes completos.
5. PR para `main`; merge; **tag** `vX.Y.Z`.
6. GitHub Release com notas profissionais.
7. Merge release de volta em `develop`.

## 6. PR Checklist

- [ ] CI verde (pytest, mypy, ruff, coverage)
- [ ] Testes adicionados/atualizados
- [ ] Docs atualizadas (guia + ADR se decisão)
- [ ] Commit messages convencionais
- [ ] Sem secrets, sem debug, sem gambiarra
