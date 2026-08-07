# Contribuindo para o EDY SIEM

Obrigado por ajudar a evoluir o EDY SIEM. Mantenha cada contribuição pequena,
testável e documentada.

## Fluxo de contribuição

1. Abra uma issue descrevendo o problema ou melhoria.
2. Discuta a abordagem; decisões arquiteturais relevantes devem propor uma ADR.
3. Crie uma branch (`feat/nome`, `fix/nome` ou `docs/nome`).
4. Siga o [padrão de código](docs/development/coding-standard.md).
5. Adicione ou atualize testes conforme o [guia de testes](docs/development/testing.md).
6. Atualize a documentação relacionada; para material didático, consulte o [guia de estudo](docs/product/study-guide.md).
7. Envie uma pull request com a CI verde.

## Quality gate

```bash
python -m pytest
python -m mypy
python -m ruff check .
cd frontend && npm run build && npx tsc -b
```

## Commits e review

Use commits atômicos com os prefixos `feat:`, `fix:`, `docs:`, `test:`, `refactor:`,
`chore:`, `ci:` ou `build:`. Em review, priorize tipagem, testes, documentação,
compatibilidade e clareza de manutenção.

## Conduta

Mantenha respeito, colaboração e foco em qualidade em toda interação.
