# EDY SIEM — Project Structure

> Árvore definitiva do projeto. **Cada pasta tem responsabilidade única.**
> Regra: nenhum arquivo fora do seu diretório de responsabilidade.
> Atualizado em 2026-08-03 para a estrutura `src/edysiem/` (Sprint 1) e a
> pipeline oficial com `ParsedEvent`/`EnrichedEvent` (Sprint 2.1).

## Árvore

```
EDYSIEM/
├── src/
│   └── edysiem/                   # Pacote principal (src-layout)
│       ├── __init__.py            # API pública raiz + __version__
│       ├── py.typed               # Marcador de tipagem
│       ├── domain/                # Entidades/enums puras (sem I/O)
│       ├── events/                # Event Bus (base, registry, bus)
│       ├── result/                # Result[T] + ErrorCode
│       ├── exceptions/            # Hierarquia de exceções
│       ├── config/                # Config tipada (env-driven)
│       ├── logging/               # Log estruturado JSON + trace_id
│       ├── plugins/               # Contratos/Protocols de extensibilidade
│       ├── di/                    # Container de injeção de dependência
│       ├── validation/            # Motor declarativo de validação
│       ├── collectors/            # (futuro) conectores de fontes
│       ├── parsers/               # (futuro) parsers por source_type
│       ├── ingestion/             # (futuro) ingestor + filas + backpressure
│       ├── normalization/         # (futuro) conversão p/ CanonicalEvent
│       ├── enrichment/            # (futuro) enrichers (asset, geo, intel)
│       ├── correlation/           # (futuro) correlation engine
│       ├── detection/             # (futuro) detection engine + regras
│       ├── incident/              # (futuro) incident engine
│       ├── persistence/           # (futuro) repositórios (SQLite via Protocol)
│       ├── api/                   # (futuro) REST API v1 (adaptador)
│       ├── cli/                   # (futuro) interface de linha de comando
│       └── ui/                    # (futuro) frontend (SPA)
├── config/                        # Configurações declarativas (fora do código)
│   ├── rules/                     # (futuro) detection/correlation rules (YAML)
│   └── collectors/                # (futuro) config de coletores
├── docs/                          # Documentação (índice: README)
│   ├── adr/                       # Architecture Decision Records
│   ├── design/                    # Design system, UX, wireframes
│   ├── guides/                    # Guias operacionais/estudo
│   └── research/                  # Benchmarks e estudos
├── examples/                      # (futuro) exemplos de eventos/regras
├── scripts/                       # Scripts de automação
│   └── migrations/                # (futuro) migrações de banco versionadas
├── tests/                         # Testes
│   ├── unit/                      # Por módulo (sem I/O real)
│   ├── integration/               # (futuro) pipeline completo (storage temp)
│   └── e2e/                       # (futuro) API/CLI ponta a ponta
├── tools/                         # Ferramentas de dev (não produto)
├── .github/workflows/             # (futuro) CI/CD
├── archive/                       # Código antigo arquivado (não apagar)
├── CHANGELOG.md
├── PROJECT_MANIFESTO.md
├── README.md
└── pyproject.toml
```

## Pipeline oficial

```
Collector
    ↓
RawEvent
    ↓
Parser
    ↓
ParsedEvent
    ↓
Normalizer
    ↓
CanonicalEvent
    ↓
Enrichment
    ↓
EnrichedEvent
    ↓
Correlation
    ↓
Detection
    ↓
Alert
    ↓
Incident
    ↓
Case
```

## Responsabilidade por diretório

| Diretório | Responsabilidade | Proibido |
|---|---|---|
| `src/edysiem/domain` | Entidades, enums, value objects puros | Importar I/O, HTTP, storage |
| `src/edysiem/result` | Resultado tipado (Result/Error) | Conter regra de negócio |
| `src/edysiem/exceptions` | Hierarquia de erros de domínio | Importar camadas externas |
| `src/edysiem/events` | Event Bus de domínio | Conhecer coletores/UI |
| `src/edysiem/config` | Config tipada (env-driven) | Conter lógica de negócio |
| `src/edysiem/logging` | Log estruturado + trace_id | Conter lógica de negócio |
| `src/edysiem/plugins` | Contratos (Protocols) de extensibilidade | Importar implementações |
| `src/edysiem/di` | Injeção de dependência | Conter lógica de negócio |
| `src/edysiem/validation` | Validação declarativa | Importar implementações |
| `collectors..incident` (futuro) | Etapas do pipeline | Acessar UI/persistence direto |
| `persistence` (futuro) | Persistir via Protocol | Conter regra de negócio |
| `api` / `cli` / `ui` (futuro) | Adaptadores de saída | Conter regra de negócio |
| `config` | Dados declarativos (regras, coletores) | Conter código Python |
| `docs` | Conhecimento do produto | Conter código executável |
| `examples` | Dados de exemplo (didático/teste) | Conter código de produção |
| `scripts` | Automação operacional | Fazer parte do pacote pip |
| `tools` | Dev apenas | Fazer parte do pacote pip |
| `tests` | Verificação | Importar produção indiretamente sem intenção |
| `archive` | Código antigo (backup) | Ser importado por produção |

## Regras

1. `domain` **não importa** nada fora de `domain` + stdlib.
2. Etapas do pipeline dependem apenas de `domain`/`result`/`plugins` + resultados anteriores.
3. Adaptadores (api/cli/ui/persistence) implementam contratos de `plugins`/`domain`.
4. Nada de `config`/`examples` importado em produção (só dados).
5. Cada módulo tem `__init__.py` com API pública explícita.
6. Eventos da pipeline são **imutáveis** — `RawEvent`, `ParsedEvent`, `CanonicalEvent` e
   `EnrichedEvent` são `@dataclass(frozen=True)`.
