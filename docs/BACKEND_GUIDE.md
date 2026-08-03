# EDY SIEM — Backend Guide

> Guia de desenvolvimento do backend. Como cada camada é organizada e como testá-la.

## 1. Estrutura

```
app/
├── core/            # dominio puro (modelos, erros, contratos) - sem I/O
│   ├── events.py    # CanonicalEvent, RawEvent
│   ├── alerts.py    # Alert
│   ├── incidents.py # Incident
│   ├── rules.py     # DetectionRule, CorrelationRule
│   ├── ioc.py
│   ├── assets.py
│   ├── errors.py
│   └── contracts.py # Protocols entre camadas
├── collectors/      # syslog, file_watcher, manual
├── ingestion/       # ingestor + filas
├── normalization/   # parsers por source_type
├── enrichment/      # geo, asset, threat_intel
├── correlation/     # correlation engine
├── detection/       # detection engine + rule engine
├── incident/        # incident engine
├── persistence/     # repositórios (SQLite via Protocol)
├── api/             # REST v1 (handlers)
├── cli/             # comandos
└── ui/              # static do frontend
```

## 2. Regras por camada

- **core**: importa NADA de outras camadas. Define modelos e interfaces.
- **collectors/ingestion/normalization/enrichment**: dependem apenas de `core`.
- **correlation/detection/incident**: dependem de `core` + resultados de etapas anteriores.
- **persistence**: implementa Protocol de `core`; nada sabe de HTTP/CLI.
- **api/cli**: adaptadores; orquestram serviços; nunca contêm regra de negócio.

## 3. Exemplo de contrato (Protocol)

```python
class EventRepository(Protocol):
    def append(self, event: CanonicalEvent) -> None: ...
    def search(self, query: EventQuery) -> list[CanonicalEvent]: ...
    def count(self, query: EventQuery) -> int: ...
```

## 4. Como desenvolver uma feature

1. Escrever/atualizar ADR se houver decisão arquitetural.
2. Definir modelo no `core` + testes unitários do modelo.
3. Implementar etapa (função pura) + testes.
4. Implementar/atualizar repositório + testes de integração.
5. Expor via API/CLI + testes e2e.
6. Documentar no guia correspondente (API_GUIDE, STUDY_GUIDE).

## 5. Testes

- `tests/unit/`: por módulo (sem I/O real).
- `tests/integration/`: pipeline completo com storage temporário.
- `tests/e2e/`: API/CLI ponta a ponta.

## 6. Boas práticas

- Funções puras na transformação de eventos (facilita teste e replay).
- Nunca importar `app.persistence` dentro de `app.detection` fora do contrato.
- `trace_id` obrigatório no contexto de processamento (ver ADR-006).
