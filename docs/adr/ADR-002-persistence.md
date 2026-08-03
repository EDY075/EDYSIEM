# ADR-002 — Persistência

- **Status:** Aceito
- **Data:** 2026-08-03

## Contexto
SIEMs reais lidam com grandes volumes. Precisamos de armazenamento correto para eventos
(append-heavy), metadados (consultas SOC) e regras/estado (CRUD transacional).

## Decisão
**SQLite (stdlib)** como persistência transacional na fundação, com **repositórios por agregado**
e contratos de interface (Protocol). O acesso a dados fica isolado em `persistence`, permitindo
trocar o motor no futuro (PostgreSQL) sem tocar nas camadas superiores.

- Eventos: tabela append-only com índices (timestamp, source, host).
- Regras/IOCs/Assets: tabelas CRUD.
- JSONB/JSON para payloads enriquecidos.

## Consequências
- (+) Zero dependência de infra na fundação; reproduzível em estudo.
- (+) Replay/export fáceis.
- (-) Volume alto exigirá particionamento/retention — tema de Sprint futura (ADR quando chegar).
- Manutenção em 1 ano: trocar storage = implementar Protocol, não refatorar pipeline.

## Critério "daqui a um ano"
A camada `persistence` expõe interfaces estáveis; o motor é detalhe interno.
