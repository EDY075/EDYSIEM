# EDY SIEM — Sprint 1 Checklist Técnico

> Critérios para iniciar a Sprint 1 e para considerar cada entregável pronto.
> Nada de código antes de a arquitetura estar aprovada (Regra Nº 1).

## 1. Gate de entrada (tudo obrigatório)

- [ ] S0.4 UX: fluxos de telas e wireframes aprovados
- [ ] S0.5 Design System: tokens e componentes base definidos
- [ ] S0.6 Estrutura do projeto criada com CI básico
- [ ] ADRs 001–006 revisados e aprovados
- [ ] Este checklist aprovado por EDY

## 2. Definition of Done (por entregável)

- [ ] Código tipado (mypy strict 0 issues)
- [ ] Testes (unit + integração) verdes; coverage ≥ 85%
- [ ] ruff check + format limpos
- [ ] Contrato documentado (API/CLI/schema) quando aplicável
- [ ] Guia de estudo atualizado quando didático
- [ ] ADR criado/atualizado quando decisão arquitetural
- [ ] Sem gambiarra, sem duplicação, sem dependência desnecessária

## 3. Ordem sugerida (S1)

1. `core`: modelos + erros + contratos (tipados) + testes
2. `persistence`: SQLite + migrações + repositórios + testes
3. `ingestion`/`normalization`: ingestão manual + parser syslog + testes
4. `enrichment`: enricher base + asset/intel + testes
5. `correlation`/`detection`: rule engine declarativo + MITRE + testes
6. `incident`: engine + ciclo de vida + testes
7. `api` v1 + `cli` + health
8. `ui` v0: shell + tokens + tela Events/Alerts

## 4. Riscos a vigiar

- Escopo inflando (usar YAGNI).
- Fronteiras vazando (revisar imports por camada).
- Testes artificiais para bater cobertura (proibido).
- Dependência nova sem justificativa (ADR exigido).
