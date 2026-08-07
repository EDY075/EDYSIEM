# EDY SIEM — Coding Guide

> Convenções de código obrigatórias. Extensão de `docs/development/coding-standard.md` com detalhes
> práticos de nomenclatura, tipos, DTOs, Result Pattern e padrões REST.

## 1. Nomenclatura

| Contexto | Padrão | Exemplo |
|---|---|---|
| Módulos/arquivos | snake_case | `event_repository.py` |
| Classes | PascalCase | `CanonicalEvent` |
| Funções/métodos | snake_case | `normalize_event` |
| Variáveis | snake_case | `source_host` |
| Constantes | UPPER_SNAKE | `DEFAULT_TIMEOUT_S` |
| Protocol/ABC | sufixo `Protocol` | `EventRepositoryProtocol` |
| Erros de domínio | sufixo `Error` | `InvalidEventError` |
| DTOs | sufixo `DTO` | `CreateRuleDTO` |
| Testes | `test_<unidade>_<comportamento>` | `test_normalize_syslog_auth_fail` |

## 2. Imports

- Ordem: stdlib → third-party → local (ordenados).
- Imports absolutos; nunca `from . import *`.
- `from __future__ import annotations` no topo de todo módulo.
- Importar módulos, não símbolos quando evita acoplamento circular.

## 3. Organização de módulo

```python
"""Módulo: <caminho>.<nome>
Responsabilidade: <uma frase>

Regras:
- <se necessário>
"""

from __future__ import annotations

# stdlib
# third-party
# local

_PRVATE_CONST = ...

class PublicClass: ...

def public_function(...) -> ...: ...
```

## 4. Comentários

- Apenas o *porquê* (decisão, sutileza); nunca o *o quê*.
- Docstrings: módulo (1 linha), classe (1 linha), função pública (1 linha + args quando útil).
- Sem comentários óbvios (`# incrementa x`).

## 5. Logging

- Usar o logging system central (`app/core/logging/` — ver LOGGING_DESIGN.md).
- Sem `print` em código de produção.
- Incluir contexto estruturado (trace_id, entity) via campos JSON.

## 6. Exceptions

- Erros de domínio tipados em `app/core/errors/`.
- Hierarquia: `EdySiemError` base → erros específicos.
- Nunca `except Exception` sem tratamento; fronteiras convertem para resposta/exit code.
- Exceções de infra (HTTP, DB) são capturadas nos adaptadores, não no domínio.

## 7. Typing

- Tipagem estrita (mypy strict).
- Tipos explícitos em assinaturas públicas.
- `Optional` → `X | None`. Coleções: `list[..]`, `dict[..]`, `tuple[..]`.
- `Any` apenas em fronteiras JSON; nunca no domínio.
- Usar `Protocol` para interfaces; `dataclass` para estruturas.

## 8. Dataclasses

- Dados imutáveis: `@dataclass(frozen=True, slots=True)`.
- Comparação/hash quando necessário (`eq=True`/`frozen`).
- Sem lógica de negócio em dataclass (apenas validação básica opcional).

## 9. DTOs

- DTOs para fronteiras (API/CLI): entram e saem dos adaptadores.
- DTO ≠ entidade de domínio: converter explicitamente (mapper).
- Validação de entrada via schema do DTO.

## 10. Result Pattern

Operações com falha esperada retornam Result em vez de exceção:

```python
@dataclass(frozen=True)
class Result:
    ok: bool
    value: Any | None = None
    error: EdySiemError | None = None

    @staticmethod
    def success(value): ...
    @staticmethod
    def failure(error): ...
```

- Usar Result em regras, validações, integrações opcionais.
- Exceções para falhas de contrato/programação; Result para falhas de domínio esperadas.

## 11. Padrões de resposta (REST)

```json
// Sucesso
{"data": {...}}
// Lista
{"data": [...], "meta": {"total": 248, "limit": 25, "offset": 0}}
// Erro
{"error": {"code": "rule_not_found", "message": "...", "trace_id": "..."}}
```

- Sempre `data`/`error` no topo (envelope consistente).
- Erros com `code` estável + `message` + `trace_id`.
- Status HTTP semântico: 200/201/204, 400/401/403/404/409/422, 500.

## 12. Padrões REST

- Recursos no plural: `/events`, `/alerts`, `/incidents`.
- Ações de ciclo de vida: `POST /resource/{id}/action`.
- Versionamento: `/api/v1`.
- Paginação: `limit`/`offset` + `meta`.
- Filtros: query params nomeados (`severity`, `status`, `since`).
- Idempotência: `Idempotency-Key` em POSTs críticos.
