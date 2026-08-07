# EDY SIEM — Relatório de Release 0.2.0

Data da revisão: 2026-08-06

## Resultado

Release pronta para publicação no Git. A árvore foi revisada, os contratos SOC e as
rotas da SPA foram verificados, e não há bloqueadores de build, testes ou abertura
das telas.

## Validações executadas

- `pytest`: 800 aprovados, cobertura total de 95,07%.
- `mypy`: sem problemas em 147 arquivos.
- `ruff check .`: aprovado.
- `npx tsc -b` e `npm run build`: aprovados.
- Ambiente em execução: `GET /api/v1/health`, os endpoints SOC e as rotas da SPA
  responderam com sucesso.

## Correções de estabilização

- O healthcheck agregado passou a aceitar os estados saudáveis produzidos pelos
  engines (`healthy`) e pelos componentes SOC (`online`).
- Corrigida codificação quebrada no `SocService`, inclusive a mensagem exibida pelo
  simulador de regras.

## Pendência não bloqueante

Em um banco de desenvolvimento já populado, `POST /api/v1/soc/pipeline/demo` pode
retornar 500 durante o seed. O runner registra o aviso e continua; as APIs e telas
SOC permanecem utilizáveis. Para reutilizar esse banco sem novo seed, execute
`python run.py --no-seed`. A investigação da causa raiz fica fora deste release.

## Publicação

O repositório não possui remoto configurado nesta revisão; portanto não há push a
executar. A tag `v0.2.0` já aponta para o checkpoint anterior da Sprint 2.13 e foi
preservada; este fechamento recebe a tag anotada `release-0.2.0`. Após adicionar um
remoto, publique o commit de release e essa tag.
