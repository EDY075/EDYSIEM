# ADR-004 — Regras Declarativas (Detection & Correlation)

- **Status:** Aceito
- **Data:** 2026-08-03

## Contexto
Engenheiros de detecção precisam criar regras sem escrever código Python. Regras devem ser
versionáveis, testáveis e mapeadas a MITRE ATT&CK.

## Decisão
**Regras declarativas em YAML/JSON**, carregadas por um engine de regras com DSL limitada
(operadores, agregações, janelas). Regras são dados, não código.

- DetectionRule: `id, name, severity, mitre {tactic, technique}, condition, timeframe, enabled`.
- CorrelationRule: `id, name, group_by, window, aggregation, condition`.
- Regras validadas por schema (sem execução arbitrária).

## Consequências
- (+) Segurança (regra não executa código arbitrário).
- (+) Versionável e auditável (git).
- (+) Testável: cada regra tem fixtures de exemplo.
- (-) DSL limitada por design; casos complexos exigem plugin Python explícito (futuro).
- Manutenção em 1 ano: novas regras = adicionar YAML + testes, sem deploy de código.

## Critério "daqui a um ano"
Um analista cria/ajusta regra em minutos e entende o impacto por testes.
