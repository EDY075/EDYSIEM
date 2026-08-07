# ADR-007 — Plugin System e Dependency Injection

- **Status:** Aceito
- **Data:** 2026-08-03

## Contexto
O EDY SIEM precisa crescer com novas fontes, parsers, enrichers e regras sem modificar o
núcleo (Princípio Aberto/Fechado). Testes precisam injetar fakes sem acoplar.

## Decisão
1. **Plugin System por registries**: `collectors`, `parsers`, `enrichers`, `rules`
   registrados em registries tipados (`core/contracts/`). Descoberta declarativa
   (config/setup), sem import mágico.
2. **Isolamento**: plugin falha → log + métrica + drop controlado; nunca derruba pipeline.
3. **Dependency Injection**: contêiner leve no bootstrap (`app/container.py`) monta o grafo.
   Serviços recebem interfaces (Protocol) injetadas, nunca instanciam dependências.
4. **Regras como dados**: YAML validado por schema; sem execução arbitrária (reforça ADR-004).

## Consequências
- (+) Extensível sem tocar no núcleo; testável com fakes.
- (+) Baixo acoplamento real entre camadas.
- (-) Custo inicial do contêiner/registries — compensa na manutenção.
- Manutenção em 1 ano: novo parser/regra = registrar + testar, sem refatorar pipeline.

## Critério "daqui a um ano"
Adicionar uma fonte de dados ou uma regra não exige alterar código de núcleo.
