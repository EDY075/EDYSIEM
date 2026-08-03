# Contribuindo para o EDY SIEM

> Processo de contribuição. Padrão profissional desde o início.

## 1. Princípios

- Qualidade de arquitetura antes de velocidade (Regra Nº 1).
- Toda mudança exige: código + testes + docs.
- Nunca quebre o gate: pytest, mypy strict, ruff, coverage ≥ 85%.

## 2. Fluxo

1. Abra uma issue descrevendo o problema/melhoria.
2. Discuta a abordagem; se houver decisão arquitetural, proponha ADR.
3. Faça fork/branch (`feat/nome`, `fix/nome`, `docs/nome`).
4. Implemente seguindo `CODING_STANDARD.md`.
5. Adicione testes (`TESTING_GUIDE.md`).
6. Atualize documentação (guia correspondente + STUDY_GUIDE se didático).
7. Envie PR; CI deve ficar verde.

## 3. Padrões de commit

`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`, `ci:`, `build:`.
Commit atômico: uma mudança lógica por commit.

## 4. Review

- Responsabilidade única, tipagem, testes, docs.
- Nada de gambiarra/dependência desnecessária.
- Critério "daqui a um ano": a mudança facilita ou dificulta evolução?

## 5. Código de conduta

Respeito, colaboração e foco em qualidade. Ver `CODE_OF_CONDUCT.md` (criar na S0.6).
