# EDY SIEM — Project Structure

> Árvore definitiva do projeto. **Cada pasta tem responsabilidade única.**
> Regra: nenhum arquivo fora do seu diretório de responsabilidade.

## Árvore

```
EDYSIEM/
├── app/                          # Código-fonte do produto
│   ├── core/                     # Domínio puro — sem I/O (Clean Architecture)
│   │   ├── contracts/            # Protocol/ABCs (interfaces entre camadas)
│   │   ├── errors/               # Erros de domínio tipados
│   │   ├── models/               # Entidades/agregados (Event, Alert, Incident…)
│   │   ├── events/               # Event Bus (schemas, producer/consumer)
│   │   ├── logging/              # Logging system (audit/app/security/debug)
│   │   └── config/               # Configuração tipada (env-driven)
│   ├── collectors/               # Conectores de fontes (syslog, arquivo, API)
│   ├── parsers/                  # Parsers por source_type
│   ├── ingestion/                # Ingestor + filas + backpressure
│   ├── normalization/            # Conversão para CanonicalEvent
│   ├── enrichment/               # Enrichers (asset, geo, intel)
│   ├── correlation/              # Correlation Engine
│   ├── detection/                # Detection Engine + regras
│   ├── incident/                 # Incident Engine
│   ├── persistence/              # Repositórios (SQLite via Protocol)
│   ├── api/                      # REST API v1 (adaptador)
│   ├── cli/                      # Interface de linha de comando
│   ├── ui/                       # Frontend (SPA)
│   ├── container.py              # Bootstrap DI (monta o grafo)
│   └── __init__.py
├── config/                       # Configurações declarativas (fora do código)
│   ├── rules/                    # Detection/Correlation rules (YAML)
│   └── collectors/               # Config de coletores
├── docs/                         # Documentação (índice: README)
│   ├── adr/                      # Architecture Decision Records
│   ├── design/                   # Design system, UX, wireframes
│   ├── guides/                   # Guias operacionais/estudo
│   └── research/                 # Benchmarks e estudos
├── examples/                     # Exemplos de eventos/regras (didático)
├── scripts/                      # Scripts de automação
│   └── migrations/               # Migrações de banco versionadas
├── tests/                        # Testes
│   ├── unit/                     # Por módulo (sem I/O real)
│   ├── integration/              # Pipeline completo (storage temp)
│   └── e2e/                      # API/CLI ponta a ponta
├── tools/                        # Ferramentas de dev (não produto)
│   └── dev/                      # Scripts de auxílio local
├── .github/workflows/            # CI/CD
├── PROJECT_MANIFESTO.md
├── README.md
└── pyproject.toml
```

## Responsabilidade por diretório

| Diretório | Responsabilidade | Proibido |
|---|---|---|
| `app/core` | Domínio puro, modelos, contratos, erros | Importar I/O, HTTP, storage |
| `app/collectors..incident` | Etapas do pipeline | Acessar UI/persistence direto |
| `app/persistence` | Persistir via Protocol | Conter regra de negócio |
| `app/api` / `app/cli` / `app/ui` | Adaptadores de saída | Conter regra de negócio |
| `config` | Dados declarativos (regras, coletores) | Conter código Python |
| `docs` | Conhecimento do produto | Conter código executável |
| `examples` | Dados de exemplo (didático/teste) | Conter código de produção |
| `scripts` | Automação operacional | Fazer parte do pacote pip |
| `tools` | Dev apenas | Fazer parte do pacote pip |
| `tests` | Verificação | Importar produção indiretamente sem intenção |

## Regras

1. `app/core` **não importa** nada fora de `app/core`.
2. Etapas do pipeline dependem apenas de `core` + resultados anteriores.
3. Adaptadores (api/cli/ui/persistence) implementam contratos de `core`.
4. Nada de `config`/`examples` importado em produção (só dados).
5. Cada módulo tem `__init__.py` com API pública explícita.
