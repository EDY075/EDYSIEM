# EDY SIEM — Backend Guide

> Guia de desenvolvimento do backend. Como cada camada é organizada e como testá-la.
> Atualizado em 2026-08-03 para a estrutura `src/edysiem/` e a pipeline oficial.

## 1. Estrutura

```
src/edysiem/
├── domain/          # entidades, enums, value objects (puros, sem I/O)
├── result/          # Result[T], ErrorCode (nunca None)
├── exceptions/      # hierarquia de exceções
├── events/          # Event Bus (base, registry, bus)
├── config/          # configuração tipada (env-driven)
├── logging/         # log estruturado JSON + trace_id
├── plugins/         # Protocols de extensibilidade (coletores, parsers, ...)
├── di/              # container de injeção de dependência
├── validation/      # motor declarativo de validação
├── collectors/      # (futuro) syslog, file_watcher, manual
├── parsers/         # (futuro) parsers por source_type
├── ingestion/       # (futuro) ingestor + filas
├── normalization/   # (futuro) conversão para CanonicalEvent
├── enrichment/      # (futuro) asset, geo, threat_intel
├── correlation/     # (futuro) correlation engine
├── detection/       # (futuro) detection engine + rule engine
├── incident/        # (futuro) incident engine
├── persistence/     # (futuro) repositórios (SQLite via Protocol)
├── api/             # (futuro) REST v1 (handlers)
├── cli/             # (futuro) comandos
└── ui/              # (futuro) static do frontend
```

## 2. Pipeline oficial

```
Collector → RawEvent → Parser → ParsedEvent → Normalizer → CanonicalEvent
→ Enrichment → EnrichedEvent → Correlation → Detection → Alert → Incident → Case
```

Cada estágio é uma função pura de transformação com contrato tipado. Os modelos
que trafegam entre os estágios são **imutáveis** (`@dataclass(frozen=True)`).

## 3. Regras por camada

- **domain**: importa NADA de outras camadas. Define modelos e interfaces.
- **result/exceptions**: folhas consumidas por todas as camadas.
- **collectors/parsers/ingestion/normalization/enrichment**: dependem apenas de
  `domain` + `result` + `plugins` (contratos).
- **correlation/detection/incident**: dependem de `domain` + resultados de etapas anteriores.
- **persistence**: implementa Protocol de `domain`; nada sabe de HTTP/CLI.
- **api/cli**: adaptadores; orquestram serviços; nunca contêm regra de negócio.

## 4. Exemplo de contrato (Protocol)

```python
class EventRepository(Protocol):
    def append(self, event: CanonicalEvent) -> None: ...
    def search(self, query: EventQuery) -> list[CanonicalEvent]: ...
    def count(self, query: EventQuery) -> int: ...
```

## 5. Modelos da pipeline (Sprint 2.1)

| Modelo | Estágio de origem | Imutável | Campos principais |
|---|---|---|---|
| `RawEvent` | Collector | ✅ | source, raw_payload, timestamp |
| `ParsedEvent` | Parser | ✅ | campos estruturados extraídos + raw |
| `CanonicalEvent` | Normalizer | ✅ | modelo canônico (severity, user, ip, host...) |
| `EnrichedEvent` | Enrichment | ✅ | canônico + enrichments |

Todos seguem **Result Pattern**: as etapas retornam `Result[T]` (nunca `None`).

## 6. Como desenvolver uma feature

1. Escrever/atualizar ADR se houver decisão arquitetural.
2. Definir modelo no `domain` + testes unitários do modelo.
3. Implementar etapa (função pura) + testes.
4. Implementar/atualizar repositório + testes de integração.
5. Expor via API/CLI + testes e2e.
6. Documentar no guia correspondente (API_GUIDE, STUDY_GUIDE).

## 7. Testes

- `tests/`: por módulo (sem I/O real).
- `tests/integration/`: (futuro) pipeline completo com storage temporário.
- `tests/e2e/`: (futuro) API/CLI ponta a ponta.

## 8. Boas práticas

- Funções puras na transformação de eventos (facilita teste e replay).
- Nunca importar `persistence` dentro de `detection` fora do contrato.
- `trace_id` obrigatório no contexto de processamento (ver ADR-006).
- Eventos da pipeline nunca são mutados: enriquecimento cria `EnrichedEvent` derivado.
