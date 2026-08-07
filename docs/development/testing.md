# EDY SIEM — Testing Guide

> Estratégia de testes. Sem testes não existe feature.

## 1. Pirâmide

```
        e2e (poucos, críticos)
       / \
      /   \
  integration (fluxos por camada)
    /          \
   /            \
unit (muitos, por módulo)
```

## 2. Camadas de teste

### Unit
- Por módulo/etapa, sem I/O real (storage em memória, syslog simulado).
- Cobre: modelos, parsers, regras, enrichers puros, validação.

### Integration
- Pipeline completo: ingestão simulada → normalização → enriquecimento → correlação →
  detecção → incidente → persistência (SQLite temporária).
- Storage temporário (tmp path) com fixture.

### E2E
- API REST ponta a ponta (autenticação, contratos, erros).
- CLI ponta a ponta.

## 3. Convenções

- Nomes: `test_<unidade>_<comportamento>`.
- Fixtures por escopo (funcion, module, session) — sem acoplamento entre testes.
- Cada regra (detection/correlation) possui fixtures de exemplo positivas e negativas.
- Cobertura alvo: ≥ 85% (gate CI realista, sem testes artificiais).

## 4. Ferramentas (gate obrigatório)

- `pytest` (verde)
- `mypy --strict` (0 issues)
- `ruff check` (limpo)
- `ruff format --check`
- Frontend: testes de componentes + `node --check` (quando UI existir)

## 5. Qualidade do teste

- Teste falha por razão clara (assertions descritivas).
- Não testar implementação; testar comportamento/contrato.
- Não criar testes apenas para bater número (regra explícita).
- Replay: dados de exemplo versionados em `examples/events/`.
