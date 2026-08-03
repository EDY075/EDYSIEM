# ADR-008 — Pipeline Oficial de Eventos

- **Status:** Aceito
- **Data:** 2026-08-03

## Contexto
O EDY SIEM precisa de um fluxo de eventos explícito e imutável, do bruto ao
enriquecido, para sustentar a operação SOC. A modelagem anterior era ambígua:
o `ParserPlugin` produzia `RawEvent`, e o enriquecimento mutava o próprio
evento (violava o princípio de imutabilidade). A auditoria da Sprint 2.1
identificou a necessidade de estágios e modelos bem definidos entre cada
transformação.

## Decisão
A pipeline oficial passa a ser:

```
Collector → RawEvent → Parser → ParsedEvent → Normalizer → CanonicalEvent
→ Enrichment → EnrichedEvent → Correlation → Detection → Alert → Incident → Case
```

Cada estágio é uma **função pura de transformação** com contrato tipado, e
cada modelo que trafega entre estágios é **imutável** (`@dataclass(frozen=True)`):

| Modelo | Estágio de origem | Responsabilidade |
|---|---|---|
| `RawEvent` | Collector | Payload bruto + origem (sem interpretação) |
| `ParsedEvent` | Parser | Campos estruturados extraídos do payload |
| `CanonicalEvent` | Normalizer | Modelo canônico de segurança (severidade, usuário, IPs, host) |
| `EnrichedEvent` | Enrichment | Canônico + contextos anexados (`Enrichment`) |

Contratos de plugins alinhados:
- `ParserPlugin.parse(RawEvent) -> Result[list[ParsedEvent]]`
- `EnrichmentPlugin.enrich(CanonicalEvent, context) -> Result[EnrichedEvent]`
- `AnalyzerPlugin.analyze(EnrichedEvent) -> Result[list[Alert]]`

## Consequências
- (+) Lifecycle explícito e imutável; replay seguro; didática por estágio.
- (+) Enriquecimento não muta o evento original — cria derivado (`EnrichedEvent`).
- (+) Contratos de plugins refletem a pipeline real (Parser não produz `RawEvent`).
- (-) `dataclasses.replace` não deriva subclasse com campos novos; a conversão
  canônico → enriquecido usa `asdict` + construção explícita.
- Manutenção em 1 ano: nova fonte/parser = implementar contrato tipado, sem
  alterar o pipeline.

## Critério "daqui a um ano"
Um desenvolvedor novo explica o caminho de um evento citando os modelos
`RawEvent → ParsedEvent → CanonicalEvent → EnrichedEvent` e seus estágios.
