# EDY SIEM — Relatório de Release 0.2.0

Data da revisão: 2026-08-06

## Resultado

Release pronta para publicação no Git. A árvore foi revisada, os contratos SOC e as
rotas da SPA foram verificados, e não há bloqueadores de build, testes ou abertura
das telas.

## Validações executadas

- `pytest`: 801 aprovados, cobertura mínima de 95% atingida.
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
- O seed `/soc/pipeline/demo` passou a reutilizar alertas e incidentes persistidos
  pelo fingerprint, além do case já vinculado ao incidente.

## Seed repetível

O seed pode ser executado repetidamente, inclusive após reiniciar a aplicação. Os
dados de demonstração existentes são reutilizados; nenhum registro persistido é
removido. `python run.py --no-seed` continua disponível para iniciar sem seed.

## Publicação

O repositório não possui remoto configurado nesta revisão; portanto não há push a
executar. A tag `v0.2.0` já aponta para o checkpoint anterior da Sprint 2.13 e foi
preservada; este fechamento recebe a tag anotada `release-0.2.0`. Após adicionar um
remoto, publique o commit de release e essa tag.
