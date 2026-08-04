# EDY SIEM — Architecture

> Arquitetura de referência. Define camadas, fluxo de dados e regras de dependência.
> Todo código deve respeitar estas fronteiras. Nenhuma camada acessa outra fora do fluxo.

## 1. Fluxo do sistema

```mermaid
flowchart LR
    subgraph Entrada
        ES[Event Sources]
        COL[Collectors]
        RAW[RawEvent]
        PAR[Parser]
        PARSED[ParsedEvent]
        NORM[Normalization]
    end
    subgraph Processamento
        CANON[CanonicalEvent]
        ENR[Enrichment]
        ENRICHED[EnrichedEvent]
        CORR[Correlation Engine]
        DET[Detection Engine]
        INC[Incident Engine]
    end
    subgraph Saida
        PERS[Persistence]
        API[REST API]
        UI[Dashboard]
        CLI[CLI]
    end

    ES --> COL --> RAW --> PAR --> PARSED --> NORM --> CANON --> ENR
    ENR --> ENRICHED --> CORR --> DET --> INC --> PERS
    PERS --> API --> UI
    PERS --> CLI
    DET --> CORR
```

> **Pipeline oficial (ADR-008):** `Collector → RawEvent → Parser → ParsedEvent →
> Normalizer → CanonicalEvent → Enrichment → EnrichedEvent → Correlation →
> Detection → Alert → Incident → Case`. Cada modelo é imutável
> (`@dataclass(frozen=True)`) e cada estágio é uma função pura de transformação.

## 2. Camadas e responsabilidade única

| Camada | Responsabilidade | Proibido |
|---|---|---|
| `collectors` | Conectar a fontes (syslog, arquivos, API) e emitir `RawEvent` via `CollectorPlugin` | Normalizar, persistir |
| `ingestion` | Fila FIFO + backpressure + retry + dead letter + rate limit + health + métricas | Conhecer parsers |
| `parsers` | Extrair campos estruturados do `RawEvent` → `ParsedEvent` | Correlacionar |
| `normalization` | Converter `ParsedEvent` para o **modelo de evento canônico** (`CanonicalEvent`) | Enriquecer |
| `enrichment` | Adicionar contexto (geo, WHOIS, asset, threat intel) → `EnrichedEvent` | Persistir |
| `correlation` | Agregar eventos relacionados (janela, identidade) | Detectar sozinho |

> **Implementado (Sprint 2.5):** `src/edysiem/correlation/` - ``CorrelationRule`` Protocol com
> metadata declarativos, ``CorrelationRegistry`` (ordenacao topologica por prioridade +
> dependencias), ``CorrelationEngine`` (janelas temporais via ``CorrelationContext``, isolamento
> de falhas, timeout por regra, metricas). Regras declarativas, sem hardcode. Ver
> `docs/PIPELINE.md` e `src/edysiem/correlation/plugins/README.md`.
| `detection` | Aplicar detection rules e gerar alertas (MITRE) | Resolver incidentes |

> **Implementado (Sprint 2.6):** `src/edysiem/detection/` - ``DetectionRule`` Protocol + ``RuleMetadata``
> declarativos (severidade, confianca, risco), ``RuleEngine`` (carregar/registrar/validar/executar regras
> com isolamento de falhas e timeout), ``DetectionEngine`` (produz ``DetectionOutcome``/``DetectionDecision``
> a partir de ``CorrelatedEvent``) e DSL declarativa (``WHEN ... AND ... THEN``). Sem Alert ainda.
> Ver `src/edysiem/detection/plugins/README.md`.
| `incident` | Agrupar alertas em incidentes e gerir ciclo de vida | Normalizar |

