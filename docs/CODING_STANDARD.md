# EDY SIEM — Coding Standard

> Padrão obrigatório de código. Todo código deve seguir isto.

## 1. Princípios
- **SOLID**, **Clean Architecture**, **KISS**, **DRY**, **YAGNI**.
- **Responsabilidade única**: cada módulo/classe/função faz uma coisa.
- **Baixo acoplamento, alta coesão**.
- **Código autodocumentado**: nomes claros > comentários.
- **Zero gambiarra, zero duplicação, zero dependências desnecessárias.**

## 2. Tipagem
- Tipagem estrita obrigatória (mypy strict).
- Toda função pública tem assinatura tipada (args, retorno, exceções documentadas).
- Uso de `Protocol` para interfaces entre camadas.
- `dict[str, Any]` apenas em fronteiras (payloads/JSON), nunca no domínio.

## 3. Estrutura de arquivo
```
"""
Módulo: <caminho>.<nome>
Responsabilidade: <uma frase>
"""

from __future__ import annotations

# imports (stdlib → third-party → local), ordenados

class X: ...

def funcao(...) -> ...: ...
```
- Máximo ~200-300 linhas por arquivo; cresceu → dividir.
- Comentários apenas quando explicam o *porquê*, nunca o *o quê*.

## 4. Tratamento de erros
- Erros de domínio como classes tipadas em `core/errors.py`.
- Nunca `except Exception` sem tratamento/log explícito.
- Fronteiras (API/CLI) convertem erros de domínio em respostas HTTP/exit codes claros.

## 5. Logs
- Log estruturado JSON (ver ADR-006).
- Níveis: DEBUG (detalhe), INFO (ação), WARNING (anomalia tolerável), ERROR (falha recuperável),
  CRITICAL (falha que exige intervenção).

## 6. Testes
- Teste unitário por módulo; integração por fluxo; e2e para caminhos críticos.
- Nome: `test_<unidade>_<comportamento>`.
- Cobertura alvo: ≥ 85% (realista, sem testes artificiais).

## 7. Ferramentas (gate)
- `pytest` (verde)
- `mypy --strict` (0 issues)
- `ruff check` (limpo)
- `ruff format --check` (formatado)
- Node/TS equivalentes no frontend

## 8. Commits
- Convenção: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`, `ci:`, `build:`.
- Mensagens objetivas; commit atômico por mudança.

## 9. Frontend — Regra de Wrappers (PERMANENTE)
> **Nenhuma biblioteca React pode ser usada diretamente em páginas.**

Toda dependência externa de UI (tabelas, gráficos, badges, modais, drawers, timelines, etc.)
deve ser **encapsulada em um componente próprio do EDY SIEM** (`frontend/src/design-system/`
ou `frontend/src/charts/`). Páginas consomem **apenas** os wrappers do projeto.

### Exemplos
```
❌ <LineChart /> de Recharts direto na página
✅ <SecurityLineChart /> criado pelo EDY SIEM (usa Recharts internamente)

❌ <table> crua com dados
✅ <DataTable /> do EDY SIEM

❌ <Modal /> de biblioteca
✅ <Modal /> do EDY SIEM (wrapping interno)
```

### Vantagens
- Identidade visual consistente em todo o sistema;
- Facilidade para trocar de biblioteca no futuro (ex.: Recharts → outro) sem tocar em páginas;
- Menos dependência externa exposta;
- Componentes reutilizáveis em todo o produto.

### Regras
- Páginas importam de `@/design-system` e `@/charts` — nunca direto de `recharts`, `react-router`, etc.
- Wrapper = componente próprio com API tipada; a biblioteca externa fica no interior.
- Novo componente externo usado → criar wrapper antes de usar em qualquer página.
