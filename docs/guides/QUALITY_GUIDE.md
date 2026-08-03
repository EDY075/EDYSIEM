# EDY SIEM — Quality Guide

> Definições de qualidade do projeto. Gate obrigatório em todo PR e release.

## 1. Cobertura mínima

- Alvo: **≥ 85%** (gate CI realista, sem testes artificiais).
- Módulos críticos (pipeline, detecção, correlação) exigem ≥ 90%.
- Cobertura por teste real de comportamento, nunca para bater número.

## 2. Lint e formato

- **ruff check**: limpo (regras E/F/W/I/UP/B/SIM/ARG/C4/RUF).
- **ruff format --check**: formatado.
- Per-file-ignores para fixtures de teste (ARG), produção sempre estrita.

## 3. Tipagem

- **mypy --strict**: 0 issues em `app/`.
- `Any` apenas em fronteiras JSON.

## 4. Complexidade

- Funções curtas (ideal < 30 linhas; máx 60).
- Arquivos < ~300 linhas; cresceu → dividir (responsabilidade única).
- Evitar aninhamento profundo (guard clauses).
- Duplicação: DRY — extrair quando repetição real (não premature).

## 5. Performance

- Nenhuma consulta N+1 no storage.
- Pipeline com backpressure; sem bloqueio global.
- Regras avaliadas com limites (timeout, janela).
- Referência: carregar lista de alertas < 500ms (dados de teste).

## 6. Documentação

- Código: docstrings de módulo/classe/função pública.
- Docs de produto: guia correspondente por feature.
- ADR para decisão arquitetural.
- Sprint Book registrado (ver SPRINT_BOOK.md).

## 7. Code Review

Critérios de review:
- Responsabilidade única; baixo acoplamento.
- Tipagem e tratamento de erros corretos.
- Testes cobrem comportamento real.
- Docs atualizadas.
- Nenhuma gambiarra/dependência desnecessária.
- Critério "daqui a um ano".

## 8. Checklist PR (obrigatório)

- [ ] CI verde (pytest, mypy, ruff, coverage ≥ 85%)
- [ ] Testes novos/atualizados
- [ ] Docs atualizadas
- [ ] Sem secrets/debug/gambiarra
- [ ] Commit convencional
- [ ] Critério "daqui a um ano" considerado

## 9. Definition of Done (feature)

- [ ] Código implementado e tipado
- [ ] Testes (unit + integração)
- [ ] API/CLI com contrato documentado
- [ ] Guia de estudo atualizado (quando didático)
- [ ] ADR criado (quando decisão)
- [ ] CI verde