> **Implementado (Sprint 2.7):** `src/edysiem/alerts/` - ``AlertEngine`` orquestra o ciclo de vida completo:
> ``RiskEngine`` (fatores), ``FingerprintEngine`` (SHA-256 deterministico), ``AlertBuilder``,
> ``DedupEngine`` (occurrences+1), ``LifecycleManager`` (OPEN->TRIAGE->INVESTIGATING->RESOLVED/FALSE_POSITIVE).
> ``Alert`` operacional pronto para SOC. Ver `src/edysiem/alerts/README.md`.
| `persistence` | Armazenar eventos, alertas, incidentes, regras | Aplicar regras |
| `api` | Expor contratos REST estáveis | Acessar UI |
| `ui` | Experiência do operador (consultas, triagem, investigação) | Acessar persistência direto |
| `cli` | Operações via terminal (ingestão manual, consultas, admin) | Acessar UI |

> A infraestrutura de ingestão (`src/edysiem/ingestion/`) é **desacoplada**
> (ADR-009): fila, backpressure, retry, dead letter, rate limit, health e
> métricas são reutilizáveis por qualquer coletor. Ver `docs/PIPELINE.md`.

## 3. Regras de dependência (obrigatórias)

1. **Direção única:** Entrada → Processamento → Persistência → Saída.
2. **Nunca** uma camada de processamento acessa `persistence` fora do fluxo definido.
3. **Nunca** a UI acessa `persistence` diretamente — somente via API.
4. **Contratos entre camadas** (schemas) são definidos em `core` e compartilhados.
5. Cada camada é um módulo Python com API pública explícita (`__init__.py`).
6. Dependências entre camadas usam **interfaces** (Protocol) — nunca classes concretas de outra camada.

## 4. Modelos da pipeline (visão geral)

A pipeline oficial trafega quatro modelos imutáveis (definidos em
`src/edysiem/domain/pipeline.py`):

| Modelo | Estágio de origem | Campos principais |
|---|---|---|
| `RawEvent` | Collector | source_type, source_host, raw_payload, received_at |
| `ParsedEvent` | Parser | event_id, timestamp, event_type, fields, raw, trace_id |
| `CanonicalEvent` | Normalizer | event_id, severity, user, process, ip_src, ip_dst, hostname, trace_id |
| `EnrichedEvent` | Enrichment | CanonicalEvent + enrichments (tupla de `Enrichment`) |

```mermaid
classDiagram
    class RawEvent {
        +source_type
        +source_host
        +raw_payload
        +received_at
    }
    class ParsedEvent {
        +event_id
        +timestamp
        +event_type
        +fields
        +trace_id
    }
    class CanonicalEvent {
        +event_id
        +timestamp
        +severity
        +user
        +process
        +ip_src
        +ip_dst
        +hostname
        +trace_id
    }
    class EnrichedEvent {
        +enrichments
    }
    CanonicalEvent <|-- EnrichedEvent
```

Detalhes do schema: `docs/DATABASE.md` e `docs/API_GUIDE.md` (contrato).

## 5. Estilo de arquitetura

- **Clean Architecture** com dependências apontando para o centro (domínio).
- **Ports & Adapters** para coletores, storage e enrichments.
- **Eventos como dados imutáveis** — um evento nunca é alterado após a normalização;
  enriquecimento cria eventos derivados anexados (não muta o original).
- **Pipeline linear** processado de forma idempotente (replay seguro).

## 6. Decisões de arquitetura

Toda decisão técnica relevante é registrada em `docs/adr/` com formato:
`ADR-NNN-titulo.md` (status, contexto, decisão, consequências).

Índice de ADRs: `docs/DECISIONS.md`.

## 7. Dependency Injection e Plugin System

- **DI**: contêiner leve no bootstrap (`app/container.py`) monta o grafo; serviços recebem
  interfaces (Protocol) injetadas — nunca instanciam dependências. Testes usam fakes.
- **Plugins**: registries tipados para `collectors`, `parsers`, `enrichers`, `rules`.
  Descoberta declarativa (config/setup); falha de plugin degrada, não derruba pipeline.
- **Detalhes:** `docs/DATAFLOW.md` §5–6 e `ADR-007`.

## 8. Critério transversal

Toda decisão deve responder: **como afeta manutenção, escalabilidade e UX daqui a um ano?**
Registrado no manifesto (`PROJECT_MANIFESTO.md` §9).
